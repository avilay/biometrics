import aiosqlite

from app.models import LogCreate, LogResponse


async def create_log(
    db: aiosqlite.Connection, metric_id: int, user_id: int, data: LogCreate
) -> LogResponse | None:
    # Verify metric belongs to user
    cursor = await db.execute(
        "SELECT id, value_type FROM metrics WHERE id = ? AND user_id = ?",
        (metric_id, user_id),
    )
    metric = await cursor.fetchone()
    if not metric:
        return None

    # Insert the log
    cursor = await db.execute(
        "INSERT INTO logs (metric_id, recorded_at, numeric_value, categorical_value) VALUES (?, ?, ?, ?)",
        (metric_id, data.recorded_at, data.numeric_value, data.categorical_value),
    )
    log_id = cursor.lastrowid

    # Resolve and insert dimensions
    dim_dict: dict[str, str] = {}
    if data.dimensions:
        for dim_name, cat_name in data.dimensions.items():
            # Look up dimension by name and metric
            dim_cursor = await db.execute(
                "SELECT id FROM dimensions WHERE metric_id = ? AND name = ?",
                (metric_id, dim_name),
            )
            dim_row = await dim_cursor.fetchone()
            if not dim_row:
                await db.execute("DELETE FROM logs WHERE id = ?", (log_id,))
                await db.commit()
                return None

            # Look up category
            cat_cursor = await db.execute(
                "SELECT id FROM dimension_categories WHERE dimension_id = ? AND name = ?",
                (dim_row["id"], cat_name),
            )
            cat_row = await cat_cursor.fetchone()
            if not cat_row:
                await db.execute("DELETE FROM logs WHERE id = ?", (log_id,))
                await db.commit()
                return None

            await db.execute(
                "INSERT INTO log_dimensions (log_id, dimension_id, category_id) VALUES (?, ?, ?)",
                (log_id, dim_row["id"], cat_row["id"]),
            )
            dim_dict[dim_name] = cat_name

    await db.commit()

    # Fetch created_at
    cursor = await db.execute("SELECT created_at FROM logs WHERE id = ?", (log_id,))
    row = await cursor.fetchone()

    return LogResponse(
        id=log_id,
        metric_id=metric_id,
        recorded_at=data.recorded_at,
        numeric_value=data.numeric_value,
        categorical_value=data.categorical_value,
        dimensions=dim_dict,
        created_at=row["created_at"],
    )


async def delete_log(
    db: aiosqlite.Connection, metric_id: int, log_id: int, user_id: int
) -> bool:
    # Verify ownership through metric
    cursor = await db.execute(
        """
        SELECT l.id FROM logs l
        JOIN metrics m ON m.id = l.metric_id
        WHERE l.id = ? AND l.metric_id = ? AND m.user_id = ?
        """,
        (log_id, metric_id, user_id),
    )
    if not await cursor.fetchone():
        return False

    await db.execute("DELETE FROM logs WHERE id = ?", (log_id,))
    await db.commit()
    return True
