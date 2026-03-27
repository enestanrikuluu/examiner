#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Examiner - Single VPS Deploy Script
# Usage: ./deploy.sh
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# --- Pre-flight checks ---
info "Running pre-flight checks..."

command -v docker >/dev/null 2>&1 || error "Docker is not installed. Run: curl -fsSL https://get.docker.com | sh"
docker compose version >/dev/null 2>&1 || error "Docker Compose V2 is not installed."

if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        warn ".env not found. Copying from .env.production..."
        cp .env.production .env
        warn ""
        warn "  >>> EDIT .env NOW with your real values, then re-run this script. <<<"
        warn ""
        warn "  At minimum set these 3 values:"
        warn "    POSTGRES_PASSWORD=<strong password>"
        warn "    JWT_SECRET=<run: openssl rand -hex 32>"
        warn "    CORS_ORIGINS=[\"http://YOUR_SERVER_IP\"]"
        warn ""
        warn "  Edit with: nano .env"
        exit 1
    else
        error "No .env or .env.production found. Cannot deploy."
    fi
fi

# Validate critical env vars
set -a
source .env
set +a

if [ "${JWT_SECRET:-}" = "CHANGE_ME_GENERATE_WITH_OPENSSL_RAND_HEX_32" ] || [ -z "${JWT_SECRET:-}" ]; then
    error "JWT_SECRET is not set. Generate one with: openssl rand -hex 32"
fi
if [ "${POSTGRES_PASSWORD:-}" = "CHANGE_ME_STRONG_PASSWORD" ] || [ -z "${POSTGRES_PASSWORD:-}" ]; then
    error "POSTGRES_PASSWORD is not set. Pick a strong password."
fi

info "Environment validated."

# --- Build ---
info "Building Docker images (first run takes 5-10 minutes)..."
docker compose build --parallel

# --- Start infrastructure first ---
info "Starting database, cache, and storage..."
docker compose up -d postgres redis minio

info "Waiting for Postgres to be ready..."
until docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-examiner}" >/dev/null 2>&1; do
    sleep 2
done
info "Postgres is ready."

# --- Run migrations ---
info "Starting API container for migrations..."
docker compose up -d api

info "Waiting for API to start..."
sleep 5

# Check if any migration files exist
MIGRATION_COUNT=$(find apps/api/alembic/versions -name '*.py' 2>/dev/null | wc -l | tr -d ' ')

if [ "$MIGRATION_COUNT" = "0" ]; then
    info "No migrations found. Generating initial migration..."
    docker compose exec -T api alembic revision --autogenerate -m "initial schema" || error "Migration generation failed. Check: docker compose logs api"
    info "Initial migration created."
fi

info "Applying migrations..."
docker compose exec -T api alembic upgrade head || error "Migration failed. Check: docker compose logs api"
info "Migrations applied."

# --- Seed admin (optional) ---
if [ -n "${ADMIN_PASSWORD:-}" ]; then
    info "Creating admin user..."
    docker compose exec -T api python scripts/seed_admin.py || warn "Admin seed failed (user may already exist)"
fi

# --- Start all services ---
info "Starting all services..."
docker compose up -d

# --- Wait for health ---
info "Waiting for services to be healthy..."
MAX_WAIT=90
WAITED=0
API_HEALTHY=false
until docker compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" >/dev/null 2>&1; do
    sleep 3
    WAITED=$((WAITED + 3))
    if [ $WAITED -ge $MAX_WAIT ]; then
        break
    fi
done

if [ $WAITED -lt $MAX_WAIT ]; then
    API_HEALTHY=true
    info "API is healthy."
else
    warn "API did not become healthy after ${MAX_WAIT}s."
    warn "Check logs: docker compose logs api"
fi

# --- Status ---
echo ""
echo "========================================="
info "Deployment complete!"
echo "========================================="
echo ""
docker compose ps --format "table {{.Name}}\t{{.Status}}"
echo ""

SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
PORT="${PORT:-80}"

if [ "$API_HEALTHY" = true ]; then
    info "App is running at: http://${SERVER_IP}:${PORT}"
else
    warn "App may still be starting. Check: docker compose ps"
fi

echo ""
echo "Useful commands:"
echo "  docker compose logs -f          # Follow all logs"
echo "  docker compose logs -f api      # API logs only"
echo "  docker compose ps               # Service status"
echo "  docker compose restart           # Restart all"
echo "  docker compose down              # Stop everything"
echo "  docker compose up -d --build     # Rebuild & restart"
echo ""

# --- Setup backups (optional) ---
setup_backups() {
    info "Setting up daily Postgres backups..."

    # Create backups directory
    mkdir -p ~/backups

    # Create backup script
    cat > ~/backups/backup-examiner.sh << 'BACKUP_SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="$HOME/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose -f /root/examiner/docker-compose.yml exec -T postgres pg_dump -U examiner examiner | gzip > "$BACKUP_DIR/examiner_$TIMESTAMP.sql.gz"
# Delete backups older than 7 days
find "$BACKUP_DIR" -name "examiner_*.sql.gz" -mtime +7 -delete
BACKUP_SCRIPT

    chmod +x ~/backups/backup-examiner.sh

    # Add to crontab if not already present
    if ! (crontab -l 2>/dev/null | grep -q "backup-examiner.sh"); then
        (crontab -l 2>/dev/null; echo "0 3 * * * $HOME/backups/backup-examiner.sh") | crontab -
        info "Daily backup cron job added (runs at 3 AM)"
    else
        info "Backup job already in crontab"
    fi

    info "Backups are configured!"
}

# Uncomment the line below to enable daily backups
# setup_backups
