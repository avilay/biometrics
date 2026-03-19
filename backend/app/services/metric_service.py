from datetime import datetime, timedelta, timezone

import aiosqlite

from app.models import MetricCreate, MetricResponse, MetricListItem, DimensionResponse, DimensionCategoryResponse


async def create_metric(db: aiosqlite.Connection, user_id: int, data: MetricCreate) -> MetricResponse:
    cursor = await db.execute(
        "INSERT INTO metrics (user_id, name, value_type, unit) VALUES (?, ?, ?, ?)",
        (user_id, data.name, data.value_type.value, data.unit),
    )
    metric_id = cursor.lastrowid

    # Insert categories for categorical metrics
    categories: list[str] = []
    if data.categories:
        for i, cat_name in enumerate(data.categories):
            await db.execute(
                "INSERT INTO metric_categories (metric_id, name, sort_order) VALUES (?, ?, ?)",
                (metric_id, cat_name, i),
            )
        categories = data.categories

    # Insert dimensions
    dimensions: list[DimensionResponse] = []
    if data.dimensions:
        for i, dim in enumerate(data.dimensions):
            dim_cursor = await db.execute(
                "INSERT INTO dimensions (metric_id, name, sort_order) VALUES (?, ?, ?)",
                (metric_id, dim.name, i),
            )
            dim_id = dim_cursor.lastrowid
            dim_cats: list[DimensionCategoryResponse] = []
            for j, cat_name in enumerate(dim.categories):
                cat_cursor = await db.execute(
                    "INSERT INTO dimension_categories (dimension_id, name, sort_order) VALUES (?, ?, ?)",
                    (dim_id, cat_name, j),
                )
                dim_cats.append(DimensionCategoryResponse(id=cat_cursor.lastrowid, name=cat_name))
            dimensions.append(DimensionResponse(id=dim_id, name=dim.name, categories=dim_cats))

    await db.commit()

    # Fetch created_at
    cursor = await db.execute("SELECT created_at FROM metrics WHERE id = ?", (metric_id,))
    row = await cursor.fetchone()

    return MetricResponse(
        id=metric_id,
        name=data.name,
        value_type=data.value_type.value,
        unit=data.unit,
        categories=categories,
        dimensions=dimensions,
        created_at=row["created_at"],
    )


async def get_metric(db: aiosqlite.Connection, user_id: int, metric_id: int) -> MetricResponse | None:
    cursor = await db.execute(
        "SELECT id, name, value_type, unit, created_at FROM metrics WHERE id = ? AND user_id = ?",
        (metric_id, user_id),
    )
    row = await cursor.fetchone()
    if not row:
        return None

    # Fetch categories
    cat_cursor = await db.execute(
        "SELECT name FROM metric_categories WHERE metric_id = ? ORDER BY sort_order",
        (metric_id,),
    )
    categories = [r["name"] for r in await cat_cursor.fetchall()]

    # Fetch dimensions with their categories
    dim_cursor = await db.execute(
        "SELECT id, name FROM dimensions WHERE metric_id = ? ORDER BY sort_order",
        (metric_id,),
    )
    dims = await dim_cursor.fetchall()
    dimensions: list[DimensionResponse] = []
    for d in dims:
        dc_cursor = await db.execute(
            "SELECT id, name FROM dimension_categories WHERE dimension_id = ? ORDER BY sort_order",
            (d["id"],),
        )
        dim_cats = [DimensionCategoryResponse(id=dc["id"], name=dc["name"]) for dc in await dc_cursor.fetchall()]
        dimensions.append(DimensionResponse(id=d["id"], name=d["name"], categories=dim_cats))

    return MetricResponse(
        id=row["id"],
        name=row["name"],
        value_type=row["value_type"],
        unit=row["unit"],
        categories=categories,
        dimensions=dimensions,
        created_at=row["created_at"],
    )


async def list_metrics(db: aiosqlite.Connection, user_id: int) -> list[MetricListItem]:
    cursor = await db.execute(
        "SELECT id, name, value_type, unit FROM metrics WHERE user_id = ? ORDER BY name",
        (user_id,),
    )
    rows = await cursor.fetchall()

    items: list[MetricListItem] = []
    now = datetime.now(timezone.utc)

    for row in rows:
        metric_id = row["id"]
        value_type = row["value_type"]

        # Get latest log
        latest_cursor = await db.execute(
            "SELECT numeric_value, categorical_value, recorded_at FROM logs "
            "WHERE metric_id = ? ORDER BY recorded_at DESC LIMIT 1",
            (metric_id,),
        )
        latest = await latest_cursor.fetchone()

        latest_value = None
        latest_recorded_at = None
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        if latest:
            latest_recorded_at = latest["recorded_at"]
            if value_type == "numeric" and latest["numeric_value"] is not None:
                latest_value = str(latest["numeric_value"])
            elif value_type == "categorical" and latest["categorical_value"] is not None:
                # Count how many times this category was logged this week
                cat_val = latest["categorical_value"]
                cnt_cursor = await db.execute(
                    "SELECT COUNT(*) AS c FROM logs "
                    "WHERE metric_id = ? AND recorded_at >= ? AND categorical_value = ?",
                    (metric_id, week_start, cat_val),
                )
                cnt = (await cnt_cursor.fetchone())["c"]
                latest_value = f"{cat_val} {cnt}x this week"
            elif value_type == "none":
                # Count how many times logged this week
                cnt_cursor = await db.execute(
                    "SELECT COUNT(*) AS c FROM logs "
                    "WHERE metric_id = ? AND recorded_at >= ?",
                    (metric_id, week_start),
                )
                cnt = (await cnt_cursor.fetchone())["c"]
                latest_value = f"{cnt}x this week"

        # Sparkline: last 7 weekly buckets
        sparkline_start = (now - timedelta(weeks=7)).strftime("%Y-%m-%d %H:%M:%S")
        if value_type == "numeric":
            agg_func = "AVG(numeric_value)"
        else:
            agg_func = "COUNT(*)"

        spark_cursor = await db.execute(
            f"""
            SELECT strftime('%Y-W%W', recorded_at) AS bucket, {agg_func} AS val
            FROM logs
            WHERE metric_id = ? AND recorded_at >= ?
            GROUP BY bucket
            ORDER BY bucket
            """,
            (metric_id, sparkline_start),
        )
        spark_rows = await spark_cursor.fetchall()

        # Build 7-period list, filling gaps with None
        spark_map = {r["bucket"]: r["val"] for r in spark_rows}
        sparkline_data: list[float | None] = []
        for i in range(7):
            week_dt = now - timedelta(weeks=6 - i)
            bucket_key = week_dt.strftime("%Y-W%W")
            sparkline_data.append(spark_map.get(bucket_key))

        items.append(
            MetricListItem(
                id=row["id"],
                name=row["name"],
                value_type=row["value_type"],
                unit=row["unit"],
                latest_value=latest_value,
                latest_recorded_at=latest_recorded_at,
                sparkline_data=sparkline_data,
            )
        )

    return items


async def delete_metric(db: aiosqlite.Connection, user_id: int, metric_id: int) -> bool:
    # Verify ownership
    cursor = await db.execute(
        "SELECT id FROM metrics WHERE id = ? AND user_id = ?",
        (metric_id, user_id),
    )
    if not await cursor.fetchone():
        return False

    await db.execute("DELETE FROM metrics WHERE id = ?", (metric_id,))
    await db.commit()
    return True
