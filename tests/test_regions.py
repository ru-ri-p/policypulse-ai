# tests/test_regions.py
from ingestion.regions import get_region, JURISDICTION_TO_REGION, REGIONS


def test_uae_maps_to_mena():
    assert get_region("UAE") == "MENA"


def test_sa_maps_to_mena():
    assert get_region("SA") == "MENA"


def test_qa_maps_to_mena():
    assert get_region("QA") == "MENA"


def test_eu_maps_to_eu():
    assert get_region("EU") == "EU"


def test_us_maps_to_us():
    assert get_region("US") == "US"


def test_uk_maps_to_uk():
    assert get_region("UK") == "UK"


def test_oecd_maps_to_eu():
    assert get_region("OECD") == "EU"


def test_unknown_jurisdiction_returns_other():
    assert get_region("XX") == "OTHER"
    assert get_region(None) == "OTHER"
    assert get_region("") == "OTHER"


def test_case_insensitive():
    assert get_region("uae") == "MENA"
    assert get_region("Uae") == "MENA"


def test_regions_list_complete():
    assert "MENA" in REGIONS
    assert "EU" in REGIONS
    assert "US" in REGIONS
    assert "UK" in REGIONS


def test_all_jurisdictions_have_region():
    for j in JURISDICTION_TO_REGION:
        assert JURISDICTION_TO_REGION[j] in REGIONS
