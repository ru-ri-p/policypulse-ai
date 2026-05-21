# tests/test_cleaner.py
from ingestion.cleaner import clean_text, extract_date


def test_clean_text_removes_urls():
    result = clean_text("Check https://example.com for details")
    assert "https://example.com" not in result


def test_clean_text_strips_whitespace():
    result = clean_text("  hello   world  ")
    assert result == "hello world"


def test_clean_text_handles_empty():
    assert clean_text("") == ""


def test_clean_text_unescapes_html():
    result = clean_text("EU &amp; AI Act")
    assert "&amp;" not in result
    assert "EU" in result


def test_extract_date_iso_format():
    result = extract_date("2024-03-15")
    assert result is not None
    assert result.year == 2024
    assert result.month == 3


def test_extract_date_uk_format():
    result = extract_date("15/03/2024")
    assert result is not None
    assert result.day == 15


def test_extract_date_invalid_returns_none():
    assert extract_date("not-a-date") is None
    assert extract_date("") is None
