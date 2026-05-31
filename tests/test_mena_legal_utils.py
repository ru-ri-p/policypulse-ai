# tests/test_mena_legal_utils.py
from ingestion.mena_legal_urls import is_law_focused_url, looks_like_legal_content


def test_dfsa_rulebook_url():
    assert is_law_focused_url(
        "https://www.dfsa.ae/what-we-do/legislation-and-rulebook/dfsa-rulebook-modules"
    )


def test_skips_difc_marketing():
    assert not is_law_focused_url("https://www.difc.ae/experience/dubai")


def test_uae_legislation_detail():
    assert is_law_focused_url("https://www.uaelegislation.gov.ae/en/legislations/1234")


def test_legal_content_signals():
    text = (
        "Article 5. The licensee shall comply with data protection requirements "
        "pursuant to this regulation on artificial intelligence systems."
    )
    assert looks_like_legal_content("PDPL Amendment", text)


def test_adgm_legal_framework():
    assert is_law_focused_url("https://www.adgm.com/legal-framework/legislation")
