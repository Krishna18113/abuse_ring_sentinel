from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

class DatasetSummary(BaseModel):
    customer_count: int = 0
    transaction_count: int = 0
    unique_devices_count: int = 0
    unique_ips_count: int = 0
    unique_coupons_count: int = 0
    referrals_count: int = 0
    total_volume_inr: float = 0.0

class SchemaAnalysis(BaseModel):
    detected_fields: List[str] = []
    missing_optional_fields: List[str] = []
    unrecognized_fields: List[str] = []

class DatasetValidationResult(BaseModel):
    session_id: str
    filename: str
    file_format: str
    valid: bool
    summary: DatasetSummary
    schema_analysis: SchemaAnalysis
    errors: List[str] = []
    warnings: List[str] = []
    preview_rows: List[Dict[str, Any]] = []
    ready_for_graph_analysis: bool
    architectural_boundary_notes: str

class ValidatePayloadRequest(BaseModel):
    filename: Optional[str] = "payload.json"
    records: List[Dict[str, Any]]

    @model_validator(mode="before")
    @classmethod
    def check_forbidden_anti_leakage_fields(cls, data):
        if isinstance(data, dict):
            records = data.get("records", [])
            forbidden_keys = {"is_abuse", "ring_id", "abuse_type", "split", "label", "ground_truth"}
            for idx, r in enumerate(records[:100]):
                if isinstance(r, dict):
                    found = [k for k in r.keys() if k in forbidden_keys]
                    if found:
                        raise ValueError(f"Forbidden ground-truth fields detected in record #{idx + 1}: {found}. Upload rejected by security policy.")
        return data

class SampleDatasetItem(BaseModel):
    dataset_id: str
    name: str
    description: str
    file_format: str
    record_count: int
    content: str

class SessionCustomerRisk(BaseModel):
    customer_id: str
    risk_probability: float
    risk_level: str
    review_required: bool
    primary_flag_reason: str
    transaction_count: int
    total_amount: float
    shared_device_count: int
    shared_ip_count: int
    shared_coupon_count: int
    multi_signal_connections_count: int
    connected_customer_ids: List[str] = []
    detected_signals: List[str] = []

class SessionClusterInfo(BaseModel):
    cluster_id: str
    customer_count: int
    risk_level: str
    customer_ids: List[str]
    shared_devices: List[str] = []
    shared_ips: List[str] = []
    shared_coupons: List[str] = []
    summary: str

class SessionInvestigationResponse(BaseModel):
    customer_id: str
    risk_probability: float
    risk_level: str
    review_required: bool
    primary_reason: str
    explanation: Dict[str, Any]
    graph: Dict[str, Any]

class SessionAnalysisReport(BaseModel):
    session_id: str
    analyzed_at: str
    total_customers: int
    high_risk_customers: int
    reviews_required: int
    detected_clusters: List[SessionClusterInfo] = []
    customer_risks: List[SessionCustomerRisk] = []
    boundary_note: str

