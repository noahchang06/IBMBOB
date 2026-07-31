"""Deterministic edge helpers for semantic relationships."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from app.models.common import DerivationLabel
from app.models.graph import (
    EdgeType,
    GraphEdge,
    default_relationship_label,
)
from app.models.inspiration import Inspiration


class AutoConnectContext(str, Enum):
    """Why an automatic edge was attached to a peer."""

    selected = "selected"
    initiation = "initiation"
    fallback = "fallback"


def to_inspiration_id(node_or_inspiration_id: str) -> str:
    """Accept either a graph node id (`n-…`) or a raw inspiration id."""
    if node_or_inspiration_id.startswith("n-"):
        return node_or_inspiration_id[2:]
    return node_or_inspiration_id


def build_related_edge(
    challenge_id: str,
    source_inspiration_id: str,
    target_inspiration_id: str,
    *,
    edge_type: EdgeType = EdgeType.similarity,
    relationship_label: str | None = None,
    relationship_description: str = "",
    transferable_insight: str = (
        "These inspirations are connected as related concepts in the reasoning graph."
    ),
    derivation: DerivationLabel = DerivationLabel.MANUAL,
    weight: float = 0.5,
    confidence: float | None = None,
    evidence: list[str] | None = None,
) -> GraphEdge:
    """Build a GraphEdge stored with inspiration ids (DB convention)."""
    label = (relationship_label or "").strip() or default_relationship_label(edge_type)
    description = (relationship_description or "").strip() or f"{label} — semantic connection between ideas."
    return GraphEdge(
        id=f"{challenge_id}-edge-{uuid.uuid4()}",
        source_id=source_inspiration_id,
        target_id=target_inspiration_id,
        edge_type=edge_type,
        weight=weight,
        relationship_label=label,
        relationship_description=description,
        transferable_insight=transferable_insight,
        evidence=list(evidence) if evidence is not None else [],
        derivation=derivation,
        confidence=confidence,
    )


def resolve_auto_connect_peer(
    peers: list[Inspiration],
    preferred_inspiration_id: Optional[str] = None,
) -> Optional[Inspiration]:
    """
    Pick exactly one existing peer to connect a new inspiration to.

    Priority:
      1. preferred_inspiration_id when it matches a peer (selected / initiation)
      2. most recently created peer (last in insertion-ordered list)
      3. None when there are no peers (first node → no edge)
    """
    if not peers:
        return None

    if preferred_inspiration_id:
        preferred_id = to_inspiration_id(preferred_inspiration_id)
        for peer in peers:
            if peer.id == preferred_id:
                return peer

    return peers[-1]


def resolve_auto_connect(
    peers: list[Inspiration],
    *,
    preferred_inspiration_id: Optional[str] = None,
    connect_context: Optional[str] = None,
) -> tuple[Optional[Inspiration], Optional[AutoConnectContext]]:
    """
    Resolve peer + semantic context for a single automatic edge.

    Connection priority (unchanged):
      selected/initiation preferred id → most recent peer → none

    Semantic context:
      - explicit connect_context of selected|initiation when preferred peer matches
      - otherwise fallback (most recent), even if a preferred id was sent but not found
    """
    if not peers:
        return None, None

    preferred_peer: Inspiration | None = None
    if preferred_inspiration_id:
        preferred_id = to_inspiration_id(preferred_inspiration_id)
        for peer in peers:
            if peer.id == preferred_id:
                preferred_peer = peer
                break

    if preferred_peer is not None:
        if connect_context == AutoConnectContext.initiation.value:
            return preferred_peer, AutoConnectContext.initiation
        # Default preferred connections to "selected" when context omitted
        return preferred_peer, AutoConnectContext.selected

    # No usable preferred peer → most recent
    return peers[-1], AutoConnectContext.fallback


def auto_edge_semantics(
    context: AutoConnectContext,
    peer_name: str,
    new_name: str,
) -> dict:
    """
    Map creation context → semantic edge fields.

    Uses existing EdgeType / DerivationLabel values only:
      Builds on   → extension
      Inspired by → inspired_by
      Related to  → similarity  (general relationship)

    derivation = SYSTEM (deterministic context rule, not Granite/AI).
    confidence = None (not AI-inferred).
    """
    if context == AutoConnectContext.selected:
        return {
            "edge_type": EdgeType.extension,
            "relationship_label": "Builds on",
            "relationship_description": (
                f"Automatically connected because this idea ('{new_name}') was created "
                f"while '{peer_name}' was selected."
            ),
            "transferable_insight": (
                f"'{new_name}' builds on the selected idea '{peer_name}' in the current reasoning context."
            ),
            "derivation": DerivationLabel.SYSTEM,
            "confidence": None,
            "evidence": ["AUTO_CONTEXT:selected"],
        }
    if context == AutoConnectContext.initiation:
        return {
            "edge_type": EdgeType.inspired_by,
            "relationship_label": "Inspired by",
            "relationship_description": (
                f"Automatically connected because this idea ('{new_name}') was created "
                f"from '{peer_name}'."
            ),
            "transferable_insight": (
                f"'{new_name}' was inspired by '{peer_name}' via the creation initiation context."
            ),
            "derivation": DerivationLabel.SYSTEM,
            "confidence": None,
            "evidence": ["AUTO_CONTEXT:initiation"],
        }
    return {
        "edge_type": EdgeType.similarity,
        "relationship_label": "Related to",
        "relationship_description": (
            f"Automatically connected to the most recent idea '{peer_name}' "
            f"because no selected or initiation target was available."
        ),
        "transferable_insight": (
            f"'{new_name}' is related to the most recent peer '{peer_name}' as a fallback connection."
        ),
        "derivation": DerivationLabel.SYSTEM,
        "confidence": None,
        "evidence": ["AUTO_CONTEXT:fallback"],
    }


def edge_exists(
    edges: list[GraphEdge],
    source_inspiration_id: str,
    target_inspiration_id: str,
    edge_type: EdgeType,
    *,
    exclude_edge_id: str | None = None,
) -> bool:
    """True when an equivalent edge (same source, target, type) already exists."""
    return any(
        e.id != exclude_edge_id
        and e.source_id == source_inspiration_id
        and e.target_id == target_inspiration_id
        and e.edge_type == edge_type
        for e in edges
    )


def with_node_prefixed_ids(edge: GraphEdge) -> GraphEdge:
    """Return a copy with n-prefixed endpoints for frontend graph state."""
    data = edge.model_dump()
    if not data["source_id"].startswith("n-"):
        data["source_id"] = f"n-{data['source_id']}"
    if not data["target_id"].startswith("n-"):
        data["target_id"] = f"n-{data['target_id']}"
    return GraphEdge(**data)
