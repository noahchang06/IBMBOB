"""Tests for semantic relationship analysis used by explanations and Granite prompts."""

from app.services.relationship_analysis import (
    MISSING_RELATIONSHIP_MESSAGE,
    analyze_comparison,
    analyze_node_relationships,
    analyze_recommendation_support,
    find_contradictions,
    format_path_prose,
    find_paths,
    provenance_phrase,
)
from app.services.graph_context import format_relationship_semantics_for_prompts
from app.services.explanation_service import ExplanationService
from app.services.mock_granite import MockGraniteAdapter
from app.models.explanation import ExplanationRequest


def _graph_with_path():
    return {
        "nodes": [
            {"id": "n-a", "label": "Idea A", "importance": 0.9},
            {"id": "n-b", "label": "Idea B", "importance": 0.8},
            {"id": "n-c", "label": "Idea C", "importance": 0.7},
            {"id": "n-d", "label": "Idea D", "importance": 0.1},
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
                "weight": 0.8,
                "confidence": None,
            },
            {
                "id": "e2",
                "source_id": "n-b",
                "target_id": "n-c",
                "edge_type": "contrast",
                "relationship_label": "Contrasts with",
                "relationship_description": "C tensions B.",
                "derivation": "AI",
                "weight": 0.6,
                "confidence": 0.55,
            },
        ],
    }


def _graph_with_contradiction():
    g = _graph_with_path()
    g["edges"].append({
        "id": "e3",
        "source_id": "n-a",
        "target_id": "n-b",
        "edge_type": "support",
        "relationship_label": "Supports",
        "relationship_description": "A affirms B.",
        "derivation": "AI_ACCEPTED",
        "weight": 0.7,
        "confidence": 0.8,
    })
    # Also add contrast on same pair
    g["edges"].append({
        "id": "e4",
        "source_id": "n-b",
        "target_id": "n-a",
        "edge_type": "contrast",
        "relationship_label": "Contrasts with",
        "relationship_description": "B challenges A.",
        "derivation": "MANUAL",
        "weight": 0.5,
        "confidence": None,
    })
    return g


def test_direct_relationship_explanation_prose():
    g = _graph_with_path()
    comparison = analyze_comparison(g, "n-a", "n-b")
    assert comparison["has_relationship"] is True
    assert any("builds on" in p.lower() for p in comparison["direct_paths"])
    assert "collaboration" in comparison["prose"]
    assert "user-authored" in comparison["prose"]


def test_two_hop_reasoning_path():
    g = _graph_with_path()
    paths = find_paths(g, "n-a", "n-c", max_hops=3)
    assert paths
    assert paths[0].length == 2
    prose = format_path_prose(paths[0])
    assert "Idea A" in prose
    assert "builds on" in prose.lower()
    assert "Idea B" in prose
    assert "contrasts with" in prose.lower()
    assert "Idea C" in prose

    comparison = analyze_comparison(g, "n-a", "n-c")
    assert comparison["indirect_paths"]
    assert "builds on" in comparison["indirect_paths"][0].lower()


def test_contrasting_edges_surfaced():
    g = _graph_with_contradiction()
    contradictions = find_contradictions(g, ["n-a", "n-b"])
    assert contradictions
    flat = " ".join(f"{a} {b}" for c in contradictions for a, b in [c.labels])
    assert "contrasts" in flat.lower()
    # Supportive side may be "Supports" or "Builds on" (both supportive)
    assert "supports" in flat.lower() or "builds on" in flat.lower()


def test_manual_versus_ai_provenance():
    assert "user-authored" in provenance_phrase("MANUAL")
    assert "suggestion" in provenance_phrase("AI").lower()
    assert "accepted" in provenance_phrase("AI_ACCEPTED").lower()

    g = _graph_with_path()
    analysis = analyze_node_relationships(g, "n-a")
    assert "user-authored" in analysis["prose"]
    # Outgoing Builds on is MANUAL
    out = analysis["strongest_outgoing"]
    assert out
    assert out[0]["derivation"] == "MANUAL"

    analysis_b = analyze_node_relationships(g, "n-b")
    # Incoming from A is MANUAL; outgoing Contrasts is AI
    assert any(e["derivation"] == "AI" for e in analysis_b["strongest_outgoing"])


def test_missing_relationship_fallback_no_fabrication():
    g = _graph_with_path()
    comparison = analyze_comparison(g, "n-a", "n-d")
    assert comparison["has_relationship"] is False
    assert MISSING_RELATIONSHIP_MESSAGE in comparison["prose"]
    assert comparison["direct_paths"] == []
    assert comparison["indirect_paths"] == []

    isolated = analyze_node_relationships(g, "n-d")
    assert isolated["has_relationships"] is False
    assert "Do not invent" in isolated["prose"]


def test_recommendation_cites_existing_relationships_only():
    g = _graph_with_path()
    support = analyze_recommendation_support(g, ["n-a"])
    assert support["has_support"] is True
    assert any("Builds on" in s["relationship_label"] or "builds on" in s["prose"].lower()
               for s in support["supporting_relationships"])

    empty = analyze_recommendation_support({"nodes": g["nodes"], "edges": []})
    assert empty["has_support"] is False
    assert "Do not invent" in empty["prose"] or "not invent" in empty["prose"].lower() or "AI inference" in empty["prose"]


def test_reusable_formatter_shared_semantics():
    g = _graph_with_path()
    block = format_relationship_semantics_for_prompts(g, ["n-a"], include_recommendation_support=True)
    assert "Observed relationship semantics" in block
    assert "Builds on" in block or "builds on" in block.lower()
    assert "user-authored" in block


def test_explanation_service_node_includes_strongest_relationships():
    import asyncio

    svc = ExplanationService(MockGraniteAdapter())
    g = _graph_with_path()
    req = ExplanationRequest(
        target_type="node",
        target_id="n-a",
        context={
            "node": g["nodes"][0],
            "inspiration": {"name": "Idea A", "domain": "biology", "description": "seed"},
            "graph": g,
        },
    )
    resp = asyncio.run(svc.explain(req))
    joined = " ".join(
        s.description
        for s in (
            resp.chain.retrieved_knowledge
            + resp.chain.deterministic_reasoning
            + resp.chain.ai_interpretation
        )
    )
    assert "Builds on" in joined or "builds on" in joined.lower()
    assert "Idea B" in joined


def test_explanation_service_compare_two_hop_and_missing():
    import asyncio

    svc = ExplanationService(MockGraniteAdapter())
    g = _graph_with_path()
    resp = asyncio.run(svc.explain(ExplanationRequest(
        target_type="compare",
        target_id="n-a:n-c",
        context={"graph": g, "source": g["nodes"][0], "target": g["nodes"][2]},
    )))
    assert "builds on" in resp.summary.lower()
    assert "contrasts with" in resp.summary.lower()

    missing = asyncio.run(svc.explain(ExplanationRequest(
        target_type="compare",
        target_id="n-a:n-d",
        context={"graph": g, "source": g["nodes"][0], "target": g["nodes"][3]},
    )))
    assert "No meaningful semantic relationship" in missing.summary
    assert "invent" in missing.summary.lower()


def test_serialize_reasoning_path_preserves_order_and_direction():
    from app.services.relationship_analysis import (
        PathHop,
        RelationshipPath,
        serialize_reasoning_path,
    )

    path = RelationshipPath(hops=[
        PathHop(
            source_id="n-a", target_id="n-b",
            source_title="Idea A", target_title="Idea B",
            relationship_label="Builds on",
            relationship_description="B expands A.",
            derivation="MANUAL", edge_type="extension", edge_id="e1",
        ),
        PathHop(
            source_id="n-b", target_id="n-c",
            source_title="Idea B", target_title="Idea C",
            relationship_label="Contrasts with",
            relationship_description="C tensions B.",
            derivation="AI", edge_type="contrast", edge_id="e2", confidence=0.55,
        ),
    ])
    payload = serialize_reasoning_path(path)
    assert [n["id"] for n in payload["nodes"]] == ["n-a", "n-b", "n-c"]
    assert [e["id"] for e in payload["edges"]] == ["e1", "e2"]
    assert payload["edges"][0]["source"] == "n-a"
    assert payload["edges"][0]["target"] == "n-b"
    assert payload["edges"][1]["relationship_label"] == "Contrasts with"
    assert "builds on" in payload["prose"].lower()


def test_comparison_paths_included_and_empty_when_missing():
    g = _graph_with_path()
    comparison = analyze_comparison(g, "n-a", "n-c")
    assert comparison["paths"]
    path = comparison["paths"][0]
    assert path["nodes"][0]["id"] == "n-a"
    assert path["nodes"][-1]["id"] == "n-c"
    assert path["edges"][0]["source"] == "n-a"
    assert path["edges"][0]["target"] == "n-b"

    missing = analyze_comparison(g, "n-a", "n-d")
    assert missing["paths"] == []


def test_explanation_response_includes_structured_paths():
    import asyncio

    svc = ExplanationService(MockGraniteAdapter())
    g = _graph_with_path()
    resp = asyncio.run(svc.explain(ExplanationRequest(
        target_type="compare",
        target_id="n-a:n-c",
        context={"graph": g, "source": g["nodes"][0], "target": g["nodes"][2]},
    )))
    assert resp.paths
    assert resp.paths[0].nodes[0].id == "n-a"
    assert resp.paths[0].edges[0].relationship_label == "Builds on"
    assert resp.paths[0].edges[0].source == "n-a"
    assert resp.paths[0].edges[0].target == "n-b"

    no_path = asyncio.run(svc.explain(ExplanationRequest(
        target_type="compare",
        target_id="n-a:n-d",
        context={"graph": g, "source": g["nodes"][0], "target": g["nodes"][3]},
    )))
    assert no_path.paths == []


def test_explanation_service_recommend_and_edge_provenance():
    import asyncio

    svc = ExplanationService(MockGraniteAdapter())
    g = _graph_with_path()
    rec = asyncio.run(svc.explain(ExplanationRequest(
        target_type="recommend",
        target_id="n-a",
        context={"graph": g, "focus_node_ids": ["n-a"]},
    )))
    assert "supported by observed" in rec.summary.lower() or "Builds on" in rec.summary
    assert rec.paths
    assert rec.paths[0].edges[0].relationship_label

    edge_resp = asyncio.run(svc.explain(ExplanationRequest(
        target_type="edge",
        target_id="e1",
        context={
            "source": g["nodes"][0],
            "target": g["nodes"][1],
            "edge": g["edges"][0],
            "graph": g,
        },
    )))
    joined = " ".join(s.description for s in edge_resp.chain.retrieved_knowledge)
    assert "user-authored" in joined
    assert "collaboration" in joined
    assert edge_resp.paths
    assert edge_resp.paths[0].edges[0].source == "n-a"
