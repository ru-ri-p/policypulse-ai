# tests/test_playbooks_api.py
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_list_playbooks():
    resp = client.get("/playbooks/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5
    ids = {p["id"] for p in data}
    assert "difc_financial_services" in ids
    assert "us_federal_ai_exposure" in ids


def test_exposure_pack_dubai_hq():
    resp = client.get("/playbooks/exposure-packs/dubai_hq")
    assert resp.status_code == 200
    pack = resp.json()
    assert "US" in pack["jurisdictions"]
    assert "EU" in pack["jurisdictions"]
    assert "UAE" in pack["jurisdictions"]
