# Phase 8 — MENA Source Coverage

Extends PolicyPulse from US/EU-centric to **GCC-first** with UAE, Saudi, and free zone sources.

## New sources

| Spider | Source | Jurisdiction | Command |
|--------|--------|--------------|---------|
| `uae_ai_office` | UAE Government AI Portal (u.ae) | UAE | `./scripts/run_spider.sh uae_ai_office` |
| `digital_dubai` | Digital Dubai AI Ethics & Data | UAE | `./scripts/run_spider.sh digital_dubai` |
| `difc_laws` | DIFC Laws & Regulations | UAE | `./scripts/run_spider.sh difc_laws` |
| `adgm_fsra` | ADGM FSRA Announcements | UAE | `./scripts/run_spider.sh adgm_fsra` |
| `sdaia_saudi` | Saudi SDAIA / NDMO | SA | `./scripts/run_spider.sh sdaia_saudi` |

## Data model changes

Migration: `ingestion/migrations/008_mena_region.sql`

- `documents.region` — high-level grouping: `MENA`, `EU`, `US`, `UK`, `OTHER`
- `sources.region` — same
- Indexes on `jurisdiction` and `region`
- Backfill script sets region from existing jurisdiction values

## Region mapping (`ingestion/regions.py`)

| Jurisdiction | Region |
|--------------|--------|
| UAE, SA, QA, BH, KW, OM, EG, GCC | MENA |
| EU, OECD | EU |
| US | US |
| UK | UK |

## API changes

`GET /documents/` now accepts `?region=MENA` (filters all GCC jurisdictions).

`GET /stats/` response includes `by_region` map.

## Dashboard

- **Region dropdown** defaults to `MENA` so demos show GCC content first
- Stats tab shows region pie chart alongside jurisdiction bar chart
- MENA document count metric in stats header

## Classifier

Added zero-shot labels:
- "United Arab Emirates or Gulf Cooperation Council policy" → `UAE`
- "Saudi Arabia policy" → `SA`

## Digest prompt

Reframed for "organisations operating in UAE/GCC" including EU extraterritorial exposure.

## How to run

```bash
# Apply migration
psql -U ppuser -d policypulse -f ingestion/migrations/008_mena_region.sql

# Seed new sources
python3 -m ingestion.seed_sources

# Run MENA spiders
./scripts/run_spider.sh uae_ai_office
./scripts/run_spider.sh digital_dubai
./scripts/run_spider.sh adgm_fsra
./scripts/run_spider.sh difc_laws
./scripts/run_spider.sh sdaia_saudi

# Verify
python3 -m ingestion.inspect_documents
```

## Notes

- `sdaia.gov.sa` uses Cloudflare protection — spider uses browser-like UA and gracefully skips blocked pages
- `uaelegislation.gov.ae` blocks bots; we use `u.ae` official portal instead
- DIFC/ADGM filter on AI/data/fintech keywords to avoid noise
- OECD spider already classifies some docs as GCC jurisdictions (Japan, etc.) — these map correctly via region
