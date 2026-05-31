# tests/test_date_extract.py
from datetime import datetime

from ingestion.date_extract import (
    extract_from_url,
    infer_document_published_at,
    parse_published_value,
)


def test_federal_register_url_date():
    dt = extract_from_url(
        "https://www.federalregister.gov/documents/2023/10/30/2023-23758/foo"
    )
    assert dt == datetime(2023, 10, 30)


def test_parse_api_publication_date():
    assert parse_published_value("2024-03-13") == datetime(2024, 3, 13)


def test_infer_from_title_iso():
    dt = infer_document_published_at(
        "AI Act guidance 2024-06-12",
        "https://example.com/page",
        "",
    )
    assert dt == datetime(2024, 6, 12)
