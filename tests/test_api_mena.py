# tests/test_api_mena.py — Phase 8 API tests for region filtering
from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _uae_document_row():
    added = datetime(2026, 5, 1, 9, 0, 0)
    return (
        101,
        "UAE AI Governance Framework",
        "https://u.ae/en/about-the-uae/ai",
        "UAE",
        "policy guidance",
        "medium",
        "Guidance for government entities adopting AI.",
        None,
        False,
        None,
        added,
        added,
        None,
        0,
        ["MAINLAND"],
        ["government"],
        {"uae_mainland_general": {"level": "high", "name": "UAE Mainland", "summary": ""}},
        None,
        None,
        None,
        None,
        None,
        None,
    )


def _sa_document_row():
    added = datetime(2026, 5, 2, 9, 0, 0)
    return (
        102,
        "Saudi PDPL Guidelines for AI",
        "https://sdaia.gov.sa/en/pdpl",
        "SA",
        "binding regulation",
        "high",
        "Personal data protection requirements for AI systems.",
        None,
        False,
        None,
        added,
        added,
        None,
        0,
        ["MAINLAND"],
        ["general"],
        {"sdaia_saudi": {"level": "high", "name": "SDAIA", "summary": ""}},
        None,
        None,
        None,
        None,
        None,
        None,
    )


@patch("api.routers.documents.run_query")
def test_filter_by_region_mena(mock_run_query):
    mock_run_query.return_value = [_uae_document_row(), _sa_document_row()]
    resp = client.get("/documents/", params={"region": "MENA", "limit": 10})
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 2
    assert docs[0]["jurisdiction"] == "UAE"
    assert docs[1]["jurisdiction"] == "SA"


@patch("api.routers.documents.run_query")
def test_filter_by_jurisdiction_uae(mock_run_query):
    mock_run_query.return_value = [_uae_document_row()]
    resp = client.get("/documents/", params={"jurisdiction": "UAE"})
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["title"] == "UAE AI Governance Framework"


@patch("api.routers.stats.run_query")
def test_stats_includes_region(mock_run_query):
    mock_run_query.side_effect = [
        [(50,)],
        [("UAE", 20), ("SA", 10), ("EU", 15), ("US", 5)],
        [("UAE AI Office", 20), ("Saudi SDAIA", 10)],
        [(8,)],
    ]
    resp = client.get("/stats/")
    assert resp.status_code == 200
    data = resp.json()
    assert "by_region" in data
    assert data["by_region"]["MENA"] == 30
    assert data["by_region"]["EU"] == 15
