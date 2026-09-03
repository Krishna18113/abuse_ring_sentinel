import io
import json
import pytest
from fastapi.testclient import TestClient
from app.api.app import app

client = TestClient(app)

def test_list_sample_datasets():
    """Verify curated sample datasets endpoint returns available demo batches."""
    resp = client.get("/api/analysis/sample-datasets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3
    dataset_ids = [d["dataset_id"] for d in data]
    assert "promo_ring_batch" in dataset_ids
    assert "organic_retail_batch" in dataset_ids
    assert "hostile_leakage_test" in dataset_ids

def test_upload_valid_csv_dataset():
    """Verify uploading a valid CSV merchant dataset produces structured summary and session."""
    csv_content = (
        "customer_id,transaction_id,amount,timestamp,device_id,ip_address,coupon_code\n"
        "C_TEST_1,TX_101,1200.0,2026-03-01 10:00:00,DEV_A,10.0.0.1,PROMO10\n"
        "C_TEST_2,TX_102,1500.0,2026-03-01 10:05:00,DEV_A,10.0.0.1,PROMO10\n"
        "C_TEST_3,TX_103,1100.0,2026-03-01 10:10:00,DEV_B,10.0.0.2,\n"
    )
    files = {"file": ("test_batch.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 200
    res = resp.json()
    assert res["valid"] is True
    assert res["file_format"] == "csv"
    assert res["summary"]["customer_count"] == 3
    assert res["summary"]["transaction_count"] == 3
    assert res["summary"]["unique_devices_count"] == 2
    assert res["summary"]["unique_coupons_count"] == 1
    assert res["summary"]["total_volume_inr"] == 3800.0
    assert len(res["preview_rows"]) == 3
    assert res["ready_for_graph_analysis"] is True
    assert "session_id" in res

def test_upload_valid_json_dataset():
    """Verify uploading a JSON array dataset validates successfully."""
    json_data = [
        {"customer_id": "M_1", "transaction_id": "T_1", "amount": 250.0, "timestamp": "2026-03-01 12:00:00", "device_id": "D1"},
        {"customer_id": "M_2", "transaction_id": "T_2", "amount": 750.0, "timestamp": "2026-03-01 12:30:00", "device_id": "D2"}
    ]
    files = {"file": ("test.json", io.BytesIO(json.dumps(json_data).encode("utf-8")), "application/json")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 200
    res = resp.json()
    assert res["valid"] is True
    assert res["file_format"] == "json"
    assert res["summary"]["customer_count"] == 2
    assert res["summary"]["total_volume_inr"] == 1000.0

def test_upload_valid_jsonl_dataset():
    """Verify uploading a JSONL dataset validates successfully."""
    lines = (
        '{"customer_id": "M_10", "transaction_id": "TX_10", "amount": 500.0, "timestamp": "2026-03-01 14:00:00"}\n'
        '{"customer_id": "M_20", "transaction_id": "TX_20", "amount": 600.0, "timestamp": "2026-03-01 14:15:00"}\n'
    )
    files = {"file": ("records.jsonl", io.BytesIO(lines.encode("utf-8")), "application/x-ndjson")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 200
    res = resp.json()
    assert res["valid"] is True
    assert res["file_format"] == "jsonl"
    assert res["summary"]["customer_count"] == 2

def test_ground_truth_rejection():
    """Verify security policy strictly rejects datasets with target labels (is_abuse, ring_id)."""
    hostile_csv = (
        "customer_id,transaction_id,amount,timestamp,device_id,is_abuse,ring_id\n"
        "M_BAD_1,TX_B1,500.0,2026-03-01 10:00:00,D_1,1,RING_99\n"
    )
    files = {"file": ("hostile.csv", io.BytesIO(hostile_csv.encode("utf-8")), "text/csv")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 200
    res = resp.json()
    assert res["valid"] is False
    assert res["ready_for_graph_analysis"] is False
    assert any("Security Policy Violation" in err for err in res["errors"])

def test_missing_mandatory_fields():
    """Verify dataset missing mandatory customer_id or amount fails validation."""
    invalid_csv = (
        "transaction_id,timestamp,device_id\n"
        "TX_INV_1,2026-03-01 10:00:00,DEV_X\n"
    )
    files = {"file": ("incomplete.csv", io.BytesIO(invalid_csv.encode("utf-8")), "text/csv")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 200
    res = resp.json()
    assert res["valid"] is False
    assert any("Missing mandatory schema fields" in err for err in res["errors"])

def test_session_retrieval():
    """Verify session metadata can be retrieved after valid upload."""
    csv_content = (
        "customer_id,transaction_id,amount,timestamp\n"
        "C_SESS_1,TX_S1,300.0,2026-03-01 11:00:00\n"
    )
    files = {"file": ("sess.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    upload_resp = client.post("/api/analysis/upload", files=files)
    session_id = upload_resp.json()["session_id"]

    get_resp = client.get(f"/api/analysis/sessions/{session_id}")
    assert get_resp.status_code == 200
    sess_data = get_resp.json()
    assert sess_data["session_id"] == session_id
    assert sess_data["record_count"] == 1

def test_seeded_demo_customers_unaffected():
    """Verify that seeded demo customers (C_00003, C_46046) remain deterministic and unaffected."""
    resp_low = client.get("/api/risk/customers/C_00003")
    assert resp_low.status_code == 200
    assert resp_low.json()["risk_level"] == "LOW"

    resp_high = client.get("/api/risk/customers/C_46046")
    assert resp_high.status_code == 200
    assert resp_high.json()["risk_level"] == "HIGH"

def test_session_graph_analysis_promo_ring():
    """Verify graph analysis detects abuse clusters and high risk in Batch A promo ring."""
    from app.analysis.samples import SAMPLE_PROMO_RING_CSV
    files = {"file": ("promo.csv", io.BytesIO(SAMPLE_PROMO_RING_CSV.encode("utf-8")), "text/csv")}
    upload_resp = client.post("/api/analysis/upload", files=files)
    session_id = upload_resp.json()["session_id"]

    # Run analysis
    analysis_resp = client.post(f"/api/analysis/sessions/{session_id}/analyze")
    assert analysis_resp.status_code == 200
    report = analysis_resp.json()
    assert report["total_customers"] == 10
    assert report["high_risk_customers"] >= 5
    assert report["reviews_required"] >= 5
    assert len(report["detected_clusters"]) >= 1
    assert "D_RING_99" in report["detected_clusters"][0]["shared_devices"]

def test_session_customer_investigation():
    """Verify inspecting an uploaded customer returns full evidence graph and explanation."""
    from app.analysis.samples import SAMPLE_PROMO_RING_CSV
    files = {"file": ("promo.csv", io.BytesIO(SAMPLE_PROMO_RING_CSV.encode("utf-8")), "text/csv")}
    upload_resp = client.post("/api/analysis/upload", files=files)
    session_id = upload_resp.json()["session_id"]

    # Run analysis then investigate customer M_1001
    client.post(f"/api/analysis/sessions/{session_id}/analyze")
    inv_resp = client.get(f"/api/analysis/sessions/{session_id}/investigate/M_1001")
    assert inv_resp.status_code == 200
    inv = inv_resp.json()
    assert inv["customer_id"] == "M_1001"
    assert inv["risk_level"] == "HIGH"
    assert inv["review_required"] is True
    assert len(inv["graph"]["nodes"]) >= 3
    assert len(inv["graph"]["edges"]) >= 2
    assert "explanation" in inv
    assert "summary" in inv["explanation"]

