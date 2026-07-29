from enum import Enum
from typing import Optional
from pydantic import BaseModel
from app.models.common import DerivationLabel, DomainType

class EdgeType(str, Enum):
    transferable_principle = "transferable_principle"
    functional_similarity = "functional_similarity"
    structural_analogy = "structural_analogy"
    visual_similarity = "visual_similarity"
    behavioral_analogy = "behavioral_analogy"

class GraphNode(BaseModel):
    id: str
    inspiration_id: str
    label: str
    domain: DomainType
    importance: float
    x: Optional[float] = None
    y: Optional[float] = None
    derivation: DerivationLabel = DerivationLabel.SYSTEM

class GraphEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float
    relationship_description: str
    transferable_insight: str
    evidence: list[str]
    derivation: DerivationLabel

class ReasoningGraph(BaseModel):
    id: str
    challenge_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
