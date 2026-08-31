from pydantic import BaseModel
from typing import List

class RiskExplanation(BaseModel):
    headline: str
    summary: str
    key_signals: List[str]
    observed_evidence: List[str]
    recommended_action: str
    uncertainty: str
