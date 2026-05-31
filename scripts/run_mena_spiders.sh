#!/usr/bin/env bash
# Run all MENA law-focused spiders, then retag documents.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
source .venv/bin/activate
export PYTHONPATH="${ROOT}"

SPIDERS=(
  uae_legislation
  dfsa_rulebook
  difc_laws
  adgm_fsra
  sdaia_saudi
  uae_ai_office
  digital_dubai
)

for name in "${SPIDERS[@]}"; do
  echo "=== crawl ${name} ==="
  (cd ingestion && scrapy crawl "${name}") || echo "WARN: ${name} failed (continuing)"
done

echo "=== retag ==="
python3 -m ingestion.retag_documents
python3 -m ingestion.backfill_published_at
echo "Done."
