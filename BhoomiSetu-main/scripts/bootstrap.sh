#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"

cd "$project_root"
docker compose up -d db

if [[ ! -f apps/backend/.env ]]; then
  cp apps/backend/.env.example apps/backend/.env
fi
if [[ ! -f apps/frontend/.env.local ]]; then
  cp apps/frontend/.env.example apps/frontend/.env.local
fi

cd "$project_root/apps/backend"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python scripts/train_models.py
.venv/bin/python -m scripts.seed_data --if-empty

cd "$project_root/apps/frontend"
npm ci

echo "Setup complete. Run ./scripts/start_demo.sh from the repository root."
