#!/usr/bin/env python3
# reports/team_handover_pdf.py — generate team handover / briefing PDF
"""
Generate a detailed PolicyPulse AI handover document for BD, engineering, and leadership.

Example:
  python3 -m reports.team_handover_pdf
  python3 -m reports.team_handover_pdf -o docs/PolicyPulse_Team_Handover.pdf
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as exc:
    raise SystemExit("Install reportlab: pip install reportlab") from exc

REPO = "https://github.com/ru-ri-p/policypulse-ai"
GENERATED = datetime.now(timezone.utc).strftime("%d %B %Y")


def _esc(text: str) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def _fetch_live_stats() -> dict:
    try:
        from ingestion.db import run_query

        total = run_query("SELECT COUNT(*) FROM documents", fetch=True)[0][0]
        by_j = run_query(
            "SELECT jurisdiction, COUNT(*) FROM documents GROUP BY 1 ORDER BY 2 DESC",
            fetch=True,
        )
        by_r = run_query(
            "SELECT region, COUNT(*) FROM documents GROUP BY 1 ORDER BY 2 DESC",
            fetch=True,
        )
        pub = run_query(
            "SELECT COUNT(*) FROM documents WHERE published_at IS NOT NULL", fetch=True
        )[0][0]
        mena = run_query(
            "SELECT COUNT(*) FROM documents WHERE jurisdiction IN ('UAE','SA')",
            fetch=True,
        )[0][0]
        dig = run_query(
            "SELECT COUNT(*) FROM documents WHERE digest_what_changed IS NOT NULL",
            fetch=True,
        )[0][0]
        emb = run_query(
            "SELECT COUNT(*) FROM documents WHERE embedding IS NOT NULL", fetch=True
        )[0][0]
        mena_src = run_query(
            """
            SELECT s.name, COUNT(*) FROM documents d
            JOIN sources s ON s.id = d.source_id
            WHERE d.jurisdiction IN ('UAE','SA')
            GROUP BY s.name ORDER BY 2 DESC
            """,
            fetch=True,
        )
        zones = run_query(
            """
            SELECT unnest(zones) z, COUNT(*) FROM documents
            WHERE jurisdiction IN ('UAE','SA') AND array_length(zones,1)>0
            GROUP BY 1 ORDER BY 2 DESC
            """,
            fetch=True,
        )
        return {
            "live": True,
            "total": total,
            "by_j": by_j,
            "by_r": by_r,
            "published": pub,
            "mena": mena,
            "digests": dig,
            "embedded": emb,
            "mena_src": mena_src,
            "zones": zones,
        }
    except Exception:
        return {
            "live": False,
            "total": 1173,
            "by_j": [("US", 1114), ("UAE", 22), ("EU", 20), ("UK", 17)],
            "by_r": [("US", 1114), ("MENA", 22), ("EU", 20), ("UK", 17)],
            "published": 1070,
            "mena": 22,
            "digests": 0,
            "embedded": 40,
            "mena_src": [
                ("UAE AI Office", 10),
                ("Digital Dubai", 10),
                ("DIFC Data & AI Regulation", 2),
            ],
            "zones": [("MAINLAND", 20), ("DIFC", 2)],
        }


def _styles():
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Heading1"],
            fontSize=26,
            leading=32,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1a365d"),
            spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub",
            parent=base["Normal"],
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4a5568"),
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#1a365d"),
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#2c5282"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
            leftIndent=14,
            spaceAfter=3,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontSize=8,
            leading=11,
            textColor=colors.grey,
        ),
    }


def _section(story, styles, title: str, items: list[str]):
    story.append(Paragraph(title, styles["h1"]))
    for item in items:
        story.append(Paragraph(f"• {_esc(item)}", styles["bullet"]))
    story.append(Spacer(1, 0.2 * cm))


def _table(story, headers: list[str], rows: list[list], col_widths=None):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))


def build_handover_pdf(output_path: Path, stats: dict) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="PolicyPulse AI — Team Handover Brief",
        author="PolicyPulse AI",
    )
    s = _styles()
    story: list = []

    # ── Cover ───────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("PolicyPulse AI", s["cover_title"]))
    story.append(Paragraph("Team Handover &amp; Briefing Document", s["cover_sub"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            f"For business development, software engineering, product, and leadership<br/>"
            f"Generated: {_esc(GENERATED)} (UTC)<br/>"
            f"Repository: {_esc(REPO)}",
            s["cover_sub"],
        )
    )
    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            "<i>AI policy monitoring for compliance teams in the UAE/GCC and beyond.</i>",
            s["cover_sub"],
        )
    )
    story.append(PageBreak())

    # ── 1. Executive summary ────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", s["h1"]))
    story.append(
        Paragraph(
            _esc(
                "PolicyPulse AI is an AI policy monitoring and compliance intelligence platform "
                "built for organisations in Dubai/GCC that must track local regulations "
                "(UAE, DIFC, ADGM, Saudi) and extraterritorial exposure (EU AI Act, US federal "
                "AI policy, UK ICO). It automatically ingests official policy sources, detects "
                "changes, classifies risk, tags by zone and sector, maps playbook impact, and can "
                "produce LLM compliance digests and weekly PDF briefs."
            ),
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>Positioning:</b> MENA-first AI policy monitor with zone/playbook layers and "
            "extraterritorial exposure packs — not a generic global feed, not internal-only GCC "
            "governance, not search-only legal tech.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>Status:</b> Working prototype, demo-ready locally. Layer 2 (playbooks, zones, "
            "weekly PDF), publication dates, and Phase 9 (MENA law spiders + Celery Beat) are "
            "implemented locally but not yet pushed to GitHub. No production deploy URL yet.",
            s["body"],
        )
    )
    story.append(PageBreak())

    # ── 2. What the product does ────────────────────────────────────
    story.append(Paragraph("2. What the Product Does", s["h1"]))
    _table(
        story,
        ["Capability", "Description"],
        [
            ["Ingestion", "Scrapy spiders pull policy text from official portals into PostgreSQL"],
            ["Change tracking", "Archives prior versions; flags % change and major updates (>20%)"],
            ["Classification", "Zero-shot ML: jurisdiction, doc type, risk level"],
            ["Semantic search", "pgvector + sentence-transformers (all-MiniLM-L6-v2)"],
            ["Compliance digests", "GPT-4o-mini: what changed, who affected, what to do, urgency"],
            ["Personalised feed", "JWT users + profile → relevance scoring"],
            ["Alerts", "Nightly email for high-relevance + urgent changes (SMTP required)"],
            ["Zones & playbooks", "DIFC/ADGM/MAINLAND tags + rule-based impact levels"],
            ["Exposure packs", "Client profiles: dubai_hq, mena_only, eu_exposure_only"],
            ["Weekly PDF brief", "Branded ReportLab report for investors/clients"],
            ["Dashboard", "Streamlit: feed, search, changes, stats, weekly brief tab"],
            ["REST API", "FastAPI v0.4.0 — documents, search, auth, playbooks, stats"],
        ],
        col_widths=[4.5 * cm, 12.5 * cm],
    )

    # ── 3. Target market ──────────────────────────────────────────
    story.append(Paragraph("3. Target Market &amp; GTM", s["h1"]))
    _table(
        story,
        ["Segment", "Value proposition"],
        [
            ["DIFC/ADGM fintech", "Zone playbooks + EU/US extraterritorial packs"],
            ["Dubai HQ multinationals", "One feed: UAE + EU AI Act + US federal exposure"],
            ["Law firms / consultancies", "White-label policy intelligence (B2B2B API)"],
            ["AI governance leads", "Change alerts, digests, version audit trail"],
        ],
        col_widths=[5 * cm, 12 * cm],
    )
    story.append(
        Paragraph(
            "<b>Default demo pack:</b> dubai_hq (GCC + EU + US + UK — not EU-only).",
            s["body"],
        )
    )
    story.append(PageBreak())

    # ── 4. Architecture ─────────────────────────────────────────────
    story.append(Paragraph("4. Technical Architecture", s["h1"]))
    story.append(
        Paragraph(
            _esc(
                "Sources (Scrapy) → Postgres pipeline → Change detector → "
                "Celery + Redis (spiders, ML, digests, alerts) → "
                "PostgreSQL 16 + pgvector → FastAPI → Streamlit dashboard"
            ),
            s["body"],
        )
    )
    _table(
        story,
        ["Component", "Technology"],
        [
            ["Language", "Python 3.13"],
            ["Ingestion", "Scrapy, custom pipelines"],
            ["Database", "PostgreSQL 16, pgvector"],
            ["Queue", "Redis + Celery Beat"],
            ["API", "FastAPI, JWT, Pydantic"],
            ["UI", "Streamlit, Plotly"],
            ["ML", "sentence-transformers, BART-MNLI (zero-shot)"],
            ["LLM", "OpenAI GPT-4o-mini (optional digests)"],
            ["PDF", "ReportLab"],
            ["Tests", "pytest (51 tests)"],
            ["Deploy", "Docker Compose (local); production TBD"],
        ],
        col_widths=[4.5 * cm, 12.5 * cm],
    )

    # ── 5. Build history ────────────────────────────────────────────
    story.append(Paragraph("5. Everything Built (Phases 1–9 + Layer 2)", s["h1"]))

    phases = [
        (
            "Phase 1–3 — Foundation",
            [
                "PostgreSQL schema, Scrapy pipeline, change detection",
                "Celery + Redis scheduling",
                "FastAPI: JWT, documents, search, stats, alerts",
                "Spiders: EU AI Act, US Federal Register, NIST, UK ICO",
            ],
        ),
        (
            "Phase 4 — LLM digests",
            [
                "Structured digest columns (what/who/todo/urgency/deadline)",
                "digests/run_digests.py + Celery batch task",
            ],
        ),
        (
            "Phase 5 — Relevance & alerts",
            [
                "User profiles, personalised /user/feed",
                "Nightly relevance email alerts",
            ],
        ),
        (
            "Phase 6 — Dashboard & Docker",
            ["Streamlit dashboard", "Docker Compose full stack"],
        ),
        (
            "Phase 7 — Polish",
            [
                "51 pytest tests",
                "OECD + UK AISI spiders",
                "Case study + launch docs",
            ],
        ),
        (
            "Phase 8 — MENA coverage",
            [
                "region column, MENA spiders (UAE, DIFC, ADGM, SDAIA, Digital Dubai)",
                "Classifier MENA labels, API region filter",
                "Dashboard MENA default (later changed to All)",
            ],
        ),
        (
            "Layer 2 — Zones, playbooks, weekly PDF",
            [
                "zones, sectors, playbook_impacts on documents",
                "YAML playbooks + exposure packs (dubai_hq includes EU+US)",
                "API /playbooks, zone/sector filters",
                "Weekly PDF generator (ReportLab)",
                "Dashboard zone filter, playbook impacts, weekly brief tab",
            ],
        ),
        (
            "Layer 2.5 — Dates & UX",
            [
                "first_scraped_at, publication date extraction",
                "Dashboard: Published vs Ingested, update status badges",
                "Keyword filter, zone guide in sidebar",
            ],
        ),
        (
            "Phase 9 — MENA law-focused ingestion",
            [
                "New spiders: uae_legislation, dfsa_rulebook",
                "Refocused DIFC, ADGM, SDAIA, Digital Dubai (law URLs only)",
                "Celery Beat: MENA daily 06:00–07:50 UTC + retag",
                "scripts/run_mena_spiders.sh manual runner",
            ],
        ),
    ]
    for title, items in phases:
        story.append(Paragraph(title, s["h2"]))
        for item in items:
            story.append(Paragraph(f"• {_esc(item)}", s["bullet"]))
    story.append(PageBreak())

    # ── 6. Current data ─────────────────────────────────────────────
    story.append(Paragraph("6. Current Data Snapshot", s["h1"]))
    live_note = (
        "Live from local database at generation time."
        if stats["live"]
        else "Fallback figures (database unavailable at generation)."
    )
    story.append(Paragraph(_esc(live_note), s["small"]))

    _table(
        story,
        ["Metric", "Count"],
        [
            ["Total documents", str(stats["total"])],
            ["With publication date", str(stats["published"])],
            ["MENA (UAE + SA)", str(stats["mena"])],
            ["With compliance digest", str(stats["digests"])],
            ["With embeddings (searchable)", str(stats["embedded"])],
        ],
        col_widths=[8 * cm, 9 * cm],
    )

    story.append(Paragraph("By jurisdiction", s["h2"]))
    _table(
        story,
        ["Jurisdiction", "Documents"],
        [[j, str(c)] for j, c in stats["by_j"]],
        col_widths=[8 * cm, 9 * cm],
    )

    story.append(Paragraph("By region", s["h2"]))
    _table(
        story,
        ["Region", "Documents"],
        [[r, str(c)] for r, c in stats["by_r"]],
        col_widths=[8 * cm, 9 * cm],
    )

    story.append(Paragraph("MENA sources (documents saved)", s["h2"]))
    _table(
        story,
        ["Source", "Count"],
        [[n, str(c)] for n, c in stats["mena_src"]],
        col_widths=[10 * cm, 7 * cm],
    )

    if stats.get("zones"):
        story.append(Paragraph("MENA zone tags", s["h2"]))
        _table(
            story,
            ["Zone", "Count"],
            [[z, str(c)] for z, c in stats["zones"]],
            col_widths=[8 * cm, 9 * cm],
        )

    story.append(PageBreak())

    # ── 7. Spiders ──────────────────────────────────────────────────
    story.append(Paragraph("7. Spider Inventory &amp; Celery Schedule", s["h1"]))
    _table(
        story,
        ["Spider", "Focus", "Beat (UTC)"],
        [
            ["uae_legislation", "UAE federal law portal", "06:00"],
            ["dfsa_rulebook", "DFSA DIFC rulebook", "06:15"],
            ["difc_laws", "DIFC laws & regulations", "06:30"],
            ["adgm_fsra", "ADGM legal framework / FSRA", "06:45"],
            ["sdaia_saudi", "Saudi PDPL / SDAIA", "07:00"],
            ["uae_ai_office", "UAE government AI policy", "07:15"],
            ["digital_dubai", "AI principles & governance", "07:30"],
            ["—", "retag_all_documents", "07:50"],
            ["eu_ai_act", "EU AI Act", "09:00"],
            ["federal_register", "US Federal Register", "09:30"],
            ["nist_airc", "NIST AI Resource Center", "10:00"],
            ["ico_uk", "UK ICO AI guidance", "10:30"],
            ["oecd_policy, uk_aisi", "OECD / UK AISI", "Manual"],
        ],
        col_widths=[4 * cm, 9 * cm, 3 * cm],
    )

    # ── 8. API ──────────────────────────────────────────────────────
    story.append(Paragraph("8. API Surface (v0.4.0)", s["h1"]))
    _table(
        story,
        ["Endpoint", "Purpose"],
        [
            ["GET /documents/", "List/filter: region, jurisdiction, zone, sector, risk, keyword"],
            ["GET /documents/{id}", "Single doc: dates, zones, impacts, digest"],
            ["GET /search/", "Semantic search (requires embeddings)"],
            ["GET /stats/", "Totals by region, jurisdiction, source"],
            ["GET /playbooks/", "Regulatory playbooks list"],
            ["GET /playbooks/exposure-packs/{id}", "Client exposure pack detail"],
            ["GET /playbooks/impacts/{doc_id}", "Playbook impacts per document"],
            ["POST /auth/login", "JWT authentication"],
            ["GET /user/feed", "Personalised relevance feed"],
            ["GET /health", "Health check"],
        ],
        col_widths=[6.5 * cm, 10.5 * cm],
    )
    story.append(PageBreak())

    # ── 9. Exposure packs & playbooks ───────────────────────────────
    story.append(Paragraph("9. Exposure Packs &amp; Playbooks", s["h1"]))
    _table(
        story,
        ["Pack ID", "Use case"],
        [
            ["dubai_hq", "Dubai HQ: GCC + EU + US + UK (recommended demo default)"],
            ["mena_only", "GCC-only footprint"],
            ["eu_exposure_only", "EU AI Act / GDPR extraterritorial focus"],
        ],
        col_widths=[4 * cm, 13 * cm],
    )
    story.append(Paragraph("Playbooks (rule-based YAML)", s["h2"]))
    _section(
        story,
        s,
        "",
        [
            "uae_mainland_general — UAE federal PDPL & AI Office",
            "difc_financial_services — DIFC / DFSA",
            "adgm_financial_services — ADGM / FSRA",
            "cbuae_banking_ai — UAE supervised financial institutions",
            "digital_dubai_tech — Dubai AI ethics & smart city",
            "sdaia_saudi — KSA PDPL & SDAIA",
            "eu_ai_act_exposure — EU extraterritorial",
            "us_federal_ai_exposure — US partner/parent exposure",
            "uk_ico_ai — UK ICO & data protection",
        ],
    )

    # ── 10. What works ──────────────────────────────────────────────
    story.append(Paragraph("10. What Works Well Today (Demo-Ready)", s["h1"]))
    _section(
        story,
        s,
        "",
        [
            "Policy feed with region, zone, exposure pack, risk, keyword filters",
            "US Federal Register with real publication dates and change flags",
            "Playbook impact badges (rule-based, no OpenAI required)",
            "Change tracking: new / updated / major revision + version archive",
            "Weekly PDF generation for dubai_hq exposure pack",
            "51 automated tests passing",
            "Docker Compose for local full stack",
            "Celery Beat schedule defined for daily ingestion",
        ],
    )

    story.append(PageBreak())

    # ── 11. Downfalls ───────────────────────────────────────────────
    story.append(Paragraph("11. Downfalls, Gaps &amp; Risks", s["h1"]))

    story.append(Paragraph("Data &amp; coverage", s["h2"]))
    _table(
        story,
        ["Issue", "Impact"],
        [
            ["~95% US corpus", "MENA demos look thin vs positioning"],
            ["MENA = mostly marketing pages", "Credibility gap for legal/compliance buyers"],
            ["Law spiders yield few new docs", "DFSA/ADGM/SDAIA/uaelegislation not saving much yet"],
            ["No PDF pipeline", "Binding instruments often PDF-only"],
            ["MENA publication dates sparse", "Sources omit dates in HTML"],
            ["Only ~40 docs embedded", "Semantic search mostly empty"],
            ["0 digests generated", "Needs OPENAI_API_KEY + batch run"],
        ],
        col_widths=[5.5 * cm, 11.5 * cm],
    )

    story.append(Paragraph("Product &amp; UX", s["h2"]))
    _table(
        story,
        ["Issue", "Impact"],
        [
            ["Streamlit ≠ production SaaS", "No multi-tenant UI, SSO, billing"],
            ["Search ignores sidebar filters", "User confusion"],
            ["No Arabic", "GCC enterprise expectation"],
            ["No acknowledge / audit trail", "Enterprise workflow missing"],
            ["PDF via shell script only", "Not one-click in dashboard"],
        ],
        col_widths=[5.5 * cm, 11.5 * cm],
    )

    story.append(Paragraph("Engineering &amp; ops", s["h2"]))
    _table(
        story,
        ["Issue", "Impact"],
        [
            ["Layer 2 + Phase 9 not on GitHub", "Team cannot reproduce latest easily"],
            ["No production deploy URL", "No shareable live demo"],
            ["Celery worker must be running", "Beat schedule inactive otherwise"],
            ["SDAIA/DFSA Cloudflare", "Bot blocking in production"],
            ["ML slow on CPU", "Batch only, not real-time"],
            ["No observability", "No Sentry/Prometheus/spider failure alerts"],
        ],
        col_widths=[5.5 * cm, 11.5 * cm],
    )

    story.append(PageBreak())

    # ── 12. Roadmap ─────────────────────────────────────────────────
    story.append(Paragraph("12. Recommended Roadmap", s["h1"]))

    story.append(Paragraph("Before Git push &amp; pilot", s["h2"]))
    _section(
        story,
        s,
        "",
        [
            "Commit + push Layer 2, dates, Phase 9",
            "Deploy API + dashboard (Railway/Render)",
            "Run OpenAI digests on top 50 high-risk / dubai_hq docs",
            "Embed full corpus for search demo",
            "Record 5-min Loom demo + README screenshots",
        ],
    )

    story.append(Paragraph("MENA credibility (highest product priority)", s["h2"]))
    _section(
        story,
        s,
        "",
        [
            "PDF ingestion pipeline (DFSA, ADGM, federal decrees)",
            "CBUAE spider for banking AI guidance",
            "Fix law spider selectors after live HTML inspection",
            "Manual seed of 10–20 canonical instruments (PDPL, DIFC DP Law)",
        ],
    )

    story.append(Paragraph("Layer 3 — sellable product", s["h2"]))
    _section(
        story,
        s,
        "",
        [
            "Acknowledge workflow (who reviewed what, audit export)",
            "Email/Slack alerts on high playbook impact + major changes",
            "B2B2B API keys per tenant + webhooks",
            "Bilingual digests (EN + AR)",
            "One-click weekly PDF from dashboard",
        ],
    )

    story.append(Paragraph("Engineering hardening", s["h2"]))
    _section(
        story,
        s,
        "",
        [
            "Spider success/failure ops dashboard",
            "Production UI (Next.js) when ready",
            "Fine-tuned MENA classifier",
            "Rate limiting, SSO, RBAC",
        ],
    )

    story.append(PageBreak())

    # ── 13. Role briefings ──────────────────────────────────────────
    story.append(Paragraph("13. Briefing Notes by Role", s["h1"]))

    story.append(Paragraph("Business development", s["h2"]))
    _section(
        story,
        s,
        "",
        [
            "Pitch: only AI policy monitor for Dubai HQ with DIFC/ADGM zones + EU+US packs",
            "Demo: Region All → dubai_hq → US doc with date → playbook impacts → weekly PDF",
            "Pilot target: DIFC/ADGM fintech compliance lead or consultancy",
            "Do not oversell: MENA law library thin; US change monitoring strongest",
            "Pricing: per-seat SaaS, per-exposure-pack API, or white-label",
        ],
    )

    story.append(Paragraph("Software engineers", s["h2"]))
    _section(
        story,
        s,
        "",
        [
            "Entry: ingestion/spiders/, api/routers/, dashboard/app.py, infra/celery_app.py",
            "Run: ./scripts/run_api.sh, run_dashboard.sh, run_tests.sh",
            "MENA: ./scripts/run_mena_spiders.sh",
            "Migrations: ingestion/migrations/002–010",
            "Large uncommitted diff vs origin/main — sync before collaborating",
        ],
    )

    story.append(Paragraph("Product / compliance advisors", s["h2"]))
    _section(
        story,
        s,
        "",
        [
            "Playbooks are YAML — editable without code (ingestion/playbooks/)",
            "dubai_hq intentionally includes EU + US, not EU-only",
            "Publication date ≠ ingest date on dashboard",
            "Digests optional — core monitoring works without OpenAI",
        ],
    )

    # ── 14. Competitive ─────────────────────────────────────────────
    story.append(Paragraph("14. Competitive Landscape", s["h1"]))
    _table(
        story,
        ["Competitor", "Strength", "PolicyPulse edge / gap"],
        [
            ["Verifli", "Global AI policy monitor", "No GCC zone/playbook layer — we differentiate"],
            ["GCC LexAI", "Legal search", "We do change monitoring + playbooks"],
            ["ALFABEN / OSSUS", "GCC governance, Arabic", "We are external policy + extraterritorial"],
            ["Generic RegTech", "Enterprise sales", "We are AI-policy-specific, MENA-first"],
        ],
        col_widths=[3.5 * cm, 5 * cm, 8.5 * cm],
    )

    # ── 15. Commands ────────────────────────────────────────────────
    story.append(Paragraph("15. Commands Cheat Sheet", s["h1"]))
    cmds = [
        "./scripts/run_api.sh          # API :8000",
        "./scripts/run_dashboard.sh    # Dashboard :8501",
        "./scripts/run_mena_spiders.sh # MENA law crawl + retag",
        "./scripts/run_tests.sh        # pytest (51 tests)",
        "./scripts/generate_weekly_brief.sh --exposure-pack dubai_hq --days 7",
        "python3 -m ingestion.retag_documents",
        "python3 -m ingestion.backfill_published_at",
        "python3 -m digests.run_digests --limit 50  # needs OPENAI_API_KEY",
        "docker compose up --build",
    ]
    for c in cmds:
        story.append(Paragraph(f"<font face='Courier' size='8'>{_esc(c)}</font>", s["body"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "<b>One-line status for leadership:</b> PolicyPulse AI is a working compliance "
            "intelligence prototype with strong US ingestion and differentiated MENA architecture "
            "(zones, playbooks, exposure packs), but MENA legal depth, production deployment, "
            "digests, and enterprise workflow features are needed before a paid pilot.",
            s["body"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            f"Document generated by PolicyPulse AI · {GENERATED} UTC · Not legal advice.",
            s["small"],
        )
    )

    doc.build(story)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate team handover PDF")
    parser.add_argument(
        "-o",
        "--output",
        default="docs/PolicyPulse_Team_Handover.pdf",
        help="Output PDF path",
    )
    args = parser.parse_args()
    stats = _fetch_live_stats()
    path = build_handover_pdf(Path(args.output), stats)
    print(f"Wrote handover PDF to {path}")


if __name__ == "__main__":
    main()
