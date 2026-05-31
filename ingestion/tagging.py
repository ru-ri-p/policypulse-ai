# ingestion/tagging.py — rule-based zone, sector, and playbook impact tagging
from __future__ import annotations

from ingestion.playbooks.loader import get_playbooks, load_playbooks_config


def _text_blob(title: str, url: str, content: str, source_name: str) -> str:
    return f"{title} {url} {content[:2000]} {source_name}".lower()


def infer_zones(
    url: str,
    source_name: str,
    title: str = "",
    content: str = "",
) -> list[str]:
    """Infer regulatory zones from URL, source, and text."""
    blob = _text_blob(title, url, content, source_name)
    zones: set[str] = set()

    hints = load_playbooks_config().get("source_zone_hints", {})
    if source_name in hints:
        for z in hints[source_name]:
            if z:
                zones.add(z)

    if "difc" in blob or "dfsa" in blob:
        zones.add("DIFC")
    if "adgm" in blob or "fsra.adgm" in blob or "adgm.com" in url:
        zones.add("ADGM")
    if "dmcc.ae" in url:
        zones.add("DMCC")

    # Federal / emirate portals without FZ markers → mainland
    if any(
        p in url
        for p in ("u.ae", "uaelegislation", "digitaldubai", "ai.gov", "centralbank.ae")
    ):
        zones.add("MAINLAND")
    if "sdaia.gov" in url or "ndmo.gov" in url:
        zones.add("MAINLAND")

    return sorted(zones)


def infer_sectors(
    url: str,
    source_name: str,
    title: str = "",
    content: str = "",
) -> list[str]:
    """Infer industry sectors from source and keywords."""
    blob = _text_blob(title, url, content, source_name)
    sectors: set[str] = set()

    sector_rules = [
        ("financial_services", ["bank", "insurance", "fintech", "dfsa", "fsra", "cbuae", "payment", "capital market"]),
        ("banking", ["cbuae", "central bank", "banking", "lending"]),
        ("technology", ["technology", "digital", "cloud", "software", "ai lab", "innovation"]),
        ("health", ["health", "dha", "doh", "medical", "clinical"]),
        ("government", ["government", "federal", "ministry", "public sector", "u.ae"]),
        ("fintech", ["fintech", "virtual asset", "crypto", "blockchain", "web3"]),
    ]

    for sector, keywords in sector_rules:
        if any(kw in blob for kw in keywords):
            sectors.add(sector)

    if not sectors:
        sectors.add("general")

    return sorted(sectors)


def _playbook_match_score(playbook: dict, blob: str, url: str, jurisdiction: str | None) -> int:
    """Higher score = stronger match (0 = no match)."""
    score = 0
    jur = (jurisdiction or "").upper()
    pb_jurs = [j.upper() for j in playbook.get("jurisdictions", [])]

    if pb_jurs and jur and jur not in pb_jurs:
        return 0

    if pb_jurs and jur in pb_jurs:
        score += 2

    for pattern in playbook.get("url_patterns", []):
        if pattern.lower() in url.lower() or pattern.lower() in blob:
            score += 3
            break

    for kw in playbook.get("title_keywords", []):
        if kw.lower() in blob:
            score += 1

    return score


def compute_playbook_impacts(
    title: str,
    url: str,
    content: str,
    source_name: str,
    jurisdiction: str | None,
    zones: list[str],
    sectors: list[str],
) -> dict[str, dict]:
    """
    Returns { playbook_id: { level, summary } } for all playbooks with non-none impact.
    level: high | medium | low
    """
    blob = _text_blob(title, url, content, source_name)
    zone_set = set(zones)
    sector_set = set(sectors)
    impacts: dict[str, dict] = {}

    for pb in get_playbooks():
        score = _playbook_match_score(pb, blob, url, jurisdiction)
        if score == 0:
            continue

        pb_zones = set(pb.get("zones", []))
        pb_sectors = set(pb.get("sectors", []))

        zone_overlap = bool(pb_zones and zone_set & pb_zones)
        sector_overlap = bool(pb_sectors and sector_set & pb_sectors)

        if score >= 4 and (zone_overlap or sector_overlap or not pb_zones):
            level = "high"
        elif score >= 2:
            level = "medium"
        else:
            level = "low"

        impacts[pb["id"]] = {
            "level": level,
            "summary": (pb.get("impact_summary") or "").strip(),
            "name": pb.get("name", pb["id"]),
        }

    return impacts


def tag_document(
    title: str,
    url: str,
    content: str,
    source_name: str,
    jurisdiction: str | None,
) -> tuple[list[str], list[str], dict]:
    """Full tagging pass for one document."""
    zones = infer_zones(url, source_name, title, content)
    sectors = infer_sectors(url, source_name, title, content)
    impacts = compute_playbook_impacts(
        title, url, content, source_name, jurisdiction, zones, sectors
    )
    return zones, sectors, impacts


def impacts_for_client_playbooks(
    impacts: dict,
    playbook_ids: list[str],
) -> dict[str, dict]:
    """Filter document impacts to a client's subscribed playbooks."""
    return {pid: impacts[pid] for pid in playbook_ids if pid in impacts}
