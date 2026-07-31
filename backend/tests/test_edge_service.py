"""Unit tests for deterministic auto-connect / semantic edge helpers."""

from app.models.common import DomainType, DerivationLabel
from app.models.graph import EdgeType, GraphEdge
from app.models.inspiration import Inspiration
from app.services.edge_service import (
    AutoConnectContext,
    auto_edge_semantics,
    build_related_edge,
    edge_exists,
    resolve_auto_connect,
    resolve_auto_connect_peer,
    to_inspiration_id,
)


def _insp(insp_id: str, name: str = "n") -> Inspiration:
    return Inspiration(
        id=insp_id,
        name=name,
        domain=DomainType.biology,
        description="d",
        historical_context="",
        key_principles=[],
        transferable_lessons=[],
        related_concepts=[],
        design_implications=[],
        derivation=DerivationLabel.MANUAL,
    )


def test_to_inspiration_id_strips_node_prefix():
    assert to_inspiration_id("n-abc") == "abc"
    assert to_inspiration_id("abc") == "abc"


def test_resolve_auto_connect_empty_peers():
    assert resolve_auto_connect_peer([]) is None
    peer, ctx = resolve_auto_connect([])
    assert peer is None and ctx is None


def test_resolve_auto_connect_prefers_selected():
    peers = [_insp("a"), _insp("b"), _insp("c")]
    peer, ctx = resolve_auto_connect(
        peers,
        preferred_inspiration_id="n-b",
        connect_context="selected",
    )
    assert peer is not None and peer.id == "b"
    assert ctx == AutoConnectContext.selected


def test_resolve_auto_connect_initiation_context():
    peers = [_insp("a", "Alpha"), _insp("b", "Beta")]
    peer, ctx = resolve_auto_connect(
        peers,
        preferred_inspiration_id="a",
        connect_context="initiation",
    )
    assert peer is not None and peer.id == "a"
    assert ctx == AutoConnectContext.initiation


def test_resolve_auto_connect_falls_back_to_most_recent():
    peers = [_insp("a"), _insp("b"), _insp("c")]
    peer, ctx = resolve_auto_connect(peers, preferred_inspiration_id="missing")
    assert peer is not None and peer.id == "c"
    assert ctx == AutoConnectContext.fallback


def test_auto_edge_semantics_by_context():
    selected = auto_edge_semantics(AutoConnectContext.selected, "Peer", "New")
    assert selected["relationship_label"] == "Builds on"
    assert selected["edge_type"] == EdgeType.extension
    assert selected["derivation"] == DerivationLabel.SYSTEM
    assert selected["confidence"] is None
    assert "selected" in selected["relationship_description"]

    initiation = auto_edge_semantics(AutoConnectContext.initiation, "Peer", "New")
    assert initiation["relationship_label"] == "Inspired by"
    assert initiation["edge_type"] == EdgeType.inspired_by
    assert "created from" in initiation["relationship_description"]

    fallback = auto_edge_semantics(AutoConnectContext.fallback, "Peer", "New")
    assert fallback["relationship_label"] == "Related to"
    assert fallback["edge_type"] == EdgeType.similarity
    assert "most recent" in fallback["relationship_description"]


def test_build_related_edge_semantics():
    edge = build_related_edge(
        "user-1",
        "source-insp",
        "target-insp",
        edge_type=EdgeType.extension,
        relationship_label="Builds on",
        relationship_description="Expands with collaboration.",
        derivation=DerivationLabel.SYSTEM,
        confidence=None,
        evidence=["AUTO_CONTEXT:selected"],
    )
    assert edge.relationship_label == "Builds on"
    assert edge.derivation == DerivationLabel.SYSTEM
    assert edge.confidence is None
    assert edge.evidence == ["AUTO_CONTEXT:selected"]


def test_edge_exists_duplicate_detection():
    edges = [
        GraphEdge(
            id="e1",
            source_id="a",
            target_id="b",
            edge_type=EdgeType.extension,
            weight=0.5,
            relationship_label="Builds on",
            relationship_description="x",
            transferable_insight="x",
            evidence=[],
            derivation=DerivationLabel.SYSTEM,
        )
    ]
    assert edge_exists(edges, "a", "b", EdgeType.extension)
    assert not edge_exists(edges, "a", "b", EdgeType.contrast)
