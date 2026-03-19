# Biometrics Tracker

A health metrics tracking app with a Vue 3 frontend (Quasar) and FastAPI backend.

## Architecture

In production, the FastAPI backend serves both the API (`/api/*`) and the built frontend static files on a single port (8000). Nginx terminates SSL and proxies `biometrics.avilay.rocks` to the backend.

## Development

### Prerequisites

- Node.js + npm
- Python 3.12+ + [uv](https://docs.astral.sh/uv/)

### Running locally

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to the backend on port 8000.

## Deployment

### Server prerequisites

- nginx
- [uv](https://docs.astral.sh/uv/)
- Cloudflare origin certificates at `/etc/cloudflare/cert.pem` and `/etc/cloudflare/privkey.pem`
- DNS for `biometrics.avilay.rocks` pointing to the server

### Step 1: Build locally

```bash
./deploy/build.sh
```

This creates a `build/` directory containing:

```
build/
├── backend/          # Python source + pyproject.toml
├── frontend/
│   └── dist/         # Pre-built frontend assets
├── deploy/
│   ├── run.sh        # Server setup script
│   ├── biometrics.conf      # Nginx config
│   └── biometrics.service   # Systemd unit file
└── .env              # Environment variables
```

### Step 2: Copy to server

```bash
scp -r build/ user@server:/opt/biometrics
```

### Step 3: Edit environment variables

On the server, review and update `/opt/biometrics/.env`:

```
DATABASE_URL=biometrics.db
FIREBASE_PROJECT_ID=avilabs-271703
```

### Step 4: Run the setup script

```bash
ssh user@server
cd /opt/biometrics
sudo bash deploy/run.sh
```

This will:
1. Install backend Python dependencies via `uv sync`
2. Create a `biometrics` system user
3. Install the nginx site config and reload nginx
4. Install and start the `biometrics` systemd service

### Step 5: Seed demo data

The demo login feature requires seed data. Run this once on a new deployment (or to reset demo data):

```bash
cd /opt/biometrics/backend
sudo -u biometrics .venv/bin/python -m seed_data
```

### Managing the service

```bash
sudo systemctl status biometrics     # Check status
sudo systemctl restart biometrics    # Restart
sudo journalctl -u biometrics -f     # Tail logs
```
