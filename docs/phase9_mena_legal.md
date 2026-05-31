# Phase 9 — MENA law-focused ingestion

## What changed

Spiders now target **regulations, rulebooks, and federal legislation** — not marketing or “visit Dubai” pages.

| Spider | Source | Focus |
|--------|--------|--------|
| `uae_legislation` | uaelegislation.gov.ae | Federal laws (AI, data protection) |
| `dfsa_rulebook` | dfsa.ae | DIFC financial rulebook & policy statements |
| `difc_laws` | difc.ae | DIFC laws & regulations index |
| `adgm_fsra` | adgm.com | ADGM legal framework & FSRA rulebooks |
| `sdaia_saudi` | sdaia.gov.sa, regulations.sdaia.gov.sa | PDPL & KSA regulations |
| `uae_ai_office` | u.ae | Federal AI strategy & government policy |
| `digital_dubai` | digitaldubai.ae | AI principles & governance standards only |

## Celery Beat (UTC)

| Time | Task |
|------|------|
| 06:00–07:30 | Each MENA spider (staggered 15 min) |
| 07:50 | `retag_all_documents` |
| 09:00+ | EU / US / UK spiders (unchanged) |

Manual run:

```bash
./scripts/run_mena_spiders.sh
# or
celery -A infra.celery_app call ingestion.tasks.run_all_mena_spiders
```

## Seed sources

```bash
python3 -m ingestion.seed_sources
```

## Notes

- **SDAIA / DFSA** may block bots (Cloudflare). Failures are logged; other spiders still run.
- Re-run `python3 -m ingestion.backfill_published_at` after crawls for new dates.
- PDF-only instruments are skipped until a PDF pipeline exists.
