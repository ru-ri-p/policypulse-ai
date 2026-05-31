# tests/test_tagging.py
from ingestion.tagging import infer_zones, tag_document, compute_playbook_impacts


def test_infer_difc_from_url():
    zones = infer_zones(
        "https://www.difc.ae/business/laws",
        "DIFC Data & AI Regulation",
    )
    assert "DIFC" in zones


def test_tag_uae_mainland_document():
    zones, sectors, impacts = tag_document(
        title="Artificial intelligence in government policies",
        url="https://u.ae/en/about-the-uae/digital-uae/artificial-intelligence/artificial-intelligence-in-government-policies",
        content="UAE government AI strategy and PDPL references for federal entities.",
        source_name="UAE AI Office",
        jurisdiction="UAE",
    )
    assert "MAINLAND" in zones
    assert "uae_mainland_general" in impacts


def test_tag_us_federal_register():
    zones, sectors, impacts = tag_document(
        title="Artificial Intelligence Executive Order",
        url="https://www.federalregister.gov/documents/2024/ai-rule",
        content="Federal register notice on artificial intelligence policy for agencies.",
        source_name="US Federal Register - AI",
        jurisdiction="US",
    )
    assert "us_federal_ai_exposure" in impacts
    assert impacts["us_federal_ai_exposure"]["level"] in ("high", "medium", "low")


def test_tag_eu_ai_act():
    zones, sectors, impacts = tag_document(
        title="EU AI Act high-risk systems",
        url="https://artificialintelligenceact.eu/the-act/",
        content="European Union AI Act requirements for high-risk AI systems.",
        source_name="EU AI Act Monitor",
        jurisdiction="EU",
    )
    assert "eu_ai_act_exposure" in impacts


def test_dubai_hq_exposure_pack_includes_us_and_eu_playbooks():
    from ingestion.playbooks.loader import get_exposure_pack

    pack = get_exposure_pack("dubai_hq")
    assert "eu_ai_act_exposure" in pack["default_playbooks"]
    assert "us_federal_ai_exposure" in pack["default_playbooks"]
    assert "difc_financial_services" in pack["default_playbooks"]
