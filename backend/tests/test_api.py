import pytest
from fastapi.testclient import TestClient
import os
import json

from app.api.app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_customers"] > 0
    assert "LOW" in data["risk_distribution"]
    assert "HIGH" in data["risk_distribution"]
    assert data["customers_requiring_review"] >= 0

def test_risk_queue():
    response = client.get("/api/risk/customers?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] > 0
    item = data["items"][0]
    assert "customer_id" in item
    assert "risk_probability" in item
    assert "risk_level" in item
    assert "review_required" in item
    assert isinstance(item["primary_signals"], list)

def test_customer_investigation():
    response = client.get("/api/risk/customers/C_46046/investigation")
    assert response.status_code == 200
    data = response.json()
    assert data["customer"]["customer_id"] == "C_46046"
    assert "signals" in data
    assert "strengths" in data
    assert "multi_signal_connections" in data

def test_customer_graph_endpoint():
    response = client.get("/api/risk/customers/C_46046/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "C_46046"
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0
    assert data["displayed_nodes_count"] > 0
    assert data["total_connections_count"] >= data["displayed_nodes_count"]
    assert "prioritization_note" in data

def test_customer_explanation():
    response = client.get("/api/risk/customers/C_46046/explanation")
    assert response.status_code == 200
    data = response.json()
    assert "headline" in data
    assert "summary" in data
    assert "key_signals" in data
    assert "observed_evidence" in data
    assert "recommended_action" in data
    assert "uncertainty" in data

def test_demo_customers():
    response = client.get("/api/demo/customers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    cids = [d["customer_id"] for d in data]
    assert "C_46046" in cids
    assert "C_00003" in cids

def test_zero_ground_truth_leakage():
    """Validates that no ground-truth keys appear in API responses or code imports."""
    forbidden = ["is_abuse", "ring_id", "abuse_type", "ground_truth"]
    
    # 1. Test investigation endpoint payload
    resp = client.get("/api/risk/customers/C_46046/investigation")
    raw_str = resp.text
    for word in forbidden:
        assert f'"{word}"' not in raw_str, f"Leakage detected: '{word}' found in investigation API response."
        
    # 2. Test graph endpoint payload
    resp_graph = client.get("/api/risk/customers/C_46046/graph")
    raw_graph_str = resp_graph.text
    for word in forbidden:
        assert f'"{word}"' not in raw_graph_str, f"Leakage detected: '{word}' found in graph API response."
        
    # 3. Test explanation endpoint payload
    resp_exp = client.get("/api/risk/customers/C_46046/explanation")
    raw_exp_str = resp_exp.text
    for word in forbidden:
        assert f'"{word}"' not in raw_exp_str, f"Leakage detected: '{word}' found in explanation API response."
