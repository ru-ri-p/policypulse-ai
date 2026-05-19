#!/usr/bin/env bash
# Run Scrapy from project root so ingestion.db imports resolve.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}"
cd "${ROOT}/ingestion"
exec scrapy crawl "$@"
