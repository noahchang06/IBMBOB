"""API tests for semantic edge create / update / delete and auto-connect."""


def _create_empty_user_challenge(client):
    resp = client.post("/api/challenges", json={
        "name": "Semantic Edge Challenge",
        "subtitle": "for edge tests",
        "description": "Starts with zero inspirations",
        "domains": ["film"],
        "tags": ["test"],
    })
    assert resp.status_code == 200
    return resp.json()


def _two_nodes(client, cid: str):
    a = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "A", "domain": "biology", "description": "idea a",
    }).json()["inspiration"]
    b = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "B", "domain": "biology", "description": "idea b",
        "connect_to_inspiration_id": a["id"],
    }).json()["inspiration"]
    return a, b


def test_first_node_creates_no_edge(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    resp = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "First", "domain": "biology", "description": "lone node",
    })
    assert resp.status_code == 200
    assert resp.json()["new_edges"] == []


def test_second_node_creates_exactly_one_auto_edge(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    first = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "First", "domain": "biology", "description": "a",
    }).json()["inspiration"]
    second = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "Second", "domain": "architecture", "description": "b",
    })
    assert second.status_code == 200
    data = second.json()
    assert len(data["new_edges"]) == 1
    edge = data["new_edges"][0]
    assert edge["source_id"] == first["id"]
    assert edge["target_id"] == data["inspiration"]["id"]
    assert edge["relationship_label"] == "Related to"
    assert edge["edge_type"] == "similarity"
    assert edge["derivation"] == "SYSTEM"
    assert edge["confidence"] is None
    assert "most recent" in edge["relationship_description"]


def test_auto_edge_selected_context_builds_on(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "SelectedPeer", "domain": "biology", "description": "a",
    }).json()["inspiration"]
    client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "Other", "domain": "biology", "description": "o",
    })
    created = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "FromSelection",
        "domain": "biology",
        "description": "c",
        "connect_to_inspiration_id": a["id"],
        "connect_context": "selected",
    })
    assert created.status_code == 200
    edge = created.json()["new_edges"][0]
    assert edge["source_id"] == a["id"]
    assert edge["relationship_label"] == "Builds on"
    assert edge["edge_type"] == "extension"
    assert edge["derivation"] == "SYSTEM"
    assert edge["confidence"] is None
    assert "selected" in edge["relationship_description"]
    assert "AUTO_CONTEXT:selected" in edge["evidence"]

    rebuilt = client.post("/api/graph/build", json={"challenge_id": cid}).json()
    match = next(e for e in rebuilt["graph"]["edges"] if e["id"] == edge["id"])
    assert match["relationship_label"] == "Builds on"


def test_auto_edge_initiation_context_inspired_by(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "InitPeer", "domain": "biology", "description": "a",
    }).json()["inspiration"]
    created = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "FromInitiation",
        "domain": "biology",
        "description": "c",
        "connect_to_inspiration_id": f"n-{a['id']}",
        "connect_context": "initiation",
    })
    assert created.status_code == 200
    edge = created.json()["new_edges"][0]
    assert edge["source_id"] == a["id"]
    assert edge["relationship_label"] == "Inspired by"
    assert edge["edge_type"] == "inspired_by"
    assert edge["derivation"] == "SYSTEM"
    assert "created from" in edge["relationship_description"]


def test_create_edge_with_preset_label(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a, b = _two_nodes(client, cid)
    resp = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": b["id"],
        "target_id": a["id"],
        "edge_type": "extension",
        "relationship_label": "Builds on",
        "relationship_description": "B expands A with a collaborative workflow.",
    })
    assert resp.status_code == 200
    edge = resp.json()
    assert edge["relationship_label"] == "Builds on"
    assert edge["edge_type"] == "extension"
    assert edge["source_id"].startswith("n-")
    assert "collaborative" in edge["relationship_description"]


def test_create_edge_with_custom_label(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a, b = _two_nodes(client, cid)
    resp = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": b["id"],
        "target_id": a["id"],
        "edge_type": "reference",
        "relationship_label": "Anticipates",
        "relationship_description": "Custom semantic link.",
    })
    assert resp.status_code == 200
    assert resp.json()["relationship_label"] == "Anticipates"


def test_update_edge_label_and_reasoning(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a, b = _two_nodes(client, cid)
    created = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": b["id"],
        "target_id": a["id"],
        "edge_type": "support",
        "relationship_label": "Supports",
        "relationship_description": "Initial",
    }).json()
    edge_id = created["id"]
    updated = client.patch(f"/api/challenges/{cid}/edges/{edge_id}", json={
        "relationship_label": "Refines",
        "edge_type": "refinement",
        "relationship_description": "B sharpens A's core claim.",
    })
    assert updated.status_code == 200
    body = updated.json()
    assert body["relationship_label"] == "Refines"
    assert body["edge_type"] == "refinement"
    assert "sharpens" in body["relationship_description"]

    rebuilt = client.post("/api/graph/build", json={"challenge_id": cid}).json()
    match = next(e for e in rebuilt["graph"]["edges"] if e["id"] == edge_id)
    assert match["relationship_label"] == "Refines"


def test_delete_edge_and_persistence(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a, b = _two_nodes(client, cid)
    created = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": b["id"],
        "target_id": a["id"],
        "edge_type": "contrast",
        "relationship_label": "Contrasts with",
        "relationship_description": "Tension.",
    }).json()
    edge_id = created["id"]
    deleted = client.delete(f"/api/challenges/{cid}/edges/{edge_id}")
    assert deleted.status_code == 204
    rebuilt = client.post("/api/graph/build", json={"challenge_id": cid}).json()
    assert all(e["id"] != edge_id for e in rebuilt["graph"]["edges"])


def test_manual_self_loop_blocked(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a = client.post(f"/api/challenges/{cid}/inspirations", json={
        "name": "A", "domain": "biology", "description": "a",
    }).json()["inspiration"]
    resp = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": a["id"],
        "target_id": a["id"],
        "relationship_label": "Similar to",
    })
    assert resp.status_code == 422


def test_manual_duplicate_edge_blocked(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a, b = _two_nodes(client, cid)
    # _two_nodes auto-edge is selected-context → extension A→B ("Builds on")
    resp = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": a["id"],
        "target_id": b["id"],
        "edge_type": "extension",
        "relationship_label": "Builds on",
    })
    assert resp.status_code == 409


def test_empty_label_rejected(client):
    challenge = _create_empty_user_challenge(client)
    cid = challenge["id"]
    a, b = _two_nodes(client, cid)
    resp = client.post(f"/api/challenges/{cid}/edges", json={
        "source_id": b["id"],
        "target_id": a["id"],
        "edge_type": "reference",
        "relationship_label": "   ",
    })
    assert resp.status_code == 422


def test_existing_curated_edges_still_load(client):
    resp = client.post("/api/graph/build", json={"challenge_id": "healthcare-dashboard"})
    assert resp.status_code == 200
    edges = resp.json()["graph"]["edges"]
    assert len(edges) == 15
    for edge in edges:
        assert edge.get("relationship_label")
        assert edge.get("relationship_description")
        assert edge["source_id"].startswith("n-")


def test_relationship_presets_endpoint(client):
    resp = client.get("/api/relationship-presets")
    assert resp.status_code == 200
    presets = resp.json()["presets"]
    labels = {p["label"] for p in presets}
    assert "Builds on" in labels
    assert "Inspired by" in labels
