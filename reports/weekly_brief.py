#!/usr/bin/env python3
# reports/weekly_brief.py — generate weekly GCC/EU/US policy brief PDF
"""
Generate a branded weekly PDF of policy changes.

Example:
  python3 -m reports.weekly_brief --exposure-pack dubai_hq --days 7
  python3 -m reports.weekly_brief --region MENA --days 7 -o docs/briefs/week.pdf
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.db import run_query
from ingestion.playbooks.loader import get_exposure_pack

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError as exc:
    raise SystemExit("Install reportlab: pip install reportlab") from exc


def _fetch_documents(
    days: int,
    region: str | None,
    exposure_pack: str | None,
    limit: int = 30,
) -> list[dict]:
    where = ["scraped_at >= NOW() - make_interval(days => %s)"]
    params: list = [days]

    pack = None
    if exposure_pack:
        pack = get_exposure_pack(exposure_pack)
        if pack:
            jurs = pack.get("jurisdictions", [])
            if jurs:
                placeholders = ", ".join(["%s"] * len(jurs))
                where.append(f"jurisdiction IN ({placeholders})")
                params.extend(jurs)
    elif region:
        from ingestion.regions import JURISDICTION_TO_REGION

        jurs = [k for k, v in JURISDICTION_TO_REGION.items() if v == region.upper()]
        if jurs:
            placeholders = ", ".join(["%s"] * len(jurs))
            where.append(f"jurisdiction IN ({placeholders})")
            params.extend(jurs)

    params.append(limit)
    where_sql = " AND ".join(where)

    rows = run_query(
        f"""
        SELECT id, title, url, jurisdiction, zones, sectors,
               change_summary, change_percent, is_major_change,
               digest_what_changed, digest_who_affected, digest_what_to_do,
               digest_urgency, playbook_impacts, scraped_at
        FROM documents
        WHERE {where_sql}
        ORDER BY is_major_change DESC NULLS LAST,
                 change_percent DESC NULLS LAST,
                 scraped_at DESC
        LIMIT %s
        """,
        tuple(params),
        fetch=True,
    )

    docs = []
    for r in rows:
        impacts = r[13] or {}
        if isinstance(impacts, str):
            impacts = json.loads(impacts)
        high_impacts = [k for k, v in impacts.items() if v.get("level") == "high"]
        docs.append(
            {
                "id": r[0],
                "title": r[1],
                "url": r[2],
                "jurisdiction": r[3],
                "zones": r[4] or [],
                "sectors": r[5] or [],
                "change_summary": r[6],
                "change_percent": r[7],
                "is_major_change": r[8],
                "digest_what": r[9],
                "digest_who": r[10],
                "digest_todo": r[11],
                "digest_urgency": r[12],
                "high_playbooks": high_impacts,
                "scraped_at": r[14],
            }
        )
    return docs


def build_pdf(
    docs: list[dict],
    output_path: Path,
    title: str,
    subtitle: str,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BriefTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1a365d"),
    )
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("Small", parent=body, fontSize=9, textColor=colors.grey)

    story = [
        Paragraph(title, title_style),
        Paragraph(subtitle, small),
        Spacer(1, 0.5 * cm),
    ]

    if not docs:
        story.append(Paragraph("No documents matched this period and filters.", body))
    else:
        story.append(
            Paragraph(f"<b>{len(docs)}</b> policy items in this brief.", body)
        )
        story.append(Spacer(1, 0.3 * cm))

        for i, d in enumerate(docs, 1):
            zones = ", ".join(d["zones"]) or "—"
            sectors = ", ".join(d["sectors"]) or "—"
            change_flag = ""
            if d.get("is_major_change"):
                change_flag = f' <font color="red">[MAJOR CHANGE ~{d.get("change_percent")}%]</font>'

            story.append(
                Paragraph(
                    f'{i}. <b>{_escape(d["title"][:120])}</b>{change_flag}',
                    h2,
                )
            )
            meta = (
                f'<b>Jurisdiction:</b> {d.get("jurisdiction") or "?"} | '
                f'<b>Zones:</b> {zones} | <b>Sectors:</b> {sectors}'
            )
            story.append(Paragraph(meta, small))
            story.append(Paragraph(f'<a href="{d["url"]}">{d["url"][:90]}...</a>', small))

            if d.get("digest_what"):
                story.append(Paragraph(f"<b>What changed:</b> {_escape(d['digest_what'])}", body))
            elif d.get("change_summary"):
                story.append(
                    Paragraph(f"<b>Change:</b> {_escape(d['change_summary'][:400])}", body)
                )

            if d.get("digest_who"):
                story.append(Paragraph(f"<b>Who is affected:</b> {_escape(d['digest_who'])}", body))
            if d.get("digest_todo"):
                story.append(Paragraph(f"<b>What to do:</b> {_escape(d['digest_todo'])}", body))
            if d.get("digest_urgency"):
                story.append(Paragraph(f"<b>Urgency:</b> {d['digest_urgency']}", body))

            if d.get("high_playbooks"):
                story.append(
                    Paragraph(
                        f"<b>High-impact playbooks:</b> {', '.join(d['high_playbooks'])}",
                        small,
                    )
                )
            story.append(Spacer(1, 0.4 * cm))

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "Generated by PolicyPulse AI — official sources only. Not legal advice.",
            small,
        )
    )

    doc.build(story)
    return output_path


def _escape(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", " ")
    )


def main():
    parser = argparse.ArgumentParser(description="Generate weekly policy brief PDF")
    parser.add_argument("--days", type=int, default=7, help="Look back N days")
    parser.add_argument("--region", type=str, default=None, help="MENA, EU, US, UK")
    parser.add_argument(
        "--exposure-pack",
        type=str,
        default="dubai_hq",
        help="Exposure pack id (dubai_hq, mena_only, eu_exposure_only)",
    )
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("-o", "--output", type=str, default=None)
    args = parser.parse_args()

    pack = get_exposure_pack(args.exposure_pack) if args.exposure_pack else None
    docs = _fetch_documents(
        days=args.days,
        region=args.region,
        exposure_pack=args.exposure_pack if not args.region else None,
        limit=args.limit,
    )

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    default_name = f"policypulse_brief_{args.exposure_pack or args.region or 'all'}_{date_str}.pdf"
    output = Path(args.output or f"docs/briefs/{default_name}")

    brief_title = "PolicyPulse — Weekly Regulatory Brief"
    if pack:
        subtitle = f"{pack['name']} | Last {args.days} days | {date_str}"
    else:
        subtitle = f"Region: {args.region or 'All'} | Last {args.days} days | {date_str}"

    path = build_pdf(docs, output, brief_title, subtitle)
    print(f"Wrote {len(docs)} items to {path}")


if __name__ == "__main__":
    main()
