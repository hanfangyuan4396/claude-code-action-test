from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_endpoint_integration():
    """Integration test for health endpoint through the full app."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure matches expected health check format
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert data["status"] == "healthy"
    assert data["service"] == "FastAPI Demo API"
    assert data["version"] == "1.0.0"
    assert response.headers["content-type"] == "application/json"

    # Verify direct access without prefix fails (confirms proper API prefix routing)
    response_direct = client.get("/health")
    assert response_direct.status_code == 404
