from typing import Any, Dict
from pydantic import BaseModel
from app.models.common import DerivationLabel

class ReasoningStep(BaseModel):
    step_number: int
    description: str
    derivation: DerivationLabel

class ExplanationChain(BaseModel):
    retrieved_knowledge: list[ReasoningStep]
    deterministic_reasoning: list[ReasoningStep]
    ai_interpretation: list[ReasoningStep]

class ExplanationRequest(BaseModel):
    target_type: str
    target_id: str
    context: Dict[str, Any]

class ExplanationResponse(BaseModel):
    request: ExplanationRequest
    chain: ExplanationChain
    summary: str
