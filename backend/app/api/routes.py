from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict
from pydantic import BaseModel
from app.data.knowledge_base import knowledge_base
from app.models.challenge import ChallengeListResponse
from app.models.graph import ReasoningGraph
from app.models.constraints import ConstraintSet, ConstraintKey
from app.models.design_system import DesignSystem
from app.models.export import ExportRequest, ExportPackage
from app.models.explanation import ExplanationRequest, ExplanationResponse
from app.services.graph_service import GraphService
from app.services.constraint_engine import ConstraintEngine
from app.services.design_system_service import DesignSystemService
from app.services.explanation_service import ExplanationService
from app.services.mock_granite import MockGraniteAdapter

router = APIRouter(prefix="/api")

graph_service = GraphService()
constraint_engine = ConstraintEngine()
design_system_service = DesignSystemService()
granite_adapter = MockGraniteAdapter()
explanation_service = ExplanationService(granite_adapter)

class BuildGraphRequest(BaseModel):
    challenge_id: str

class ApplyConstraintsRequest(BaseModel):
    graph: ReasoningGraph
    constraints: ConstraintSet

class GenerateDesignSystemRequest(BaseModel):
    graph: ReasoningGraph
    constraints: ConstraintSet

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/challenges", response_model=ChallengeListResponse)
async def list_challenges():
    challenges = knowledge_base.get_challenges()
    return {"challenges": challenges}

@router.get("/challenges/{challenge_id}")
async def get_challenge(challenge_id: str):
    challenge = knowledge_base.get_challenge(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

@router.post("/graph/build")
async def build_graph(req: BuildGraphRequest):
    graph = graph_service.build_graph(req.challenge_id)
    inspirations = knowledge_base.get_inspirations(req.challenge_id)
    # Also generate the initial design system with default constraints
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
    graph = graph_service.build_graph(challenge_id)
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
    explanation_req = ExplanationRequest(
        target_type="edge",
        target_id=req.get("edge_id", ""),
        context=req
    )
    return await explanation_service.explain(explanation_req)

@router.post("/explain/design-decision")
async def explain_design_decision(req: Dict[str, Any]):
    explanation_req = ExplanationRequest(
        target_type="design_decision",
        target_id=req.get("decision", ""),
        context=req
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
    summary = await granite_adapter.generate_reasoning_summary(
        req.graph.model_dump(), req.constraints, ds.model_dump()
    )
    inspirations = knowledge_base.get_inspirations(req.challenge_id)
    
    return ExportPackage(
        challenge_name=req.challenge_id.replace("-", " ").title(),
        design_tokens=ds,
        graph=req.graph,
        selected_inspirations=inspirations,
        constraints=req.constraints,
        reasoning_summary_markdown=summary
    )
