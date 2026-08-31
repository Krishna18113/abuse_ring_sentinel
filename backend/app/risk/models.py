from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# --- Sub-models for behavioral features ---
class CustomerInfo(BaseModel):
    customer_id: str
    account_created_at: Optional[str] = "Active"
    account_age_days: Optional[float] = 120.0

class RiskInfo(BaseModel):
    risk_probability: float
    risk_level: str
    review_required: bool

class BehaviorInfo(BaseModel):
    transaction_count: int
    total_transaction_amount: Optional[float] = 0.0
    average_transaction_amount: Optional[float] = 0.0
    median_transaction_amount: Optional[float] = 0.0
    coupon_usage_count: int
    unique_coupons_used: Optional[int] = 0
    referrals_made: int
    was_referred: Optional[bool] = False
    active_days: Optional[int] = 1
    night_transaction_ratio: Optional[float] = 0.0

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
