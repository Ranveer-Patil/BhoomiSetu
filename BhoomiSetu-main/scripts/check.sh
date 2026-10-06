#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$project_dir/apps/backend"
.venv/bin/ruff check .
.venv/bin/pytest

cd "$project_dir/apps/frontend"
npm run lint
npm test
npm run build

