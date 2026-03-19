#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Biometrics Server Setup ==="

# 1. Install backend dependencies
echo "Installing backend dependencies..."
cd "$PROJECT_DIR/backend"
UV_PYTHON_INSTALL_DIR=/opt/uv/python uv sync

# 2. Verify frontend dist exists
if [ ! -d "$PROJECT_DIR/frontend/dist" ]; then
    echo "ERROR: frontend/dist not found. Run build.sh first."
    exit 1
fi

# 3. Create biometrics user if it doesn't exist
if ! id -u biometrics &>/dev/null; then
    echo "Creating biometrics user..."
    useradd --system --no-create-home --shell /usr/sbin/nologin biometrics
fi
chown -R biometrics:biometrics "$PROJECT_DIR"
chmod -R u+rwX "$PROJECT_DIR"

# 4. Install nginx configs
echo "Setting up nginx..."
cp "$SCRIPT_DIR/biometrics.conf" /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/biometrics.conf /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# 5. Update systemd service with correct paths
sed "s|WorkingDirectory=.*|WorkingDirectory=$PROJECT_DIR/backend|" "$SCRIPT_DIR/biometrics.service" \
    | sed "s|EnvironmentFile=.*|EnvironmentFile=$PROJECT_DIR/.env|" \
    | sed "s|ExecStart=.*|ExecStart=$PROJECT_DIR/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000|" \
    > /etc/systemd/system/biometrics.service

systemctl daemon-reload
systemctl enable biometrics
systemctl restart biometrics

echo ""
echo "=== Deployment complete ==="
echo "Check status: systemctl status biometrics"
echo "View logs:    journalctl -u biometrics -f"
