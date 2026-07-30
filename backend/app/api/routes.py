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
from app.models.graph import ReasoningGraph, GraphEdge
from app.models.inspiration import Inspiration
from app.models.constraints import ConstraintSet, ConstraintKey
from app.models.design_system import DesignSystem
from app.models.export import ExportPackage
from app.models.explanation import ExplanationRequest, ExplanationResponse
from app.services.graph_service import GraphService
from app.services.constraint_engine import ConstraintEngine
from app.services.design_system_service import DesignSystemService
from app.services.explanation_service import ExplanationService

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

class AddInspirationResponse(BaseModel):
    inspiration: Inspiration
    new_edges: list[GraphEdge]

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
    
    new_edges = await granite_adapter.generate_edges_for_new_inspiration(challenge_id, new_inspiration, existing_inspirations)
    
    for edge in new_edges:
        await repo.create_edge(challenge_id, edge)
        
    return AddInspirationResponse(inspiration=new_inspiration, new_edges=new_edges)

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
    graph = await graph_service.build_graph(req.challenge_id)
    
    inspirations = []
    if req.challenge_id.startswith("user-"):
        inspirations = await repo.get_inspirations_for_challenge(req.challenge_id)
    else:
        inspirations = knowledge_base.get_inspirations(req.challenge_id)

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
