# Biometrics Tracker - Implementation Plan

## Context

Build a personal metrics tracking webapp per `design/product-vision.md`. The app lets users define custom metrics (with varying value types and dimensions), log entries, and analyze timeseries data with filtering/grouping/aggregation. Must run on a Raspberry Pi (8GB RAM, 2 cores). UI mockups in `design/ui/` provide the visual reference.

---

## Technology Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | **Vue 3 + Quasar v2 + ECharts 5** | Mockups already use these; Quasar has great mobile components (bottom sheets, FABs, date pickers); dark theme built-in |
| Backend | **Python / FastAPI + Uvicorn** | ~30-50MB RAM; excellent for aggregation logic; native async; lightweight |
| Database | **SQLite** (via `aiosqlite`) | No server process; single file; sufficient for single-user app |
| Auth | **Firebase Auth** (client-side Google Sign-in) + **PyJWT** (server-side token verification) | Avoids heavy `firebase-admin` SDK; just verify JWTs with Google's public keys |
| State | **Pinia** | Official Vue state management, lightweight |

No ORM — raw SQL keeps aggregation queries simple and dependencies minimal.

---

## Database Schema

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    firebase_uid  TEXT NOT NULL UNIQUE,
    email         TEXT,
    display_name  TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE metrics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    name        TEXT NOT NULL,
    value_type  TEXT NOT NULL CHECK (value_type IN ('none', 'numeric', 'categorical')),
    unit        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, name)
);

CREATE TABLE metric_categories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id INTEGER NOT NULL REFERENCES metrics(id) ON DELETE CASCADE,
    name      TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE(metric_id, name)
);

CREATE TABLE dimensions (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id INTEGER NOT NULL REFERENCES metrics(id) ON DELETE CASCADE,
    name      TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE(metric_id, name)
);

CREATE TABLE dimension_categories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension_id INTEGER NOT NULL REFERENCES dimensions(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    UNIQUE(dimension_id, name)
);

CREATE TABLE logs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id         INTEGER NOT NULL REFERENCES metrics(id) ON DELETE CASCADE,
    recorded_at       TEXT NOT NULL,  -- ISO 8601
    numeric_value     REAL,
    categorical_value TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_logs_metric_time ON logs(metric_id, recorded_at);

CREATE TABLE log_dimensions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id       INTEGER NOT NULL REFERENCES logs(id) ON DELETE CASCADE,
    dimension_id INTEGER NOT NULL REFERENCES dimensions(id),
    category_id  INTEGER NOT NULL REFERENCES dimension_categories(id),
    UNIQUE(log_id, dimension_id)
);
```

---

## API Endpoints

All endpoints require `Authorization: Bearer <firebase_id_token>` (except login).

**Auth**
- `POST /api/auth/login` — body: `{ id_token }` — upserts user, returns user info

**Metrics**
- `GET /api/metrics` — list all metrics with latest value + sparkline summary
- `POST /api/metrics` — create metric with categories/dimensions
- `GET /api/metrics/{id}` — get metric definition
- `DELETE /api/metrics/{id}` — delete metric and all its logs

**Logs**
- `POST /api/metrics/{id}/logs` — create log entry with dimension values
- `GET /api/metrics/{id}/logs?range=W&aggregate=mean&group_by=Event&filter_Delta=One-Hour-After` — returns chart-ready aggregated data (labels + series arrays)
- `DELETE /api/metrics/{id}/logs/{log_id}` — delete a log entry

The aggregation endpoint is the core complexity: it maps range→resampling bucket, applies filters, groups by time bucket (+ optional dimension), and applies count/sum/mean.

---

## Frontend Architecture

**Routes**
| Path | Page | Description |
|------|------|-------------|
| `/` | LoginPage | Google sign-in (redirects to dashboard if authenticated) |
| `/dashboard` | DashboardPage | Grid of MetricCards + FAB to add metric |
| `/metrics/new` | AddMetricPage | Dynamic form for metric definition |
| `/metrics/:id` | MetricDetailPage | Charts, filters, table, FAB to log entry |

**Key Components**
- `MetricCard.vue` — name, latest value, sparkline chart
- `SparklineChart.vue` — tiny ECharts bar chart
- `TimeRangeSelector.vue` — D/W/M/6M/Y button group
- `AggregateSelector.vue` — count/sum/mean dropdown (options depend on value_type)
- `DimensionFilters.vue` — dynamic filter dropdowns per dimension
- `GroupBySelector.vue` — dropdown of available dimensions
- `MetricChart.vue` — bar or stacked bar chart
- `MetricTable.vue` — data table matching chart data
- `LogEntryDialog.vue` — bottom sheet with type-appropriate inputs
- `DimensionBuilder.vue` — add/remove dimensions with chip input for categories

---

## Project Structure

```
biometrics/
  design/                          # Existing (reference only)
  backend/
    app/
      main.py                      # FastAPI app, CORS, lifespan
      config.py                    # Settings
      database.py                  # SQLite connection + schema init
      auth.py                      # JWT verification
      models.py                    # Pydantic models
      routers/
        auth_router.py
        metrics_router.py
        logs_router.py
      services/
        metric_service.py
        log_service.py
        aggregation_service.py     # Timeseries resampling + aggregation
    requirements.txt
    tests/
  frontend/
    src/
      App.vue
      router/
      stores/                      # Pinia (auth, metrics)
      pages/                       # 4 pages
      components/                  # Reusable components
      composables/                 # useAuth, useApi
      layouts/
      boot/firebase.ts
```

---

## Implementation Phases

### Phase 1: Project Scaffolding + Database
- Create FastAPI project structure with `main.py`, `config.py`, `database.py` (auto-creates tables on startup)
- Scaffold Quasar frontend with dark theme + ECharts
- Verify both start cleanly

### Phase 2: Authentication
- Frontend: Firebase init, `useAuth` composable, `LoginPage.vue`, route guards
- Backend: JWT verification middleware (PyJWT + Google public keys), `POST /api/auth/login`, user upsert
- End-to-end: sign in → token → backend creates user in SQLite

### Phase 3: Metric Definition (CRUD)
- Backend: metric create/list/get/delete with categories + dimensions
- Frontend: `DashboardPage.vue` (metric cards, no sparklines yet), `AddMetricPage.vue` (dynamic form with dimension builder)
- Test: create all 5 example metric types

### Phase 4: Log Entry
- Backend: log create/delete with dimension values
- Frontend: `LogEntryDialog.vue` — adapts to metric type (numeric input, categorical select, dimension selects, date/time)
- Test: log entries for each metric type

### Phase 5: Timeseries Aggregation + Detail Page
- Backend: `aggregation_service.py` — range→bucket mapping, SQL GROUP BY with `strftime`, filters, grouping, aggregate functions
- Frontend: `MetricDetailPage.vue` with all controls (time range, aggregate, filters, group-by) + chart + table
- Test with all 5 example metrics from product vision

### Phase 6: Dashboard Sparklines
- Backend: extend `GET /api/metrics` to include latest value + 7-period sparkline data
- Frontend: `SparklineChart.vue` in `MetricCard.vue`

### Phase 7: Polish + Deployment
- Responsive testing, error handling, loading states
- `deploy/run.sh` — starts uvicorn, serves built frontend via FastAPI's StaticFiles
- Optional: systemd service for Pi auto-start

---

## Verification

- **Unit tests**: `tests/test_aggregation.py` covering all value_type × aggregate_function combinations and all 5 resampling rules
- **Manual E2E**: Create each of the 5 example metrics from the product vision, log entries, verify dashboard cards and detail page charts match expected behavior
- **Pi deployment**: Run `deploy/run.sh` on Pi, access from phone browser, verify responsive layout and performance
