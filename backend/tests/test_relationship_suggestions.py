"""Tests for Granite relationship suggestions (parse + API; never auto-persist)."""

from unittest.mock import AsyncMock

import pytest

from app.models.graph import EdgeType
from app.services.relationship_suggestions import (
    parse_relationship_suggestions,
    RelationshipSuggestionResponse,
)


def test_parse_valid_structured_granite_response():
    raw = """
    {
      "suggestions": [
        {
          "edge_type": "extension",
          "relationship_label": "Builds on",
          "relationship_description": "The target expands the source by adding collaboration.",
          "confidence": 0.82
        },
        {
          "edge_type": "inspiration",
          "relationship_label": "Inspired by",
          "relationship_description": "Target draws creative direction from source.",
          "confidence": 0.7
        }
      ]
    }
    """
    result = parse_relationship_suggestions(raw)
    assert len(result.suggestions) == 2
    assert result.suggestions[0].edge_type == EdgeType.extension
    assert result.suggestions[0].confidence == 0.82
    assert result.suggestions[1].edge_type == EdgeType.inspired_by


def test_parse_maps_composition_and_omits_invalid_confidence():
    raw = '{"suggestions":[{"edge_type":"composition","relationship_label":"Composed of","relationship_description":"Parts combine.","confidence":"high"}]}'
    result = parse_relationship_suggestions(raw)
    assert result.suggestions[0].edge_type == EdgeType.combination
    assert result.suggestions[0].confidence is None


def test_parse_malformed_granite_response_raises():
    with pytest.raises(ValueError):
        parse_relationship_suggestions("Sorry, I cannot help with that.")
    with pytest.raises(ValueError):
        parse_relationship_suggestions('{"suggestions":[]}')
    with pytest.raises(ValueError):
        parse_relationship_suggestions('{"oops": true}')


def test_parse_caps_at_three_suggestions():
    items = [
        {
            "edge_type": "similarity",
            "relationship_label": f"Related {i}",
            "relationship_description": f"desc {i}",
            "confidence": 0.5,
        }
        for i in range(5)
    ]
    result = RelationshipSuggestionResponse.model_validate({"suggestions": items})
    assert len(result.suggestions) == 3


def _create_challenge_with_two_nodes(client):
    challenge = client.post("/api/challenges", json={
        "name": "Suggest Rel Challenge",
        "subtitle": "suggest tests",
        "description": "two ideas",
        "domains": ["film"],
        "tags": ["test"],
    }).json()
    cid = challenge["id"]
    a = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "SourceIdea", "domain": "biology", "description": "seed concept",
    }).json()["inspiration"]
    b = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "TargetIdea",
        "domain": "architecture",
        "description": "expanded application",
        "connect_to_inspiration_id": a["id"],
    }).json()["inspiration"]
    return cid, a, b


def _edge_count(client, cid: str) -> int:
    rebuilt = client.post("/api/graph/build", json={"challenge_id": cid}).json()
    return len(rebuilt["graph"]["edges"])


def test_suggest_endpoint_returns_suggestions_without_persisting(client):
    cid, a, b = _create_challenge_with_two_nodes(client)
    before = _edge_count(client, cid)

    resp = client.post(f"/api/challenges/{cid}/edges/suggest", json={
        "source_id": a["id"],
        "target_id": b["id"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data
    assert 1 <= len(data["suggestions"]) <= 3
    assert data["suggestions"][0]["relationship_label"]
    assert data["suggestions"][0]["relationship_description"]
    assert data["suggestions"][0]["edge_type"]

    assert _edge_count(client, cid) == before


def test_suggest_malformed_granite_returns_502(client, monkeypatch):
    cid, a, b = _create_challenge_with_two_nodes(client)
    before = _edge_count(client, cid)

    async def boom(*_args, **_kwargs):
        raise ValueError("No JSON object found in model response")

    monkeypatch.setattr(
        "app.api.routes.granite_adapter.suggest_relationships",
        AsyncMock(side_effect=boom),
    )

    resp = client.post(f"/api/challenges/{cid}/edges/suggest", json={
        "source_id": a["id"],
        "target_id": b["id"],
    })
    assert resp.status_code == 502
    assert "unusable" in resp.json()["detail"].lower()
    assert _edge_count(client, cid) == before


def test_suggest_timeout_returns_504(client, monkeypatch):
    cid, a, b = _create_challenge_with_two_nodes(client)
    before = _edge_count(client, cid)

    async def timeout(*_args, **_kwargs):
        raise TimeoutError("timed out")

    monkeypatch.setattr(
        "app.api.routes.granite_adapter.suggest_relationships",
        AsyncMock(side_effect=timeout),
    )

    resp = client.post(f"/api/challenges/{cid}/edges/suggest", json={
        "source_id": a["id"],
        "target_id": b["id"],
    })
    assert resp.status_code == 504
    assert _edge_count(client, cid) == before


def test_suggest_watsonx_error_returns_502(client, monkeypatch):
    cid, a, b = _create_challenge_with_two_nodes(client)

    async def fail(*_args, **_kwargs):
        raise RuntimeError("watsonx unavailable")

    monkeypatch.setattr(
        "app.api.routes.granite_adapter.suggest_relationships",
        AsyncMock(side_effect=fail),
    )

    resp = client.post(f"/api/challenges/{cid}/edges/suggest", json={
        "source_id": a["id"],
        "target_id": b["id"],
    })
    assert resp.status_code == 502
    detail = resp.json()["detail"]
    assert "credential" not in detail.lower()
    assert "api_key" not in detail.lower()


def test_accepted_suggestion_persists_as_ai_accepted(client):
    cid, a, b = _create_challenge_with_two_nodes(client)
    before = _edge_count(client, cid)
    # Opposite direction from the auto-edge so type/direction do not collide.
    resp = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": b["id"],
        "target_id": a["id"],
        "edge_type": "extension",
        "relationship_label": "Builds on",
        "relationship_description": "Accepted Granite suggestion.",
        "confidence": 0.82,
        "from_ai_suggestion": True,
        "suggestion_edited": False,
    })
    assert resp.status_code == 200
    edge = resp.json()
    assert edge["derivation"] == "AI_ACCEPTED"
    assert "AI_SUGGESTION" in edge["evidence"]
    assert "USER_EDITED" not in edge["evidence"]
    assert edge["confidence"] == 0.82
    assert _edge_count(client, cid) == before + 1


def test_edited_suggestion_preserves_ai_origin(client):
    cid, a, b = _create_challenge_with_two_nodes(client)
    resp = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": a["id"],
        "target_id": b["id"],
        "edge_type": "contrast",
        "relationship_label": "Productively opposes",
        "relationship_description": "User-edited reasoning after Granite.",
        "confidence": 0.6,
        "from_ai_suggestion": True,
        "suggestion_edited": True,
    })
    assert resp.status_code == 200
    edge = resp.json()
    assert edge["derivation"] == "AI_ACCEPTED"
    assert "AI_SUGGESTION" in edge["evidence"]
    assert "USER_EDITED" in edge["evidence"]


def test_rejected_suggestion_creates_no_edge(client):
    """Rejecting is a client-only action; without create, graph is unchanged."""
    cid, a, b = _create_challenge_with_two_nodes(client)
    before = _edge_count(client, cid)
    suggest = client.post(f"/api/challenges/{cid}/edges/suggest", json={
        "source_id": a["id"],
        "target_id": b["id"],
    })
    assert suggest.status_code == 200
    assert len(suggest.json()["suggestions"]) >= 1
    # User rejects all suggestions → no POST /edges
    assert _edge_count(client, cid) == before
