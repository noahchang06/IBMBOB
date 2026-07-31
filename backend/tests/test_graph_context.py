"""Tests for semantic graph context used in Granite prompts (no live watsonx calls)."""

from app.services.graph_context import (
    build_relationship_prompt,
    build_semantic_graph_context,
    build_reasoning_summary_prompt,
    relationship_label_for_edge,
    select_neighborhood_node_ids,
    FALLBACK_RELATIONSHIP_LABEL,
)


def _sample_graph():
    return {
        "nodes": [
            {"id": "n-a", "label": "Idea A", "inspiration_id": "a", "domain": "biology", "importance": 0.9, "derivation": "MANUAL"},
            {"id": "n-b", "label": "Idea B", "inspiration_id": "b", "domain": "architecture", "importance": 0.8, "derivation": "MANUAL"},
            {"id": "n-c", "label": "Idea C", "inspiration_id": "c", "domain": "film", "importance": 0.2, "derivation": "CURATED"},
            {"id": "n-d", "label": "Unrelated D", "inspiration_id": "d", "domain": "music", "importance": 0.1, "derivation": "CURATED"},
        ],
        "edges": [
            {
                "id": "e1",
                "source_id": "n-a",
                "target_id": "n-b",
                "edge_type": "extension",
                "relationship_label": "Builds on",
                "relationship_description": "B expands A with collaboration.",
                "derivation": "MANUAL",
                "confidence": None,
                "transferable_insight": "Expand selectively.",
                "evidence": [],
                "weight": 0.5,
            },
            {
                "id": "e2",
                "source_id": "n-b",
                "target_id": "n-c",
                "edge_type": "contrast",
                "relationship_label": "Contrasts with",
                "relationship_description": "C tensions B.",
                "derivation": "AI",
                "confidence": 0.42,
                "transferable_insight": "",
                "evidence": [],
                "weight": 0.4,
            },
            {
                "id": "e3",
                "source_id": "n-d",
                "target_id": "n-d",
                "edge_type": "similarity",
                "relationship_description": "orphan self",
                "derivation": "CURATED",
                "weight": 0.1,
                "transferable_insight": "",
                "evidence": [],
            },
        ],
    }


def test_fallback_label_for_old_edges():
    assert relationship_label_for_edge({}) == FALLBACK_RELATIONSHIP_LABEL
    assert relationship_label_for_edge({"edge_type": "extension"}) == "Builds on"
    assert relationship_label_for_edge({"relationship_label": "  Inspired by  "}) == "Inspired by"


def test_neighborhood_excludes_unrelated_nodes():
    graph = _sample_graph()
    included = select_neighborhood_node_ids(graph, ["n-a"])
    assert "n-a" in included
    assert "n-b" in included  # neighbor via Builds on
    assert "n-d" not in included  # unrelated


def test_semantic_context_preserves_direction_and_manual_label():
    graph = _sample_graph()
    ctx = build_semantic_graph_context(graph, ["n-a", "n-b"])
    edge_labels = {e["relationship_label"] for e in ctx["edges"]}
    assert "Builds on" in edge_labels
    # Direction preserved
    builds = next(e for e in ctx["edges"] if e["relationship_label"] == "Builds on")
    assert builds["source"] == "n-a"
    assert builds["target"] == "n-b"
    assert builds["derivation"] == "MANUAL"
    assert builds["confidence"] is None
    # Per-node incoming/outgoing
    node_a = next(n for n in ctx["nodes"] if n["id"] == "n-a")
    assert any(r["relationship_label"] == "Builds on" for r in node_a["outgoing_relationships"])
    node_b = next(n for n in ctx["nodes"] if n["id"] == "n-b")
    assert any(r["relationship_label"] == "Builds on" for r in node_b["incoming_relationships"])
    # Unrelated D excluded
    assert all(n["id"] != "n-d" for n in ctx["nodes"])


def test_old_edge_without_label_gets_fallback_in_context():
    graph = {
        "nodes": [
            {"id": "n-1", "label": "One", "importance": 1},
            {"id": "n-2", "label": "Two", "importance": 1},
        ],
        "edges": [{
            "id": "e-old",
            "source_id": "n-1",
            "target_id": "n-2",
            "edge_type": "functional_similarity",
            "relationship_description": "legacy",
            "derivation": "CURATED",
            "weight": 0.5,
            "evidence": [],
            "transferable_insight": "",
        }],
    }
    ctx = build_semantic_graph_context(graph, ["n-1"])
    assert ctx["edges"][0]["relationship_label"] == "Related to"


def test_relationship_prompt_includes_semantic_edges_and_instructions():
    graph = _sample_graph()
    ctx = build_semantic_graph_context(graph, ["n-a", "n-b"])
    edge = graph["edges"][0]
    source = graph["nodes"][0]
    target = graph["nodes"][1]
    prompt = build_relationship_prompt(source, target, edge, ctx)

    assert "You are analyzing a creative reasoning graph" in prompt
    assert "Builds on" in prompt
    assert "MANUAL" in prompt
    assert "Do not infer that two ideas are related merely because they are nearby" in prompt
    assert "n-a" in prompt and "n-b" in prompt
    assert "Unrelated D" not in prompt
    assert '"relationship_label": "Builds on"' in prompt
    assert "AI inference" in prompt


def test_reasoning_summary_prompt_uses_semantic_json():
    graph = _sample_graph()
    prompt = build_reasoning_summary_prompt(graph, {"accessibility": 0.8}, {"wcag_level": "AA"})
    assert "Semantic reasoning graph" in prompt
    assert "Builds on" in prompt or "Contrasts with" in prompt
    assert "observed graph relationships" in prompt.lower() or "observed" in prompt.lower()
