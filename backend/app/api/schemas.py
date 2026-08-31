from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DashboardSummaryResponse(BaseModel):
    total_customers: int
    customers_requiring_review: int
    high_risk_customers: int
    medium_risk_customers: int
    low_risk_customers: int
    total_transactions: int
    high_risk_percentage: float
    risk_distribution: Dict[str, int]
    investigation_statistics: Dict[str, Any]

class RiskQueueItem(BaseModel):
    customer_id: str
    risk_probability: float
    risk_level: str
    review_required: bool
    primary_signals: List[str]

class RiskQueueResponse(BaseModel):
    items: List[RiskQueueItem]
    total: int
    limit: int
    offset: int

class GraphNode(BaseModel):
    id: str
    type: str # "customer", "device", "ip", "coupon"
    data: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    label: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class GraphResponse(BaseModel):
    customer_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_connections_count: int
    displayed_nodes_count: int
    prioritization_note: str

class DemoCustomer(BaseModel):
    customer_id: str
    category: str
    description: str
    risk_probability: float
    risk_level: str
    review_required: bool
