#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
backend_dir="$project_root/apps/backend"

cd "$backend_dir"
.venv/bin/alembic upgrade head
.venv/bin/python scripts/train_models.py
.venv/bin/python -m scripts.seed_data

cd "$project_root/apps/frontend"
npm run build

echo "BhoomiSetu demo state is ready: 5 roles, 20 varied cases, OSM parcels, 2 ML models and a production frontend build."
