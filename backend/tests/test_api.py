import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["granite_mode"] in ("mock", "watsonx")
    assert "granite_model" in data

def test_list_challenges():
    response = client.get("/api/challenges")
    assert response.status_code == 200
    data = response.json()
    assert "challenges" in data
    assert len(data["challenges"]) >= 1
    assert data["challenges"][0]["id"] == "healthcare-dashboard"

def test_get_challenge_detail():
    response = client.get("/api/challenges/healthcare-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "healthcare-dashboard"
    assert data["node_count"] == 12

def test_build_graph():
    response = client.post("/api/graph/build", json={"challenge_id": "healthcare-dashboard"})
    assert response.status_code == 200
    data = response.json()
    assert "graph" in data
    assert "inspirations" in data
    assert "design_system" in data
    assert len(data["graph"]["nodes"]) == 12
    assert len(data["graph"]["edges"]) == 15
    assert len(data["inspirations"]) == 12

def test_apply_constraints():
    build_resp = client.post("/api/graph/build", json={"challenge_id": "healthcare-dashboard"})
    graph = build_resp.json()["graph"]
    
    constraints = {
        "visual_tension": 0.8,
        "information_density": 0.7,
        "accessibility": 0.9,
        "playfulness": 0.2,
        "material_scarcity": 0.4
    }
    
    response = client.post("/api/graph/apply-constraints", json={"graph": graph, "constraints": constraints})
    assert response.status_code == 200
    data = response.json()
    assert "graph" in data
    assert "effects" in data
    assert "design_system" in data
    assert len(data["effects"]) > 0
    assert data["design_system"]["wcag_level"] == "AAA"

def test_explain_node():
    build_resp = client.post("/api/graph/build", json={"challenge_id": "healthcare-dashboard"})
    graph = build_resp.json()["graph"]
    node = graph["nodes"][0]
    
    response = client.post("/api/explain", json={
        "target_type": "node",
        "target_id": node["id"],
        "context": {"node": node}
    })
    assert response.status_code == 200
    data = response.json()
    assert "chain" in data
    assert len(data["chain"]["retrieved_knowledge"]) > 0
    assert len(data["chain"]["deterministic_reasoning"]) > 0
    assert len(data["chain"]["ai_interpretation"]) > 0

def test_explain_edge():
    build_resp = client.post("/api/graph/build", json={"challenge_id": "healthcare-dashboard"})
    graph = build_resp.json()["graph"]
    edge = graph["edges"][0]
    
    response = client.post("/api/explain/edge", json={
        "edge_id": edge["id"],
        "source": {"id": edge["source_id"], "label": "Source"},
        "target": {"id": edge["target_id"], "label": "Target"},
        "edge": edge
    })
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data

def test_export_package():
    build_resp = client.post("/api/graph/build", json={"challenge_id": "healthcare-dashboard"})
    graph = build_resp.json()["graph"]
    constraints = {"accessibility": 0.8}
    
    response = client.post("/api/export", json={
        "challenge_id": "healthcare-dashboard",
        "graph": graph,
        "constraints": constraints,
        "inspiration_ids": ["hc-circadian", "hc-wayfinding"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "challenge_name" in data
    assert "design_tokens" in data
    assert "reasoning_summary_markdown" in data
