"""Seed the database with ~2 months of test data for all 5 example metrics."""

import asyncio
import random
from datetime import datetime, timedelta, timezone

import aiosqlite

from app.auth import DEMO_FIREBASE_UID
from app.config import settings

random.seed(42)

NOW = datetime.now(timezone.utc)
TWO_MONTHS_AGO = NOW - timedelta(days=60)


async def seed():
    db = await aiosqlite.connect(settings.DATABASE_URL)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")

    # Ensure schema exists
    from app.database import SCHEMA_SQL
    await db.executescript(SCHEMA_SQL)
    await db.commit()

    # Create/find demo user
    await db.execute(
        "INSERT OR IGNORE INTO users (firebase_uid, email, display_name) "
        f"VALUES ('{DEMO_FIREBASE_UID}', 'demo@example.com', 'Demo User')"
    )
    await db.commit()
    cur = await db.execute("SELECT id FROM users WHERE firebase_uid = ?", (DEMO_FIREBASE_UID,))
    user_id = (await cur.fetchone())["id"]

    # ── 1. Meditation (none, no dimensions) ──────────────────────────
    metric_id = await create_metric(db, user_id, "Meditation", "none")
    # ~1 meditation per day, some days skipped
    day = TWO_MONTHS_AGO
    while day < NOW:
        if random.random() < 0.65:  # 65% chance of meditating
            hour = random.choice([6, 7, 8, 17, 18, 21])
            ts = day.replace(hour=hour, minute=random.randint(0, 59))
            await insert_log(db, metric_id, ts)
            # Occasionally meditate twice in a day
            if random.random() < 0.15:
                hour2 = random.choice([17, 18, 21])
                ts2 = day.replace(hour=hour2, minute=random.randint(0, 59))
                await insert_log(db, metric_id, ts2)
        day += timedelta(days=1)
    print(f"  Meditation: seeded")

    # ── 2. Food (none, 4 dimensions) ─────────────────────────────────
    metric_id = await create_metric(db, user_id, "Food", "none")
    dims = {
        "Source": await create_dimension(db, metric_id, "Source", ["Home-Cooked", "Take-Out", "Tiffin"]),
        "Taste": await create_dimension(db, metric_id, "Taste", ["Delicious", "Edible", "Bad"]),
        "Is_Filling": await create_dimension(db, metric_id, "Is_Filling", ["True", "False"]),
        "Healthy": await create_dimension(db, metric_id, "Healthy", ["Very", "Medium", "No"]),
    }
    # 2-3 meals per day
    day = TWO_MONTHS_AGO
    while day < NOW:
        n_meals = random.choice([2, 2, 3, 3, 3])
        meal_hours = sorted(random.sample([7, 8, 12, 13, 18, 19, 20], n_meals))
        for h in meal_hours:
            ts = day.replace(hour=h, minute=random.randint(0, 45))
            source = random.choices(["Home-Cooked", "Take-Out", "Tiffin"], weights=[50, 30, 20])[0]
            if source == "Home-Cooked":
                taste = random.choices(["Delicious", "Edible", "Bad"], weights=[40, 50, 10])[0]
                healthy = random.choices(["Very", "Medium", "No"], weights=[50, 35, 15])[0]
            elif source == "Take-Out":
                taste = random.choices(["Delicious", "Edible", "Bad"], weights=[60, 30, 10])[0]
                healthy = random.choices(["Very", "Medium", "No"], weights=[15, 40, 45])[0]
            else:
                taste = random.choices(["Delicious", "Edible", "Bad"], weights=[30, 55, 15])[0]
                healthy = random.choices(["Very", "Medium", "No"], weights=[40, 45, 15])[0]
            filling = random.choices(["True", "False"], weights=[70, 30])[0]

            log_id = await insert_log(db, metric_id, ts)
            await insert_log_dim(db, log_id, dims["Source"], source)
            await insert_log_dim(db, log_id, dims["Taste"], taste)
            await insert_log_dim(db, log_id, dims["Is_Filling"], filling)
            await insert_log_dim(db, log_id, dims["Healthy"], healthy)
        day += timedelta(days=1)
    print(f"  Food: seeded")

    # ── 3. Mood (categorical, no dimensions) ─────────────────────────
    metric_id = await create_metric(db, user_id, "Mood", "categorical")
    for cat in ["Happy", "Sad", "Angry", "Serene"]:
        await db.execute(
            "INSERT INTO metric_categories (metric_id, name, sort_order) VALUES (?, ?, ?)",
            (metric_id, cat, ["Happy", "Sad", "Angry", "Serene"].index(cat)),
        )
    # 2-4 mood logs per day
    day = TWO_MONTHS_AGO
    while day < NOW:
        n = random.choice([2, 2, 3, 3, 4])
        hours = sorted(random.sample(range(7, 23), n))
        for h in hours:
            ts = day.replace(hour=h, minute=random.randint(0, 59))
            mood = random.choices(
                ["Happy", "Sad", "Angry", "Serene"],
                weights=[40, 15, 10, 35],
            )[0]
            await insert_log(db, metric_id, ts, categorical_value=mood)
        day += timedelta(days=1)
    print(f"  Mood: seeded")

    # ── 4. Weight (numeric, no dimensions) ───────────────────────────
    metric_id = await create_metric(db, user_id, "Weight", "numeric", unit="lbs")
    # Weigh in most mornings, slight downward trend from 185 to 180
    weight = 185.0
    day = TWO_MONTHS_AGO
    while day < NOW:
        if random.random() < 0.85:  # 85% chance of weighing in
            weight += random.gauss(-0.08, 0.5)  # slight downward drift
            weight = max(175.0, min(195.0, weight))  # clamp
            ts = day.replace(hour=random.choice([6, 7, 8]), minute=random.randint(0, 30))
            await insert_log(db, metric_id, ts, numeric_value=round(weight, 1))
        day += timedelta(days=1)
    print(f"  Weight: seeded")

    # ── 5. Blood Glucose (numeric, 2 dimensions) ─────────────────────
    metric_id = await create_metric(db, user_id, "Blood Glucose", "numeric", unit="mg/dL")
    dims = {
        "Event": await create_dimension(db, metric_id, "Event", ["Fasting", "Breakfast", "Workout", "Ad-Hoc"]),
        "Delta": await create_dimension(db, metric_id, "Delta", ["One-Hour-After", "Two-Hours-After"]),
    }
    day = TWO_MONTHS_AGO
    while day < NOW:
        # Fasting reading most mornings
        if random.random() < 0.75:
            ts = day.replace(hour=random.choice([6, 7]), minute=random.randint(0, 30))
            val = round(random.gauss(95, 8), 0)
            log_id = await insert_log(db, metric_id, ts, numeric_value=val)
            await insert_log_dim(db, log_id, dims["Event"], "Fasting")

        # Post-breakfast readings ~60% of days
        if random.random() < 0.60:
            delta = random.choice(["One-Hour-After", "Two-Hours-After"])
            h = 9 if delta == "One-Hour-After" else 10
            ts = day.replace(hour=h, minute=random.randint(0, 45))
            base = 140 if delta == "One-Hour-After" else 120
            val = round(random.gauss(base, 15), 0)
            log_id = await insert_log(db, metric_id, ts, numeric_value=val)
            await insert_log_dim(db, log_id, dims["Event"], "Breakfast")
            await insert_log_dim(db, log_id, dims["Delta"], delta)

        # Post-workout readings ~30% of days
        if random.random() < 0.30:
            delta = random.choice(["One-Hour-After", "Two-Hours-After"])
            h = 17 if delta == "One-Hour-After" else 18
            ts = day.replace(hour=h, minute=random.randint(0, 45))
            val = round(random.gauss(110, 12), 0)
            log_id = await insert_log(db, metric_id, ts, numeric_value=val)
            await insert_log_dim(db, log_id, dims["Event"], "Workout")
            await insert_log_dim(db, log_id, dims["Delta"], delta)

        # Ad-hoc readings ~10% of days
        if random.random() < 0.10:
            ts = day.replace(hour=random.choice([11, 14, 16, 20]), minute=random.randint(0, 59))
            val = round(random.gauss(115, 18), 0)
            log_id = await insert_log(db, metric_id, ts, numeric_value=val)
            await insert_log_dim(db, log_id, dims["Event"], "Ad-Hoc")
        day += timedelta(days=1)
    print(f"  Blood Glucose: seeded")

    await db.commit()
    await db.close()

    # Print summary
    db = await aiosqlite.connect(settings.DATABASE_URL)
    db.row_factory = aiosqlite.Row
    cur = await db.execute("SELECT COUNT(*) as c FROM metrics")
    print(f"\nTotal metrics: {(await cur.fetchone())['c']}")
    cur = await db.execute("SELECT COUNT(*) as c FROM logs")
    print(f"Total log entries: {(await cur.fetchone())['c']}")
    cur = await db.execute(
        "SELECT m.name, COUNT(l.id) as c FROM metrics m LEFT JOIN logs l ON l.metric_id = m.id GROUP BY m.id"
    )
    for row in await cur.fetchall():
        print(f"  {row['name']}: {row['c']} entries")
    await db.close()


async def create_metric(db, user_id, name, value_type, unit=None):
    cur = await db.execute(
        "INSERT INTO metrics (user_id, name, value_type, unit) VALUES (?, ?, ?, ?)",
        (user_id, name, value_type, unit),
    )
    await db.commit()
    return cur.lastrowid


async def create_dimension(db, metric_id, name, categories):
    cur = await db.execute(
        "INSERT INTO dimensions (metric_id, name, sort_order) VALUES (?, ?, 0)",
        (metric_id, name),
    )
    dim_id = cur.lastrowid
    cat_map = {}
    for i, cat in enumerate(categories):
        cat_cur = await db.execute(
            "INSERT INTO dimension_categories (dimension_id, name, sort_order) VALUES (?, ?, ?)",
            (dim_id, cat, i),
        )
        cat_map[cat] = cat_cur.lastrowid
    await db.commit()
    return {"dim_id": dim_id, "cats": cat_map}


async def insert_log(db, metric_id, ts, numeric_value=None, categorical_value=None):
    cur = await db.execute(
        "INSERT INTO logs (metric_id, recorded_at, numeric_value, categorical_value) VALUES (?, ?, ?, ?)",
        (metric_id, ts.strftime("%Y-%m-%dT%H:%M:%SZ"), numeric_value, categorical_value),
    )
    return cur.lastrowid


async def insert_log_dim(db, log_id, dim_info, category_name):
    cat_id = dim_info["cats"][category_name]
    await db.execute(
        "INSERT INTO log_dimensions (log_id, dimension_id, category_id) VALUES (?, ?, ?)",
        (log_id, dim_info["dim_id"], cat_id),
    )


if __name__ == "__main__":
    asyncio.run(seed())
