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
