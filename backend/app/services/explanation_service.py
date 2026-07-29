from app.models.explanation import ExplanationRequest, ExplanationResponse, ExplanationChain, ReasoningStep
from app.models.common import DerivationLabel
from app.services.granite_adapter import GraniteAdapter

class ExplanationService:
    def __init__(self, granite_adapter: GraniteAdapter):
        self.granite_adapter = granite_adapter
        
    async def explain(self, request: ExplanationRequest) -> ExplanationResponse:
        retrieved = [
            ReasoningStep(step_number=1, description=f"Retrieved context for {request.target_type} {request.target_id}.", derivation=DerivationLabel.RETRIEVED)
        ]
        
        deterministic = [
            ReasoningStep(step_number=2, description="Applied constraints and base reasoning heuristics.", derivation=DerivationLabel.SYSTEM)
        ]
        
        if request.target_type == "edge":
            source = request.context.get("source", {})
            target = request.context.get("target", {})
            edge = request.context.get("edge", {})
            ai_insight = await self.granite_adapter.explain_relationship(source, target, edge)
        else:
            ai_insight = await self.granite_adapter.explain_design_tradeoff(request.context, request.context.get("constraints", {}))
            
        ai_steps = [
            ReasoningStep(step_number=3, description=ai_insight, derivation=DerivationLabel.AI)
        ]
        
        chain = ExplanationChain(
            retrieved_knowledge=retrieved,
            deterministic_reasoning=deterministic,
            ai_interpretation=ai_steps
        )
        
        return ExplanationResponse(
            request=request,
            chain=chain,
            summary=ai_insight
        )
