#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
source .venv/bin/activate
export PYTHONPATH="${ROOT}"
exec uvicorn api.main:app --reload --port 8000
