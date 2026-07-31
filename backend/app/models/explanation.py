from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
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

class ReasoningPathNode(BaseModel):
    id: str
    title: str

class ReasoningPathEdge(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    relationship_label: str
    relationship_description: str = ""
    derivation: str = "UNKNOWN"
    confidence: Optional[float] = None

class ReasoningPath(BaseModel):
    """Ordered directed path that supports an explanation conclusion."""
    nodes: list[ReasoningPathNode] = Field(default_factory=list)
    edges: list[ReasoningPathEdge] = Field(default_factory=list)
    prose: Optional[str] = None

class ExplanationResponse(BaseModel):
    request: ExplanationRequest
    chain: ExplanationChain
    summary: str
    # Structured graph paths reused from relationship_analysis (never fabricated).
    paths: list[ReasoningPath] = Field(default_factory=list)
