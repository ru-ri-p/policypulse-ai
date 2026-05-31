# tests/test_api.py
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _sample_document_row():
    now = datetime(2026, 5, 20, 12, 0, 0)
    return (
        1,
        "EU AI Act — Title",
        "https://example.com/doc",
        "EU",
        "binding regulation",
        "high",
        "A short policy summary for testing.",
        5.0,
        False,
        None,
        now,
        now,
        None,
        0,
        [],
        ["financial_services"],
        {"eu_ai_act_exposure": {"level": "high", "name": "EU AI Act", "summary": "EU scope"}},
        None,
        None,
        None,
        None,
        None,
        None,
    )


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


@patch("api.routers.documents.run_query")
def test_list_documents(mock_run_query):
    mock_run_query.return_value = [_sample_document_row()]
    resp = client.get("/documents/", params={"limit": 5})
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["jurisdiction"] == "EU"
    assert docs[0]["risk_level"] == "high"
    assert "eu_ai_act_exposure" in docs[0]["playbook_impacts"]
    assert docs[0]["update_status"] == "updated"
    assert docs[0]["first_scraped_at"] is not None


@patch("api.routers.documents.run_query")
def test_get_document_by_id(mock_run_query):
    mock_run_query.return_value = [_sample_document_row()]
    resp = client.get("/documents/1")
    assert resp.status_code == 200
    assert resp.json()["title"].startswith("EU AI Act")


@patch("api.routers.documents.run_query")
def test_get_document_not_found(mock_run_query):
    mock_run_query.return_value = []
    resp = client.get("/documents/99999")
    assert resp.status_code == 404


@patch("api.routers.stats.run_query")
def test_stats_endpoint(mock_run_query):
    mock_run_query.side_effect = [
        [(1151,)],
        [("US", 900), ("EU", 200), ("UK", 51)],
        [("US Federal Register", 900), ("EU AI Act", 200)],
        [(42,)],
    ]
    resp = client.get("/stats/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1151
    assert data["high_risk"] == 42
    assert "by_jurisdiction" in data


@patch("ml_pipeline.search.semantic_search")
def test_search_endpoint(mock_search):
    mock_search.return_value = [(1, "Facial recognition rule", "EU", 0.91)]
    resp = client.get("/search/", params={"q": "facial recognition"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["similarity"] == 0.91


def test_search_requires_query():
    resp = client.get("/search/")
    assert resp.status_code == 422
