from app.models.explanation import (
    ExplanationRequest,
    ExplanationResponse,
    ExplanationChain,
    ReasoningStep,
    ReasoningPath,
)
from app.models.common import DerivationLabel
from app.services.granite_adapter import GraniteAdapter
from app.services.graph_context import (
    build_semantic_graph_context,
    relationship_label_for_edge,
    format_relationship_semantics_for_prompts,
)
from app.services.relationship_analysis import (
    MISSING_RELATIONSHIP_MESSAGE,
    analyze_comparison,
    analyze_node_relationships,
    analyze_recommendation_support,
    format_edge_evidence_line,
    provenance_phrase,
    paths_from_edges,
)


class ExplanationService:
    def __init__(self, granite_adapter: GraniteAdapter):
        self.granite_adapter = granite_adapter

    def _coerce_paths(self, raw_paths: list | None) -> list[ReasoningPath]:
        """Validate structured paths from relationship_analysis (no frontend recompute)."""
        if not raw_paths:
            return []
        result: list[ReasoningPath] = []
        for item in raw_paths:
            if not isinstance(item, dict):
                continue
            # Skip empty fabricated-looking payloads
            if not item.get("nodes") or not item.get("edges"):
                continue
            try:
                result.append(ReasoningPath.model_validate(item))
            except Exception:
                continue
        return result

    async def explain(self, request: ExplanationRequest) -> ExplanationResponse:
        if request.target_type == "edge":
            return await self._explain_edge(request)
        elif request.target_type == "node":
            return await self._explain_node(request)
        elif request.target_type == "compare":
            return await self._explain_compare(request)
        elif request.target_type == "recommend":
            return await self._explain_recommend(request)
        else:
            return await self._explain_design_decision(request)

    def _inspirations_map(self, context: dict) -> dict:
        inspirations = context.get("inspirations") or {}
        if isinstance(inspirations, list):
            return {i.get("id"): i for i in inspirations if isinstance(i, dict) and i.get("id")}
        if isinstance(inspirations, dict):
            return inspirations
        return {}

    def _renumber(self, *groups: list[ReasoningStep]) -> None:
        n = 1
        for group in groups:
            for step in group:
                step.step_number = n
                n += 1

    async def _explain_edge(self, request: ExplanationRequest) -> ExplanationResponse:
        source = request.context.get("source", {})
        target = request.context.get("target", {})
        edge = request.context.get("edge", {})
        graph = request.context.get("graph")

        source_label = source.get("label", source.get("id", "source"))
        target_label = target.get("label", target.get("id", "target"))
        edge_type = edge.get("edge_type", "connection")
        weight = edge.get("weight", 0)
        relationship_label = relationship_label_for_edge(edge)
        relationship = edge.get("relationship_description", "")
        insight = edge.get("transferable_insight", "")
        evidence = edge.get("evidence", [])
        confidence = edge.get("confidence")
        derivation = edge.get("derivation", "UNKNOWN")

        focus_ids = [source.get("id"), target.get("id")]
        graph_context = build_semantic_graph_context(
            graph,
            [fid for fid in focus_ids if fid],
            inspirations=self._inspirations_map(request.context),
        )

        comparison = analyze_comparison(
            graph or {
                "nodes": [source, target],
                "edges": [edge],
            },
            source.get("id") or "",
            target.get("id") or "",
        )

        retrieved = [
            ReasoningStep(
                step_number=1,
                description=(
                    f"Retrieved semantic relationship '{relationship_label}' "
                    f"('{source_label}' → '{target_label}', type: {edge_type}, "
                    f"derivation: {derivation}, weight: {weight:.2f}"
                    + (f", confidence: {confidence:.2f}" if isinstance(confidence, (int, float)) else "")
                    + f"). Reasoning evidence: {relationship or '(none provided)'}"
                ),
                derivation=DerivationLabel.RETRIEVED,
            ),
        ]
        provenance_note = f"Provenance: {provenance_phrase(str(derivation))}."
        if str(derivation).upper() == "MANUAL":
            provenance_note += " Manual edges are treated as user-authored evidence."
        elif str(derivation).upper() in ("AI", "AI_ACCEPTED"):
            provenance_note += " AI edges are treated as suggestions with provenance."
        retrieved.append(ReasoningStep(
            step_number=2,
            description=provenance_note,
            derivation=DerivationLabel.RETRIEVED,
        ))
        if evidence:
            retrieved.append(ReasoningStep(
                step_number=3,
                description=f"Evidence tags: {' | '.join(evidence)}",
                derivation=DerivationLabel.RETRIEVED,
            ))
        if comparison.get("indirect_paths"):
            retrieved.append(ReasoningStep(
                step_number=len(retrieved) + 1,
                description=(
                    "Indirect relationship path(s) between these ideas:\n"
                    + "\n".join(f"  • {p}" for p in comparison["indirect_paths"])
                ),
                derivation=DerivationLabel.RETRIEVED,
            ))
        elif comparison.get("direct_paths"):
            retrieved.append(ReasoningStep(
                step_number=len(retrieved) + 1,
                description="Direct path: " + comparison["direct_paths"][0],
                derivation=DerivationLabel.RETRIEVED,
            ))

        contradictions = comparison.get("contradictions") or []
        if contradictions:
            retrieved.append(ReasoningStep(
                step_number=len(retrieved) + 1,
                description="Surfaced contradictions:\n"
                + "\n".join(f"  • {c['description']}" for c in contradictions),
                derivation=DerivationLabel.RETRIEVED,
            ))

        if graph_context.get("edges"):
            retrieved.append(ReasoningStep(
                step_number=len(retrieved) + 1,
                description=(
                    f"Loaded {len(graph_context['nodes'])}-node / "
                    f"{len(graph_context['edges'])}-edge neighborhood for analysis "
                    f"(incoming+outgoing semantic relationships preserved)."
                ),
                derivation=DerivationLabel.RETRIEVED,
            ))

        deterministic = [
            ReasoningStep(
                step_number=len(retrieved) + 1,
                description=(
                    f"Edge weight {weight:.2f} retained as connection strength. "
                    f"Transferable insight: {insight or '(none)'}. "
                    f"Relationship semantics are not reduced to similarity."
                ),
                derivation=DerivationLabel.SYSTEM,
            ),
        ]
        if not relationship and not comparison.get("has_relationship"):
            deterministic.append(ReasoningStep(
                step_number=len(retrieved) + len(deterministic) + 1,
                description=MISSING_RELATIONSHIP_MESSAGE,
                derivation=DerivationLabel.SYSTEM,
            ))

        ai_insight = await self.granite_adapter.explain_relationship(
            source, target, edge, graph_context=graph_context
        )
        ai_steps = [
            ReasoningStep(
                step_number=len(retrieved) + len(deterministic) + 1,
                description=ai_insight,
                derivation=DerivationLabel.AI,
            )
        ]

        self._renumber(retrieved, deterministic, ai_steps)
        chain = ExplanationChain(
            retrieved_knowledge=retrieved,
            deterministic_reasoning=deterministic,
            ai_interpretation=ai_steps,
        )
        summary = ai_insight
        if comparison.get("direct_paths"):
            summary = f"{comparison['direct_paths'][0]} {ai_insight}"

        # Prefer comparison paths; ensure the focus edge itself is represented
        paths = self._coerce_paths(comparison.get("paths"))
        if not paths and edge:
            graph_for_edge = graph or {"nodes": [source, target], "edges": [edge]}
            paths = self._coerce_paths(paths_from_edges([edge], graph_for_edge))

        return ExplanationResponse(
            request=request, chain=chain, summary=summary, paths=paths
        )

    async def _explain_node(self, request: ExplanationRequest) -> ExplanationResponse:
        inspiration = request.context.get("inspiration", {})
        node = request.context.get("node") or {}
        graph = request.context.get("graph")
        node_name = inspiration.get("name") or node.get("label") or request.target_id
        domain = inspiration.get("domain") or node.get("domain") or "unknown"
        description = inspiration.get("description", "")
        principles = inspiration.get("key_principles", [])

        focus_id = node.get("id") or request.target_id
        graph_context = build_semantic_graph_context(
            graph,
            [focus_id] if focus_id else [],
            inspirations=self._inspirations_map(request.context),
        )
        analysis = analyze_node_relationships(graph, focus_id)

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

        retrieved.append(ReasoningStep(
            step_number=len(retrieved) + 1,
            description=analysis["prose"],
            derivation=DerivationLabel.RETRIEVED,
        ))

        deterministic = [
            ReasoningStep(
                step_number=len(retrieved) + 1,
                description=(
                    f"Node importance uses degree centrality across the reasoning graph "
                    f"(domain: {domain}). Conclusions must cite observed relationship labels "
                    f"and descriptions — not generic similarity."
                ),
                derivation=DerivationLabel.SYSTEM,
            ),
        ]
        if not analysis.get("has_relationships"):
            deterministic.append(ReasoningStep(
                step_number=len(retrieved) + len(deterministic) + 1,
                description=(
                    f"Fallback: {MISSING_RELATIONSHIP_MESSAGE} "
                    "Node interpretation relies on idea content alone."
                ),
                derivation=DerivationLabel.SYSTEM,
            ))
        else:
            out_lines = []
            for e in analysis.get("strongest_outgoing") or []:
                out_lines.append(
                    format_edge_evidence_line(
                        e, source_title=e["_source_title"], target_title=e["_target_title"]
                    )
                )
            in_lines = []
            for e in analysis.get("strongest_incoming") or []:
                in_lines.append(
                    format_edge_evidence_line(
                        e, source_title=e["_source_title"], target_title=e["_target_title"]
                    )
                )
            if out_lines or in_lines:
                deterministic.append(ReasoningStep(
                    step_number=len(retrieved) + len(deterministic) + 1,
                    description=(
                        "Strongest relationship citations for conclusions:\n"
                        + ("Outgoing:\n  • " + "\n  • ".join(out_lines) + "\n" if out_lines else "")
                        + ("Incoming:\n  • " + "\n  • ".join(in_lines) if in_lines else "")
                    ).strip(),
                    derivation=DerivationLabel.SYSTEM,
                ))

        decision = {
            **request.context,
            "inspiration": inspiration,
            "node": node or {"id": focus_id, "label": node_name, "domain": domain},
            "target_id": request.target_id,
        }
        ai_insight = await self.granite_adapter.explain_design_tradeoff(
            decision, request.context.get("constraints", {}), graph_context=graph_context
        )
        ai_steps = [
            ReasoningStep(
                step_number=len(retrieved) + len(deterministic) + 1,
                description=ai_insight,
                derivation=DerivationLabel.AI,
            )
        ]

        self._renumber(retrieved, deterministic, ai_steps)
        chain = ExplanationChain(
            retrieved_knowledge=retrieved,
            deterministic_reasoning=deterministic,
            ai_interpretation=ai_steps,
        )
        summary = analysis["prose"] + "\n\n" + ai_insight
        return ExplanationResponse(
            request=request,
            chain=chain,
            summary=summary,
            paths=self._coerce_paths(analysis.get("paths")),
        )

    async def _explain_compare(self, request: ExplanationRequest) -> ExplanationResponse:
        graph = request.context.get("graph")
        source = request.context.get("source") or request.context.get("node_a") or {}
        target = request.context.get("target") or request.context.get("node_b") or {}
        source_id = source.get("id") or request.context.get("source_id") or ""
        target_id = target.get("id") or request.context.get("target_id") or ""
        if (not source_id or not target_id) and ":" in (request.target_id or ""):
            parts = request.target_id.split(":", 1)
            source_id = source_id or parts[0]
            target_id = target_id or parts[1]

        comparison = analyze_comparison(graph, source_id, target_id)
        graph_context = build_semantic_graph_context(
            graph,
            [source_id, target_id],
            inspirations=self._inspirations_map(request.context),
        )

        retrieved = [
            ReasoningStep(
                step_number=1,
                description=comparison["prose"],
                derivation=DerivationLabel.RETRIEVED,
            )
        ]
        deterministic = [
            ReasoningStep(
                step_number=2,
                description=(
                    "Path analysis preserves directed human-readable labels "
                    "(e.g. builds on / contrasts with) and treats relationship_description "
                    "as reasoning evidence. Manual edges are user-authored; AI edges are "
                    "suggestions with provenance."
                    if comparison.get("has_relationship")
                    else MISSING_RELATIONSHIP_MESSAGE
                ),
                derivation=DerivationLabel.SYSTEM,
            )
        ]

        decision = {
            **request.context,
            "comparison": comparison,
            "source": source,
            "target": target,
            "mode": "compare",
        }
        ai_insight = await self.granite_adapter.explain_design_tradeoff(
            decision, request.context.get("constraints", {}), graph_context=graph_context
        )
        if not comparison.get("has_relationship"):
            ai_insight = (
                f"{MISSING_RELATIONSHIP_MESSAGE} "
                "Comparison is limited to idea content without an observed path."
            )

        ai_steps = [
            ReasoningStep(step_number=3, description=ai_insight, derivation=DerivationLabel.AI)
        ]
        self._renumber(retrieved, deterministic, ai_steps)
        return ExplanationResponse(
            request=request,
            chain=ExplanationChain(
                retrieved_knowledge=retrieved,
                deterministic_reasoning=deterministic,
                ai_interpretation=ai_steps,
            ),
            summary=comparison["prose"],
            paths=self._coerce_paths(comparison.get("paths")),
        )

    async def _explain_recommend(self, request: ExplanationRequest) -> ExplanationResponse:
        graph = request.context.get("graph") or {}
        focus = request.context.get("focus_node_ids") or []
        if not focus and request.context.get("node"):
            focus = [request.context["node"].get("id")]
        if not focus and request.target_id:
            focus = [request.target_id]

        support = analyze_recommendation_support(graph, focus)
        build_semantic_graph_context(
            graph,
            focus,
            inspirations=self._inspirations_map(request.context),
        )

        retrieved = [
            ReasoningStep(
                step_number=1,
                description=support["prose"],
                derivation=DerivationLabel.RETRIEVED,
            )
        ]
        deterministic = [
            ReasoningStep(
                step_number=2,
                description=(
                    "Recommendations must cite existing relationships as support. "
                    "Do not invent edges. Mark proposed next ideas as AI inference."
                    if support.get("has_support")
                    else (
                        "No supporting relationships found. "
                        + MISSING_RELATIONSHIP_MESSAGE
                    )
                ),
                derivation=DerivationLabel.SYSTEM,
            )
        ]

        alternatives = await self.granite_adapter.suggest_alternatives(
            graph, request.context.get("constraints", {})
        )
        if support.get("has_support"):
            cited = "; ".join(
                s["prose"] for s in support.get("supporting_relationships", [])[:3]
            )
            alt_text = (
                f"Recommended next directions (AI inference), supported by observed "
                f"relationships [{cited}]: "
            )
            for alt in alternatives[:2]:
                concept = alt.get("concept") or alt.get("id") or "alternative"
                alt_text += f" → {concept}."
            ai_insight = alt_text
        else:
            ai_insight = (
                "No meaningful existing relationships support a grounded recommendation. "
                "Any next idea would be unsupported speculation unless marked clearly as "
                "AI inference without claiming graph evidence."
            )
            if alternatives:
                ai_insight += (
                    " Tentative AI inference only (not backed by observed edges): "
                    + "; ".join(
                        a.get("concept") or a.get("id") or "idea" for a in alternatives[:2]
                    )
                    + "."
                )

        ai_steps = [
            ReasoningStep(step_number=3, description=ai_insight, derivation=DerivationLabel.AI)
        ]
        self._renumber(retrieved, deterministic, ai_steps)
        return ExplanationResponse(
            request=request,
            chain=ExplanationChain(
                retrieved_knowledge=retrieved,
                deterministic_reasoning=deterministic,
                ai_interpretation=ai_steps,
            ),
            summary=ai_insight,
            paths=self._coerce_paths(support.get("paths")),
        )

    async def _explain_design_decision(self, request: ExplanationRequest) -> ExplanationResponse:
        graph = request.context.get("graph")
        focus = request.context.get("node", {}).get("id") or request.target_id
        graph_context = build_semantic_graph_context(
            graph,
            [focus] if focus else [],
            inspirations=self._inspirations_map(request.context),
        )
        support = analyze_recommendation_support(graph, [focus] if focus else None)
        node_analysis = analyze_node_relationships(graph, focus) if focus else None
        semantics = format_relationship_semantics_for_prompts(
            graph,
            [focus] if focus else [],
            include_recommendation_support=True,
        )

        retrieved = [
            ReasoningStep(
                step_number=1,
                description=f"Retrieved design decision context for '{request.target_id}'.",
                derivation=DerivationLabel.RETRIEVED,
            ),
            ReasoningStep(
                step_number=2,
                description=semantics,
                derivation=DerivationLabel.RETRIEVED,
            ),
        ]

        deterministic = [
            ReasoningStep(
                step_number=3,
                description=(
                    "Applied constraint propagation: constraint values modulate "
                    "typography scale, colour palette, spacing unit, and WCAG level. "
                    "Semantic edge labels (not mere similarity) inform which relationships "
                    "remain creatively productive under the active constraints."
                ),
                derivation=DerivationLabel.SYSTEM,
            )
        ]
        if node_analysis and node_analysis.get("contradictions"):
            deterministic.append(ReasoningStep(
                step_number=4,
                description="Contradictions to weigh in the decision:\n"
                + "\n".join(
                    f"  • {c['description']}" for c in node_analysis["contradictions"]
                ),
                derivation=DerivationLabel.SYSTEM,
            ))

        ai_insight = await self.granite_adapter.explain_design_tradeoff(
            request.context,
            request.context.get("constraints", {}),
            graph_context=graph_context,
        )
        ai_steps = [
            ReasoningStep(step_number=5, description=ai_insight, derivation=DerivationLabel.AI)
        ]

        self._renumber(retrieved, deterministic, ai_steps)
        chain = ExplanationChain(
            retrieved_knowledge=retrieved,
            deterministic_reasoning=deterministic,
            ai_interpretation=ai_steps,
        )
        summary = ai_insight
        if support.get("has_support"):
            summary = support["prose"] + "\n\n" + ai_insight
        paths = self._coerce_paths(
            (node_analysis or {}).get("paths") or support.get("paths")
        )
        return ExplanationResponse(
            request=request, chain=chain, summary=summary, paths=paths
        )
