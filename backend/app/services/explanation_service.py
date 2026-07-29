from app.models.explanation import ExplanationRequest, ExplanationResponse, ExplanationChain, ReasoningStep
from app.models.common import DerivationLabel
from app.services.granite_adapter import GraniteAdapter


class ExplanationService:
    def __init__(self, granite_adapter: GraniteAdapter):
        self.granite_adapter = granite_adapter

    async def explain(self, request: ExplanationRequest) -> ExplanationResponse:
        if request.target_type == "edge":
            return await self._explain_edge(request)
        elif request.target_type == "node":
            return await self._explain_node(request)
        else:
            return await self._explain_design_decision(request)

    async def _explain_edge(self, request: ExplanationRequest) -> ExplanationResponse:
        source = request.context.get("source", {})
        target = request.context.get("target", {})
        edge = request.context.get("edge", {})

        source_label = source.get("label", source.get("id", "source"))
        target_label = target.get("label", target.get("id", "target"))
        edge_type = edge.get("edge_type", "connection")
        weight = edge.get("weight", 0)
        relationship = edge.get("relationship_description", "")
        insight = edge.get("transferable_insight", "")
        evidence = edge.get("evidence", [])

        retrieved = [
            ReasoningStep(
                step_number=1,
                description=(
                    f"Retrieved cross-domain edge: '{source_label}' → '{target_label}' "
                    f"(type: {edge_type}, weight: {weight:.2f}). "
                    f"Relationship: {relationship}"
                ),
                derivation=DerivationLabel.RETRIEVED,
            ),
        ]
        if evidence:
            retrieved.append(ReasoningStep(
                step_number=2,
                description=f"Evidence base: {' | '.join(evidence)}",
                derivation=DerivationLabel.RETRIEVED,
            ))

        deterministic = [
            ReasoningStep(
                step_number=3,
                description=(
                    f"Edge weight {weight:.2f} computed from domain centrality. "
                    f"Transferable insight: {insight}"
                ),
                derivation=DerivationLabel.SYSTEM,
            ),
        ]

        ai_insight = await self.granite_adapter.explain_relationship(source, target, edge)
        ai_steps = [
            ReasoningStep(step_number=4, description=ai_insight, derivation=DerivationLabel.AI)
        ]

        chain = ExplanationChain(
            retrieved_knowledge=retrieved,
            deterministic_reasoning=deterministic,
            ai_interpretation=ai_steps,
        )
        return ExplanationResponse(request=request, chain=chain, summary=ai_insight)

    async def _explain_node(self, request: ExplanationRequest) -> ExplanationResponse:
        inspiration = request.context.get("inspiration", {})
        node_name = inspiration.get("name", request.target_id)
        domain = inspiration.get("domain", "unknown")
        description = inspiration.get("description", "")
        principles = inspiration.get("key_principles", [])

        retrieved = [
            ReasoningStep(
                step_number=1,
                description=(
                    f"Loaded inspiration node '{node_name}' from the {domain} domain. "
                    f"{description}"
                ),
                derivation=DerivationLabel.RETRIEVED,
            ),
        ]
        if principles:
            principle_names = ", ".join(p.get("name", "") for p in principles[:3])
            retrieved.append(ReasoningStep(
                step_number=2,
                description=f"Key transferable principles: {principle_names}.",
                derivation=DerivationLabel.RETRIEVED,
            ))

        deterministic = [
            ReasoningStep(
                step_number=3,
                description=(
                    f"Node importance calculated via degree centrality across the "
                    f"reasoning graph. Domain: {domain}."
                ),
                derivation=DerivationLabel.SYSTEM,
            ),
        ]

        ai_insight = await self.granite_adapter.explain_design_tradeoff(
            request.context, {}
        )
        ai_steps = [
            ReasoningStep(step_number=4, description=ai_insight, derivation=DerivationLabel.AI)
        ]

        chain = ExplanationChain(
            retrieved_knowledge=retrieved,
            deterministic_reasoning=deterministic,
            ai_interpretation=ai_steps,
        )
        return ExplanationResponse(request=request, chain=chain, summary=ai_insight)

    async def _explain_design_decision(self, request: ExplanationRequest) -> ExplanationResponse:
        retrieved = [
            ReasoningStep(
                step_number=1,
                description=f"Retrieved design decision context for '{request.target_id}'.",
                derivation=DerivationLabel.RETRIEVED,
            )
        ]

        deterministic = [
            ReasoningStep(
                step_number=2,
                description=(
                    "Applied constraint propagation: constraint values directly modulate "
                    "typography scale, colour palette, spacing unit, and WCAG compliance level."
                ),
                derivation=DerivationLabel.SYSTEM,
            )
        ]

        ai_insight = await self.granite_adapter.explain_design_tradeoff(
            request.context, request.context.get("constraints", {})
        )
        ai_steps = [
            ReasoningStep(step_number=3, description=ai_insight, derivation=DerivationLabel.AI)
        ]

        chain = ExplanationChain(
            retrieved_knowledge=retrieved,
            deterministic_reasoning=deterministic,
            ai_interpretation=ai_steps,
        )
        return ExplanationResponse(request=request, chain=chain, summary=ai_insight)
