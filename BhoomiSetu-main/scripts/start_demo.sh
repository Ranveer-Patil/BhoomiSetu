#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
backend_port="${BHOOMISETU_BACKEND_PORT:-8000}"
frontend_port="${BHOOMISETU_FRONTEND_PORT:-3000}"

"$project_root/scripts/reset_demo.sh"

cd "$project_root/apps/backend"
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$backend_port" &
backend_pid=$!

cd "$project_root/apps/frontend"
npm run start -- --hostname 127.0.0.1 --port "$frontend_port" &
frontend_pid=$!

cleanup() {
  kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "BhoomiSetu is starting: frontend http://127.0.0.1:$frontend_port · API http://127.0.0.1:$backend_port/docs"
wait "$backend_pid" "$frontend_pid"
