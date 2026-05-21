# Phase 7 — Polish, Pitch, and Launch

Weeks 21–24 (Days 141–168). Code deliverables are in the repo; the rest is your portfolio work.

## Done in the repo (Day 141 + sources)

| Item | Location |
|------|----------|
| pytest suite (15+ tests) | `tests/` |
| Run tests | `./scripts/run_tests.sh` |
| OECD spider | `./scripts/run_spider.sh oecd_policy` |
| UK AISI spider | `./scripts/run_spider.sh uk_aisi` |
| Seed new sources | `python3 -m ingestion.seed_sources` |

## Your checklist (Days 142–168)

### Days 142–145 — README & docs

- [ ] Add **live demo URL** to README after Railway/Render deploy
- [ ] Add **screenshots** (`docs/screenshots/`): dashboard feed, search, API docs
- [ ] Confirm architecture diagram in README matches your stack

### Days 146–150 — 5-minute demo (Loom)

Suggested script:

1. **Problem (30s):** AI policy changes daily; compliance teams cannot read every source.
2. **Solution (30s):** PolicyPulse ingests EU/US/UK/OECD sources, classifies risk, embeds for search, generates digests.
3. **Dashboard (2m):** Policy feed → filters → expand doc → digest panel → semantic search → recent changes.
4. **API (1m):** `/docs` → `/documents`, `/search`, `/user/feed` with JWT.
5. **Close (30s):** Docker deploy, roadmap (more sources, email alerts, enterprise SSO).

### Days 151–155 — Case study (Medium / dev.to)

Outline (~1500 words): `docs/case_study_outline.md`

Post on LinkedIn with link to repo + demo video.

### Days 156–161 — Premium sources

```bash
python3 -m ingestion.seed_sources
./scripts/run_spider.sh oecd_policy
./scripts/run_spider.sh uk_aisi
python3 -m ingestion.inspect_documents
```

Note: OECD pages are partly SPA; the spider uses listing HTML + meta descriptions. Re-run periodically for new initiatives.

### Days 162–168 — Accelerators

| Program | URL | Fit |
|---------|-----|-----|
| Y Combinator | https://www.ycombinator.com/apply | B2B compliance / govtech angle |
| Mozilla Builders | https://builders.mozilla.org | Trustworthy / open AI |
| NSF I-Corps | https://www.nsf.gov/i-corps | Research-to-market, no equity |

Prep: one-pager from README + demo link + traction (# documents, sources, test count).

## Commands

```bash
pip install pytest pytest-asyncio httpx
./scripts/run_tests.sh
```
