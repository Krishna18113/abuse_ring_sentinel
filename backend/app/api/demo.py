"""
Pre-configured seed demo customers selected strictly from model evaluation and evidence engine outputs.
"""
from typing import List
from app.api.schemas import DemoCustomer

DEMO_CUSTOMERS: List[DemoCustomer] = [
    DemoCustomer(
        customer_id="C_46046",
        category="High Risk Abuse Ring",
        description="Shares hardware with 9 accounts, 5 multi-signal connections, and 60s transaction coordination.",
        risk_probability=0.9906,
        risk_level="HIGH",
        review_required=True
    ),
    DemoCustomer(
        customer_id="C_00003",
        category="Low Risk Legitimate Customer",
        description="Normal longitudinal activity, isolated device and IP infrastructure, clean referral history.",
        risk_probability=0.0002,
        risk_level="LOW",
        review_required=False
    )
]
