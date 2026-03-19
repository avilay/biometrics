from datetime import datetime, timedelta, timezone
from typing import Optional

import aiosqlite

from app.models import AggregationResponse, SeriesData


# Range -> (timedelta for lookback, strftime bucket format, label for display)
RANGE_CONFIG = {
    "D": (timedelta(hours=24), "%Y-%m-%d %H:00", "hour"),
    "W": (timedelta(days=7), "%Y-%m-%d", "day"),
    "M": (timedelta(days=30), "%Y-W%W", "week"),
    "6M": (timedelta(days=180), "%Y-%m", "month"),
    "Y": (timedelta(days=365), "%Y-%m", "month"),
}


def _generate_buckets(range_key: str, now: datetime) -> list[str]:
    """Generate the expected time bucket labels for a given range."""
    if range_key == "D":
        return [(now - timedelta(hours=23 - i)).strftime("%Y-%m-%d %H:00") for i in range(24)]
    elif range_key == "W":
        return [(now - timedelta(days=6 - i)).strftime("%Y-%m-%d") for i in range(7)]
    elif range_key == "M":
        # ~4-5 weeks in 30 days
        buckets = []
        for i in range(5):
            dt = now - timedelta(weeks=4 - i)
            bucket = dt.strftime("%Y-W%W")
            if bucket not in buckets:
                buckets.append(bucket)
        return buckets
    elif range_key == "6M":
        buckets = []
        for i in range(6):
            dt = now - timedelta(days=30 * (5 - i))
            bucket = dt.strftime("%Y-%m")
            if bucket not in buckets:
                buckets.append(bucket)
        return buckets
    elif range_key == "Y":
        buckets = []
        for i in range(12):
            dt = now - timedelta(days=30 * (11 - i))
            bucket = dt.strftime("%Y-%m")
            if bucket not in buckets:
                buckets.append(bucket)
        return buckets
    return []


def _agg_sql(aggregate: str) -> str:
    mapping = {
        "count": "COUNT(*)",
        "sum": "SUM(l.numeric_value)",
        "mean": "AVG(l.numeric_value)",
    }
    return mapping.get(aggregate, "COUNT(*)")


async def aggregate_logs(
    db: aiosqlite.Connection,
    metric_id: int,
    user_id: int,
    range_key: str = "W",
    aggregate: str = "count",
    group_by: Optional[str] = None,
    filters: Optional[dict[str, str]] = None,
) -> AggregationResponse | None:
    # Verify metric belongs to user
    cursor = await db.execute(
        "SELECT id, value_type FROM metrics WHERE id = ? AND user_id = ?",
        (metric_id, user_id),
    )
    metric = await cursor.fetchone()
    if not metric:
        return None

    value_type = metric["value_type"]

    config = RANGE_CONFIG.get(range_key)
    if not config:
        config = RANGE_CONFIG["W"]
        range_key = "W"

    lookback, bucket_fmt, _ = config
    now = datetime.now(timezone.utc)
    start_time = (now - lookback).strftime("%Y-%m-%d %H:%M:%S")

    agg_func = _agg_sql(aggregate)

    # Base query parts
    select_parts = [f"strftime('{bucket_fmt}', l.recorded_at) AS bucket", f"{agg_func} AS agg_val"]
    from_parts = ["logs l"]
    where_parts = ["l.metric_id = ?", "l.recorded_at >= ?"]
    params: list = [metric_id, start_time]
    group_parts = ["bucket"]

    # Determine grouping
    group_by_col = None
    if group_by:
        if group_by == "__categorical__" or (group_by == "value" and value_type == "categorical"):
            # Group by the categorical value of the metric itself
            select_parts.append("l.categorical_value AS group_name")
            group_parts.append("group_name")
            group_by_col = "group_name"
        else:
            # Group by a dimension's categories
            from_parts.append("JOIN log_dimensions ld_g ON ld_g.log_id = l.id")
            from_parts.append("JOIN dimensions d_g ON d_g.id = ld_g.dimension_id")
            from_parts.append("JOIN dimension_categories dc_g ON dc_g.id = ld_g.category_id")
            where_parts.append("d_g.name = ?")
            params.append(group_by)
            select_parts.append("dc_g.name AS group_name")
            group_parts.append("group_name")
            group_by_col = "group_name"

    # Apply dimension filters
    if filters:
        filter_idx = 0
        for dim_name, cat_name in filters.items():
            alias_ld = f"ld_f{filter_idx}"
            alias_d = f"d_f{filter_idx}"
            alias_dc = f"dc_f{filter_idx}"
            from_parts.append(f"JOIN log_dimensions {alias_ld} ON {alias_ld}.log_id = l.id")
            from_parts.append(f"JOIN dimensions {alias_d} ON {alias_d}.id = {alias_ld}.dimension_id")
            from_parts.append(
                f"JOIN dimension_categories {alias_dc} ON {alias_dc}.id = {alias_ld}.category_id"
            )
            where_parts.append(f"{alias_d}.name = ?")
            where_parts.append(f"{alias_dc}.name = ?")
            params.extend([dim_name, cat_name])
            filter_idx += 1

    query = (
        f"SELECT {', '.join(select_parts)} "
        f"FROM {' '.join(from_parts)} "
        f"WHERE {' AND '.join(where_parts)} "
        f"GROUP BY {', '.join(group_parts)} "
        f"ORDER BY bucket"
    )

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

    # Generate expected bucket labels
    labels = _generate_buckets(range_key, now)

    if group_by_col:
        # Collect all group names and organize data
        groups: dict[str, dict[str, float]] = {}
        for row in rows:
            gname = row["group_name"] or "Unknown"
            bucket = row["bucket"]
            val = row["agg_val"]
            if gname not in groups:
                groups[gname] = {}
            groups[gname][bucket] = val

        series = []
        for gname, bucket_map in sorted(groups.items()):
            data = [bucket_map.get(lbl) for lbl in labels]
            series.append(SeriesData(name=gname, data=data))
    else:
        bucket_map = {row["bucket"]: row["agg_val"] for row in rows}
        data = [bucket_map.get(lbl) for lbl in labels]
        series = [SeriesData(name="total", data=data)]

    return AggregationResponse(labels=labels, series=series)
