from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import DerivationLabel, DomainType


class EdgeType(str, Enum):
    """Internal normalized relationship category."""

    # Legacy curated / analogy categories (preserved for existing seed data)
    transferable_principle = "transferable_principle"
    functional_similarity = "functional_similarity"
    structural_analogy = "structural_analogy"
    visual_similarity = "visual_similarity"
    behavioral_analogy = "behavioral_analogy"
    # Semantic relationship categories
    inspired_by = "inspired_by"
    extension = "extension"
    refinement = "refinement"
    contrast = "contrast"
    support = "support"
    dependency = "dependency"
    usage = "usage"
    similarity = "similarity"
    opposition = "opposition"
    evolution = "evolution"
    combination = "combination"
    reference = "reference"


# Default human-readable labels for each internal edge_type
EDGE_TYPE_DEFAULT_LABELS: dict[EdgeType, str] = {
    EdgeType.transferable_principle: "Transfers principle from",
    EdgeType.functional_similarity: "Similar to",
    EdgeType.structural_analogy: "Structurally analogous to",
    EdgeType.visual_similarity: "Visually similar to",
    EdgeType.behavioral_analogy: "Behaviorally analogous to",
    EdgeType.inspired_by: "Inspired by",
    EdgeType.extension: "Builds on",
    EdgeType.refinement: "Refines",
    EdgeType.contrast: "Contrasts with",
    EdgeType.support: "Supports",
    EdgeType.dependency: "Depends on",
    EdgeType.usage: "Uses",
    EdgeType.similarity: "Similar to",
    EdgeType.opposition: "Opposes",
    EdgeType.evolution: "Evolves into",
    EdgeType.combination: "Combines with",
    EdgeType.reference: "References",
}


# UI presets: user-facing label → internal edge_type
RELATIONSHIP_PRESETS: list[dict[str, str]] = [
    {"label": "Inspired by", "edge_type": EdgeType.inspired_by.value},
    {"label": "Builds on", "edge_type": EdgeType.extension.value},
    {"label": "Refines", "edge_type": EdgeType.refinement.value},
    {"label": "Contrasts with", "edge_type": EdgeType.contrast.value},
    {"label": "Supports", "edge_type": EdgeType.support.value},
    {"label": "Depends on", "edge_type": EdgeType.dependency.value},
    {"label": "Uses", "edge_type": EdgeType.usage.value},
    {"label": "Similar to", "edge_type": EdgeType.similarity.value},
    {"label": "Related to", "edge_type": EdgeType.similarity.value},
    {"label": "Opposes", "edge_type": EdgeType.opposition.value},
    {"label": "Evolves into", "edge_type": EdgeType.evolution.value},
    {"label": "Combines with", "edge_type": EdgeType.combination.value},
    {"label": "References", "edge_type": EdgeType.reference.value},
]


def default_relationship_label(edge_type: EdgeType) -> str:
    return EDGE_TYPE_DEFAULT_LABELS.get(edge_type, "Related to")


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
    weight: float = 0.5
    relationship_label: str = "Related to"
    relationship_description: str = ""
    transferable_insight: str = ""
    evidence: list[str] = Field(default_factory=list)
    derivation: DerivationLabel = DerivationLabel.MANUAL
    confidence: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ReasoningGraph(BaseModel):
    id: str
    challenge_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
