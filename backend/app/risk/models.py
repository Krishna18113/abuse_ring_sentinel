from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# --- Sub-models for behavioral features ---
class CustomerInfo(BaseModel):
    customer_id: str

class RiskInfo(BaseModel):
    risk_probability: float
    risk_level: str
    review_required: bool

class BehaviorInfo(BaseModel):
    transaction_count: int
    coupon_usage_count: int
    referrals_made: int

# --- Sub-models for signals ---
class SharedDeviceDetail(BaseModel):
    device_id: str
    customer_count: int
    connected_customers: List[str]
    transaction_count: int

class SharedIPDetail(BaseModel):
    ip_address: str
    customer_count: int
    connected_customers: List[str]
    transaction_count: int

class CouponCoordinationDetail(BaseModel):
    coupon_id: str
    customer_count: int
    connected_customers: List[str]
    shared_device_count: int
    shared_ip_count: int

class ReferralDetail(BaseModel):
    referrer_id: Optional[str]
    referred_ids: List[str]
    referral_in_degree: int
    referral_out_degree: int
    referral_component_size: int

class TemporalTxDetail(BaseModel):
    customer_id: str
    transaction_id: str
    timestamp: str

class TemporalClusterDetail(BaseModel):
    time_window_seconds: int
    customer_count: int
    transaction_count: int
    total_amount: float
    transactions: List[TemporalTxDetail]

# --- Sub-models for multi-signal and strength summaries ---
class MultiSignalDetail(BaseModel):
    connected_customer: str
    signals: List[str]
    signal_count: int

class SignalStrengthDetail(BaseModel):
    detected: bool
    strength: str  # NONE, LOW, MEDIUM, HIGH
    details: Dict[str, Any]

class EvidenceSummary(BaseModel):
    signal_count: int
    connected_customer_count: int
    temporal_cluster_count: int

# --- Complete Evidence Package ---
class EvidencePackage(BaseModel):
    customer: CustomerInfo
    risk: RiskInfo
    behavior: BehaviorInfo
    signals: Dict[str, Any]
    multi_signal_connections: List[MultiSignalDetail]
    summary: EvidenceSummary
    strengths: Dict[str, SignalStrengthDetail]
