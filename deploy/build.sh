#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build"

echo "=== Building Biometrics Deployment Package ==="

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/frontend" "$BUILD_DIR/deploy"

# 1. Build frontend
echo "Building frontend..."
cd "$PROJECT_DIR/frontend"
npm install
npx vite build
cp -r dist "$BUILD_DIR/frontend/"

# 2. Copy backend source (no .venv — will be created on server)
echo "Copying backend..."
rsync -a --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' --exclude 'biometrics.db' \
    "$PROJECT_DIR/backend/" "$BUILD_DIR/backend/"

# 3. Copy deploy files
echo "Copying deploy files..."
cp "$SCRIPT_DIR/run.sh" "$BUILD_DIR/deploy/"
cp "$SCRIPT_DIR/biometrics.service" "$BUILD_DIR/deploy/"
cp "$SCRIPT_DIR/biometrics.conf" "$BUILD_DIR/deploy/"

# 4. Copy Firebase credentials
echo "Copying Firebase credentials..."
cp "$PROJECT_DIR/avilabs-271703-6e398aa5a10c.json" "$BUILD_DIR/"

# 5. Copy version file
cp "$PROJECT_DIR/VERSION.txt" "$BUILD_DIR/"

# 6. Copy production env template
echo "Creating .env..."
cat > "$BUILD_DIR/.env" <<'EOF'
DATABASE_URL=biometrics.db
FIREBASE_PROJECT_ID=avilabs-271703
FIREBASE_CREDENTIALS=/opt/biometrics/avilabs-271703-6e398aa5a10c.json
EOF

echo ""
echo "=== Build complete: $BUILD_DIR ==="
echo ""
echo "To deploy, copy the build directory to your server and run:"
echo "  scp -r $BUILD_DIR user@server:/opt/biometrics"
echo "  ssh user@server 'cd /opt/biometrics && sudo bash deploy/run.sh'"
