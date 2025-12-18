from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "OPERATIONAL"

def test_audit_flow():
    payload = {"url": "https://www.imot.bg/pcgi/imot.cgi?act=5&adv=mock123"}
    response = client.post("/audit", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUEUED"
    assert "listing_id" in data
