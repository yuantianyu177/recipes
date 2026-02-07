#!/bin/bash
# =============================================================
# setup.sh - One-click development environment setup
# Recipe App
# =============================================================
set -e

# ---- Color helpers ----
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

step=0
total_steps=9

progress() {
  step=$((step + 1))
  echo -e "\n${GREEN}[${step}/${total_steps}]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

fail() {
  echo -e "${RED}[ERROR]${NC} $1"
  exit 1
}

ok() {
  echo -e "  ${GREEN}✔${NC} $1"
}

# ---- 1. Check prerequisites ----
progress "Checking prerequisites..."

command -v git >/dev/null 2>&1 || fail "git is not installed. Please install git first."
ok "git $(git --version | awk '{print $3}')"

command -v curl >/dev/null 2>&1 || fail "curl is not installed. Please install curl first."
ok "curl found"

# ---- 2. Install Node.js via nvm ----
progress "Checking Node.js..."

export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

if command -v node >/dev/null 2>&1; then
  NODE_VER=$(node -v)
  ok "Node.js ${NODE_VER} already installed"
else
  warn "Node.js not found, installing via nvm..."
  if [ ! -s "$NVM_DIR/nvm.sh" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
  fi
  nvm install --lts
  nvm use --lts
  ok "Node.js $(node -v) installed"
fi

# ---- 3. Install Python 3.11+ ----
progress "Checking Python..."

PYTHON_CMD=""
for cmd in python3.12 python3.11 python3; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PY_VER=$("$cmd" --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
      PYTHON_CMD="$cmd"
      break
    fi
  fi
done

if [ -n "$PYTHON_CMD" ]; then
  ok "Python $($PYTHON_CMD --version 2>&1 | awk '{print $2}') found ($PYTHON_CMD)"
else
  warn "Python 3.11+ not found. Attempting to install via system package manager..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv python3-pip
    PYTHON_CMD="python3.11"
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3.11
    PYTHON_CMD="python3.11"
  elif command -v brew >/dev/null 2>&1; then
    brew install python@3.11
    PYTHON_CMD="python3.11"
  else
    fail "Cannot auto-install Python 3.11+. Please install manually."
  fi
  ok "Python $($PYTHON_CMD --version 2>&1 | awk '{print $2}') installed"
fi

# ---- 4. Install Docker & Docker Compose ----
progress "Checking Docker..."

if command -v docker >/dev/null 2>&1; then
  ok "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
else
  warn "Docker not found. Installing..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  ok "Docker installed (you may need to log out and back in for group permissions)"
fi

if docker compose version >/dev/null 2>&1; then
  ok "Docker Compose (plugin) found"
elif command -v docker-compose >/dev/null 2>&1; then
  ok "docker-compose $(docker-compose --version | awk '{print $3}' | tr -d ',')"
else
  warn "Docker Compose not found. It should come with Docker Desktop or the docker-compose-plugin package."
fi

# ---- 5. Start dev containers ----
progress "Starting development containers (PostgreSQL + MeiliSearch)..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/.env" ]; then
  ok "Using existing .env file"
else
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  ok "Created .env from .env.example"
fi

COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
fi

$COMPOSE_CMD -f "$SCRIPT_DIR/docker-compose.dev.yml" --env-file "$SCRIPT_DIR/.env" up -d
ok "PostgreSQL and MeiliSearch containers started"

# ---- 6. Setup frontend ----
progress "Setting up frontend..."

if [ -d "$SCRIPT_DIR/frontend" ] && [ -f "$SCRIPT_DIR/frontend/package.json" ]; then
  cd "$SCRIPT_DIR/frontend"
  npm install
  ok "Frontend dependencies installed"
else
  warn "Frontend project not yet created, skipping npm install (will be set up in Phase 1)"
fi

# ---- 7. Setup backend ----
progress "Setting up backend..."

if [ -d "$SCRIPT_DIR/backend" ] && [ -f "$SCRIPT_DIR/backend/requirements.txt" ]; then
  cd "$SCRIPT_DIR/backend"
  if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    ok "Python virtual environment created"
  else
    ok "Python virtual environment already exists"
  fi
  . venv/bin/activate
  pip install --upgrade pip -q
  pip install -r requirements.txt -q
  ok "Backend dependencies installed"
else
  warn "Backend project not yet created, skipping pip install (will be set up in Phase 2)"
fi

# ---- 8. Generate .env ----
progress "Verifying .env configuration..."

cd "$SCRIPT_DIR"
if [ -f ".env" ]; then
  ok ".env file exists"
else
  cp .env.example .env
  ok ".env created from .env.example"
fi

# ---- 9. Verify services ----
progress "Verifying all services are running..."

echo "  Waiting for containers to be healthy..."
sleep 3

# Check PostgreSQL
if $COMPOSE_CMD -f "$SCRIPT_DIR/docker-compose.dev.yml" --env-file "$SCRIPT_DIR/.env" ps --format '{{.Status}}' postgres 2>/dev/null | grep -qi "up\|healthy"; then
  ok "PostgreSQL is running on port ${POSTGRES_PORT:-5432}"
else
  # Fallback check
  if $COMPOSE_CMD -f "$SCRIPT_DIR/docker-compose.dev.yml" --env-file "$SCRIPT_DIR/.env" ps | grep -i postgres | grep -qi "up"; then
    ok "PostgreSQL is running on port ${POSTGRES_PORT:-5432}"
  else
    warn "PostgreSQL may not be running. Check with: docker compose -f docker-compose.dev.yml ps"
  fi
fi

# Check MeiliSearch
if curl -sf http://localhost:7700/health >/dev/null 2>&1; then
  ok "MeiliSearch is running on port 7700"
else
  warn "MeiliSearch may not be ready yet. Check with: curl http://localhost:7700/health"
fi

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}  Environment setup complete!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "  PostgreSQL:  localhost:${POSTGRES_PORT:-5432}"
echo "  MeiliSearch: http://localhost:7700"
echo ""
echo "  Next steps:"
echo "    - Frontend dev:  cd frontend && npm run dev"
echo "    - Backend dev:   cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo ""
