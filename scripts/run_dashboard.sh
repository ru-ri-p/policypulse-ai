#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
source .venv/bin/activate
export API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
exec streamlit run dashboard/app.py
