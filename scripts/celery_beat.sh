#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
source .venv/bin/activate
export PYTHONPATH="${ROOT}"
exec celery -A infra.celery_app beat --loglevel=info
