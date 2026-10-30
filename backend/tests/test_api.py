from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "options-pricing-backend"
    assert "timestamp" in data

def test_prometheus_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    # Verify standard and custom Prometheus metrics are present
    assert "http_requests_total" in text
    assert "monte_carlo_simulations_total" in text
    assert "monte_carlo_simulation_duration_seconds" in text
    assert "monte_carlo_active_websockets" in text

def test_simulation_endpoint_records_metrics():
    payload = {
        "spot": 100.0,
        "strike": 100.0,
        "vol": 0.2,
        "rate": 0.05,
        "days": 30,
        "sims": 500,
        "steps": 50,
        "option_type": "call",
        "style": "european"
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "price" in data
    assert "greeks" in data
    assert data["price"] > 0

    # Scrape metrics again to ensure simulation count was incremented
    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    assert 'monte_carlo_simulations_total{option_type="call",status="success",style="european"}' in metrics_res.text
