import logging
import uuid
from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from pydantic import BaseModel

from app.config import settings
from app.data.knowledge_base import knowledge_base
from app.db.dependencies import repo
from app.models.challenge import ChallengeListResponse, PresetChallenge
from app.models.common import DomainType, DerivationLabel
from app.models.graph import ReasoningGraph, GraphEdge, EdgeType, RELATIONSHIP_PRESETS
from app.models.inspiration import Inspiration
from app.models.constraints import ConstraintSet, ConstraintKey
from app.models.design_system import DesignSystem
from app.models.export import ExportPackage
from app.models.explanation import ExplanationRequest, ExplanationResponse
from app.services.graph_service import GraphService
from app.services.constraint_engine import ConstraintEngine
from app.services.design_system_service import DesignSystemService
from app.services.explanation_service import ExplanationService
from app.services.edge_service import (
    auto_edge_semantics,
    build_related_edge,
    edge_exists,
    resolve_auto_connect,
    to_inspiration_id,
    with_node_prefixed_ids,
)
from app.services.graph_context import build_semantic_graph_context
from app.services.relationship_suggestions import RelationshipSuggestionResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

graph_service = GraphService(repo)
constraint_engine = ConstraintEngine()
design_system_service = DesignSystemService()

def _make_granite_adapter():
    if settings.USE_MOCK_GRANITE:
        from app.services.mock_granite import MockGraniteAdapter
        return MockGraniteAdapter()
    if not settings.GRANITE_API_KEY or not settings.WATSONX_PROJECT_ID:
        logger.warning("GRANITE_API_KEY or WATSONX_PROJECT_ID is not set. Falling back to MockGraniteAdapter.")
        from app.services.mock_granite import MockGraniteAdapter
        return MockGraniteAdapter()
    from app.services.watsonx_granite import WatsonXGraniteAdapter
    logger.info("IBM Granite enabled — model=%s endpoint=%s", settings.GRANITE_MODEL_ID, settings.GRANITE_API_URL)
    return WatsonXGraniteAdapter()

granite_adapter = _make_granite_adapter()
explanation_service = ExplanationService(granite_adapter)

class BuildGraphRequest(BaseModel):
    challenge_id: str

class ApplyConstraintsRequest(BaseModel):
    graph: ReasoningGraph
    constraints: ConstraintSet

class GenerateDesignSystemRequest(BaseModel):
    graph: ReasoningGraph
    constraints: ConstraintSet
    
class CreateChallengeRequest(BaseModel):
    name: str
    subtitle: str
    description: str
    domains: list[DomainType]
    tags: list[str]

class CreateInspirationRequest(BaseModel):
    name: str
    domain: DomainType
    description: str
    # Preferred peer for the single auto-edge (selected or initiation node).
    # Accepts inspiration id or graph node id (`n-…`).
    connect_to_inspiration_id: str | None = None
    # Why that peer was chosen: "selected" | "initiation". Omit for fallback.
    connect_context: str | None = None

class AddInspirationResponse(BaseModel):
    inspiration: Inspiration
    new_edges: list[GraphEdge]

class CreateEdgeRequest(BaseModel):
    source_id: str  # inspiration id or `n-…` node id
    target_id: str
    edge_type: EdgeType = EdgeType.similarity
    relationship_label: str = "Similar to"
    relationship_description: str = ""
    transferable_insight: str = (
        "These inspirations are connected as related concepts in the reasoning graph."
    )
    confidence: float | None = None
    # When accepting a Granite suggestion (possibly edited), clients send AI_ACCEPTED.
    derivation: DerivationLabel = DerivationLabel.MANUAL
    from_ai_suggestion: bool = False
    suggestion_edited: bool = False


class SuggestRelationshipsRequest(BaseModel):
    source_id: str
    target_id: str
    graph: dict | None = None
    inspirations: list[dict] | None = None


class UpdateEdgeRequest(BaseModel):
    edge_type: EdgeType | None = None
    relationship_label: str | None = None
    relationship_description: str | None = None
    transferable_insight: str | None = None
    confidence: float | None = None
    weight: float | None = None

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "granite_mode": "mock" if settings.USE_MOCK_GRANITE else "watsonx",
        "granite_model": settings.GRANITE_MODEL_ID,
    }

@router.get("/challenges", response_model=ChallengeListResponse)
async def list_challenges():
    seeded_challenges = knowledge_base.get_challenges()
    db_challenges = await repo.get_all_challenges()
    
    for challenge in db_challenges:
        inspirations = await repo.get_inspirations_for_challenge(challenge.id)
        challenge.node_count = len(inspirations)

    all_challenges = {challenge.id: challenge for challenge in seeded_challenges}
    for challenge in db_challenges:
        if challenge.id not in all_challenges:
            all_challenges[challenge.id] = challenge
            
    return {"challenges": list(all_challenges.values())}

@router.post("/challenges", response_model=PresetChallenge)
async def create_challenge(challenge_req: CreateChallengeRequest):
    new_id = f"user-{uuid.uuid4()}"
    new_challenge = PresetChallenge(
        id=new_id,
        name=challenge_req.name,
        subtitle=challenge_req.subtitle,
        description=challenge_req.description,
        domains=challenge_req.domains,
        tags=challenge_req.tags,
        node_count=0
    )
    await repo.create_challenge(new_challenge)
    
    # Generate and save inspirations
    inspirations = await granite_adapter.generate_inspirations(new_challenge)
    for insp in inspirations:
        await repo.create_inspiration(new_id, insp)
        
    # Generate and save edges
    edges = await granite_adapter.generate_edges(new_id, inspirations)
    for edge in edges:
        await repo.create_edge(new_id, edge)
        
    return new_challenge

@router.post("/challenges/{challenge_id}/inspirations", response_model=AddInspirationResponse)
async def add_inspiration(challenge_id: str, insp_req: CreateInspirationRequest):
    if not challenge_id.startswith("user-"):
        raise HTTPException(status_code=400, detail="Cannot add inspirations to a curated challenge.")

    new_id = f"{challenge_id}-manual-{uuid.uuid4()}"
    new_inspiration = Inspiration(
        id=new_id,
        name=insp_req.name,
        domain=insp_req.domain,
        description=insp_req.description,
        historical_context="",
        key_principles=[],
        transferable_lessons=[],
        related_concepts=[],
        design_implications=[],
        derivation=DerivationLabel.MANUAL,
    )
    await repo.create_inspiration(challenge_id, new_inspiration)

    existing_inspirations = await repo.get_inspirations_for_challenge(challenge_id)
    peers = [i for i in existing_inspirations if i.id != new_inspiration.id]

    # Exactly one deterministic auto-edge (or none for the first node).
    # Peer priority: selected/initiation preferred id → most recent → none.
    # Semantics depend on connect_context (selected / initiation / fallback).
    new_edges: list[GraphEdge] = []
    peer, auto_context = resolve_auto_connect(
        peers,
        preferred_inspiration_id=insp_req.connect_to_inspiration_id,
        connect_context=insp_req.connect_context,
    )
    if peer is not None and auto_context is not None:
        existing_edges = await repo.get_edges_for_challenge(challenge_id)
        semantics = auto_edge_semantics(auto_context, peer.name, new_inspiration.name)
        edge = build_related_edge(
            challenge_id,
            source_inspiration_id=peer.id,
            target_inspiration_id=new_inspiration.id,
            **semantics,
        )
        if not edge_exists(existing_edges, edge.source_id, edge.target_id, edge.edge_type):
            await repo.create_edge(challenge_id, edge)
            new_edges.append(edge)

    return AddInspirationResponse(inspiration=new_inspiration, new_edges=new_edges)


@router.get("/relationship-presets")
async def relationship_presets():
    return {"presets": RELATIONSHIP_PRESETS}


@router.post(
    "/challenges/{challenge_id}/edges/suggest",
    response_model=RelationshipSuggestionResponse,
)
async def suggest_edge_relationships(challenge_id: str, req: SuggestRelationshipsRequest):
    """
    Ask Granite for relationship suggestions. NEVER persists an edge.
    """
    if not challenge_id.startswith("user-"):
        raise HTTPException(status_code=400, detail="Suggestions are only available on user challenges.")

    source_id = to_inspiration_id(req.source_id)
    target_id = to_inspiration_id(req.target_id)
    if source_id == target_id:
        raise HTTPException(status_code=422, detail="Cannot suggest a self-loop relationship.")

    inspirations = await repo.get_inspirations_for_challenge(challenge_id)
    by_id = {i.id: i for i in inspirations}
    if source_id not in by_id or target_id not in by_id:
        raise HTTPException(status_code=404, detail="Source or target inspiration was not found on this challenge.")

    source_insp = by_id[source_id]
    target_insp = by_id[target_id]
    source_idea = {
        "id": source_id,
        "title": source_insp.name,
        "description": source_insp.description,
        "domain": source_insp.domain.value,
    }
    target_idea = {
        "id": target_id,
        "title": target_insp.name,
        "description": target_insp.description,
        "domain": target_insp.domain.value,
    }

    insp_map = {i.id: i.model_dump() for i in inspirations}
    if req.inspirations:
        for item in req.inspirations:
            if isinstance(item, dict) and item.get("id"):
                insp_map[item["id"]] = item

    graph = req.graph
    focus = [f"n-{source_id}", f"n-{target_id}", source_id, target_id]
    # Prefer node ids from provided graph when present
    if graph and graph.get("nodes"):
        focus = []
        for n in graph["nodes"]:
            if n.get("inspiration_id") in (source_id, target_id) or n.get("id") in (
                f"n-{source_id}",
                f"n-{target_id}",
                source_id,
                target_id,
            ):
                focus.append(n["id"])
        if not focus:
            focus = [f"n-{source_id}", f"n-{target_id}"]

    graph_context = build_semantic_graph_context(
        graph,
        focus,
        inspirations=insp_map,
        max_nodes=10,
    )

    try:
        raw = await granite_adapter.suggest_relationships(
            source_idea, target_idea, graph_context=graph_context
        )
        # Re-validate even if adapter already parsed (defense in depth)
        if isinstance(raw, RelationshipSuggestionResponse):
            result = raw
        else:
            result = RelationshipSuggestionResponse.model_validate(raw)
        logger.info(
            "Relationship suggestions ready challenge=%s count=%s (not persisted)",
            challenge_id,
            len(result.suggestions),
        )
        return result
    except ValueError as exc:
        logger.warning("Malformed Granite relationship suggestions: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Granite returned an unusable suggestion payload. Try again.",
        ) from exc
    except TimeoutError as exc:
        logger.warning("Granite relationship suggestion timed out")
        raise HTTPException(
            status_code=504,
            detail="Granite suggestion timed out. Try again.",
        ) from exc
    except Exception as exc:
        # Do not leak credentials / raw SDK internals
        logger.exception("Granite relationship suggestion failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Could not get relationship suggestions from Granite. Try again later.",
        ) from exc


@router.post("/challenges/{challenge_id}/edges", response_model=GraphEdge)
async def create_edge(challenge_id: str, edge_req: CreateEdgeRequest):
    if not challenge_id.startswith("user-"):
        raise HTTPException(status_code=400, detail="Cannot add edges to a curated challenge.")

    source_id = to_inspiration_id(edge_req.source_id)
    target_id = to_inspiration_id(edge_req.target_id)

    if source_id == target_id:
        raise HTTPException(
            status_code=422,
            detail="Cannot create a self-loop: source and target must differ.",
        )

    label = (edge_req.relationship_label or "").strip()
    if not label:
        raise HTTPException(status_code=422, detail="relationship_label is required.")

    inspirations = await repo.get_inspirations_for_challenge(challenge_id)
    insp_ids = {i.id for i in inspirations}
    if source_id not in insp_ids or target_id not in insp_ids:
        raise HTTPException(status_code=404, detail="Source or target inspiration was not found on this challenge.")

    existing_edges = await repo.get_edges_for_challenge(challenge_id)
    if edge_exists(existing_edges, source_id, target_id, edge_req.edge_type):
        raise HTTPException(
            status_code=409,
            detail="An equivalent relationship (same source, target, and type) already exists.",
        )

    derivation = edge_req.derivation
    evidence: list[str] = []
    if edge_req.from_ai_suggestion or derivation == DerivationLabel.AI_ACCEPTED:
        derivation = DerivationLabel.AI_ACCEPTED
        evidence.append("AI_SUGGESTION")
        if edge_req.suggestion_edited:
            evidence.append("USER_EDITED")

    edge = build_related_edge(
        challenge_id,
        source_inspiration_id=source_id,
        target_inspiration_id=target_id,
        edge_type=edge_req.edge_type,
        relationship_label=label,
        relationship_description=edge_req.relationship_description,
        transferable_insight=edge_req.transferable_insight,
        confidence=edge_req.confidence,
        derivation=derivation,
        evidence=evidence,
    )
    await repo.create_edge(challenge_id, edge)
    stored = await repo.get_edge(challenge_id, edge.id)
    return with_node_prefixed_ids(stored or edge)


@router.patch("/challenges/{challenge_id}/edges/{edge_id}", response_model=GraphEdge)
async def update_edge(challenge_id: str, edge_id: str, edge_req: UpdateEdgeRequest):
    if not challenge_id.startswith("user-"):
        raise HTTPException(status_code=400, detail="Cannot edit edges on a curated challenge.")

    existing = await repo.get_edge(challenge_id, edge_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Edge not found.")

    new_type = edge_req.edge_type if edge_req.edge_type is not None else existing.edge_type
    new_label = (
        edge_req.relationship_label.strip()
        if edge_req.relationship_label is not None
        else existing.relationship_label
    )
    if not new_label:
        raise HTTPException(status_code=422, detail="relationship_label cannot be empty.")

    if edge_req.edge_type is not None and edge_req.edge_type != existing.edge_type:
        all_edges = await repo.get_edges_for_challenge(challenge_id)
        if edge_exists(
            all_edges,
            existing.source_id,
            existing.target_id,
            new_type,
            exclude_edge_id=edge_id,
        ):
            raise HTTPException(
                status_code=409,
                detail="An equivalent relationship (same source, target, and type) already exists.",
            )

    updated = existing.model_copy(update={
        "edge_type": new_type,
        "relationship_label": new_label,
        "relationship_description": (
            edge_req.relationship_description
            if edge_req.relationship_description is not None
            else existing.relationship_description
        ),
        "transferable_insight": (
            edge_req.transferable_insight
            if edge_req.transferable_insight is not None
            else existing.transferable_insight
        ),
        "confidence": (
            edge_req.confidence if edge_req.confidence is not None else existing.confidence
        ),
        "weight": edge_req.weight if edge_req.weight is not None else existing.weight,
    })
    saved = await repo.update_edge(challenge_id, updated)
    if not saved:
        raise HTTPException(status_code=404, detail="Edge not found.")
    return with_node_prefixed_ids(saved)


@router.delete("/challenges/{challenge_id}/edges/{edge_id}", status_code=204)
async def delete_edge(challenge_id: str, edge_id: str):
    if not challenge_id.startswith("user-"):
        raise HTTPException(status_code=400, detail="Cannot delete edges on a curated challenge.")

    deleted = await repo.delete_edge(challenge_id, edge_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Edge not found.")
    return {}

@router.get("/challenges/{challenge_id}")
async def get_challenge(challenge_id: str):
    challenge = knowledge_base.get_challenge(challenge_id)
    if challenge:
        return challenge
    db_challenges = await repo.get_all_challenges()
    for db_challenge in db_challenges:
        if db_challenge.id == challenge_id:
            return db_challenge
    raise HTTPException(status_code=404, detail="Challenge not found")

@router.delete("/challenges/{challenge_id}", status_code=204)
async def delete_challenge(challenge_id: str):
    await repo.delete_challenge(challenge_id)
    return {}

@router.post("/graph/build")
async def build_graph(req: BuildGraphRequest):
    inspirations = []
    if req.challenge_id.startswith("user-"):
        inspirations = await repo.get_inspirations_for_challenge(req.challenge_id)
        # Backfill edges for challenges created while watsonx mode lacked structural generation
        existing_edges = await repo.get_edges_for_challenge(req.challenge_id)
        if inspirations and not existing_edges:
            generated = await granite_adapter.generate_edges(req.challenge_id, inspirations)
            for edge in generated:
                await repo.create_edge(req.challenge_id, edge)
    else:
        inspirations = knowledge_base.get_inspirations(req.challenge_id)

    graph = await graph_service.build_graph(req.challenge_id)

    default_constraints = {k.value: 0.5 for k in ConstraintKey}
    ds = design_system_service.generate_design_system(graph, default_constraints)
    return {"graph": graph, "inspirations": inspirations, "design_system": ds}

@router.post("/graph/apply-constraints")
async def apply_constraints(req: ApplyConstraintsRequest):
    modified_graph, effects = constraint_engine.apply_constraints(req.graph, req.constraints)
    ds = design_system_service.generate_design_system(modified_graph, req.constraints)
    return {"graph": modified_graph, "effects": effects, "design_system": ds}

@router.get("/design-system/{challenge_id}", response_model=DesignSystem)
async def get_design_system(challenge_id: str):
    graph = await graph_service.build_graph(challenge_id)
    default_constraints = {k.value: 0.5 for k in ConstraintKey}
    return design_system_service.generate_design_system(graph, default_constraints)

@router.post("/design-system/generate", response_model=DesignSystem)
async def generate_design_system(req: GenerateDesignSystemRequest):
    return design_system_service.generate_design_system(req.graph, req.constraints)

@router.post("/explain", response_model=ExplanationResponse)
async def explain(req: ExplanationRequest):
    return await explanation_service.explain(req)

@router.post("/explain/edge")
async def explain_edge(req: Dict[str, Any]):
    explanation_req = ExplanationRequest(target_type="edge", target_id=req.get("edge_id", ""), context=req)
    return await explanation_service.explain(explanation_req)

@router.post("/explain/design-decision")
async def explain_design_decision(req: Dict[str, Any]):
    explanation_req = ExplanationRequest(target_type="design_decision", target_id=req.get("decision", ""), context=req)
    return await explanation_service.explain(explanation_req)

@router.post("/explain/compare")
async def explain_compare(req: Dict[str, Any]):
    source = req.get("source") or {}
    target = req.get("target") or {}
    source_id = source.get("id") or req.get("source_id") or ""
    target_id = target.get("id") or req.get("target_id") or ""
    explanation_req = ExplanationRequest(
        target_type="compare",
        target_id=f"{source_id}:{target_id}",
        context=req,
    )
    return await explanation_service.explain(explanation_req)

@router.post("/explain/recommend")
async def explain_recommend(req: Dict[str, Any]):
    focus = req.get("focus_node_ids") or []
    target_id = focus[0] if focus else req.get("target_id", "recommend")
    explanation_req = ExplanationRequest(
        target_type="recommend",
        target_id=target_id,
        context=req,
    )
    return await explanation_service.explain(explanation_req)

class ExportRequestBody(BaseModel):
    challenge_id: str
    graph: ReasoningGraph
    constraints: ConstraintSet
    inspiration_ids: list[str] = []

@router.post("/export")
async def export_package(req: ExportRequestBody):
    ds = design_system_service.generate_design_system(req.graph, req.constraints)
    summary = await granite_adapter.generate_reasoning_summary(req.graph.model_dump(), req.constraints, ds.model_dump())
    
    all_inspirations = []
    if req.challenge_id.startswith("user-"):
        all_inspirations = await repo.get_inspirations_for_challenge(req.challenge_id)
    else:
        all_inspirations = knowledge_base.get_inspirations(req.challenge_id)

    if req.inspiration_ids:
        selected = [i for i in all_inspirations if i.id in req.inspiration_ids]
    else:
        selected = all_inspirations
        
    challenge = knowledge_base.get_challenge(req.challenge_id)
    if not challenge:
        db_challenges = await repo.get_all_challenges()
        for db_challenge in db_challenges:
            if db_challenge.id == req.challenge_id:
                challenge = db_challenge
                break
    challenge_name = challenge.name if challenge else req.challenge_id.replace("-", " ").title()
    return ExportPackage(
        challenge_name=challenge_name,
        design_tokens=ds,
        graph=req.graph,
        selected_inspirations=selected,
        constraints=req.constraints,
        reasoning_summary_markdown=summary,
    )
