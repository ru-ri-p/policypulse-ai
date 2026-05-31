# Layer 2 — Zones, playbooks & weekly PDF

## What this adds

1. **Zone / sector tags** on each document (`DIFC`, `ADGM`, `MAINLAND`, sectors like `financial_services`).
2. **Playbooks** — rule-based impact levels (high / medium / low) per regulatory context.
3. **Exposure packs** — client profiles that define which playbooks and jurisdictions matter.
4. **Weekly PDF brief** — branded summary for demos and pilot clients.

## Exposure packs

| Pack | Use case |
|------|----------|
| `dubai_hq` | Dubai HQ with GCC operations **and** EU + US + UK exposure (recommended default) |
| `mena_only` | GCC-only footprint |
| `eu_exposure_only` | EU AI Act / GDPR focus |

**Dubai HQ should not be EU-only.** Companies in DIFC/ADGM often serve US clients, use US cloud vendors, or process EU data — so `dubai_hq` includes UAE playbooks plus `eu_ai_act_exposure`, `us_federal_ai_exposure`, and `uk_ico`.

## Setup

```bash
psql -U ppuser -d policypulse -f ingestion/migrations/009_zones_sectors_playbooks.sql
python3 -m ingestion.retag_documents
pip install reportlab
```

## API

- `GET /playbooks/` — list playbooks
- `GET /playbooks/exposure-packs` — list packs
- `GET /playbooks/exposure-packs/dubai_hq` — pack detail
- `GET /documents/?zone=DIFC&sector=financial_services`
- `GET /playbooks/impacts/{doc_id}?exposure_pack=dubai_hq`

## Weekly PDF

```bash
chmod +x scripts/generate_weekly_brief.sh
./scripts/generate_weekly_brief.sh --exposure-pack dubai_hq --days 7
```

Output defaults to `docs/briefs/weekly_brief_<date>.pdf`.

## Dashboard

Sidebar: **Zone**, **Exposure pack**. Policy cards show zones, sectors, and playbook impacts filtered by the selected pack. **Weekly brief** tab shows pack scope and the shell command.

## Backfill

Re-run after changing playbook YAML:

```bash
python3 -m ingestion.retag_documents
# optional: python3 -m ingestion.retag_documents --limit 100
```
