from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_check_endpoint():
    """Test health check endpoint returns expected response."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "FastAPI Demo API"
    assert data["version"] == "1.0.0"


def test_health_check_endpoint_returns_json():
    """Test health check endpoint returns JSON content type."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
