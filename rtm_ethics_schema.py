from typing import Any, List, Dict
from pydantic import BaseModel

class WhyNot(BaseModel):
    action: str
    reason: Any

class DecisionAudit(BaseModel):
    selected_action: str
    scores: Dict[str, float]
    future_risk_e: float
    mitigations: List[str]
    why_not_others: List[WhyNot] = []

class AbortPayload(BaseModel):
    ACTION_ABORTED: bool = True
    reason: str
    top_safer_options: List[Dict[str, Any]] = []
    missing_facts_suggestion: List[str] = []
