"""
Semantic graph context for IBM Granite prompts.

Serializes a focused subgraph (nodes + directed semantic edges) so Granite
reasons over relationship meaning — not adjacency or flat idea lists.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Optional


FALLBACK_RELATIONSHIP_LABEL = "Related to"

_GRAPH_REASONING_INSTRUCTIONS = (
    "You are analyzing a creative reasoning graph.\n"
    "Nodes contain ideas.\n"
    "Edges contain explicit semantic relationships between ideas.\n"
    "Use edge labels and relationship descriptions as reasoning evidence.\n"
    "Do not reduce every relationship to mere similarity — preserve specific semantics "
    "such as builds on, contrasts with, supports, refines, depends on, inspired by.\n"
    "Do not infer that two ideas are related merely because they are nearby in the graph.\n"
    "Treat manually created edges (derivation MANUAL) as intentional user-authored evidence.\n"
    "Treat system/context edges (derivation SYSTEM) and curated edges (CURATED) as "
    "authoritative recorded relationships.\n"
    "Treat AI-generated edges (derivation AI) as suggestions with provenance; note confidence.\n"
    "Treat accepted AI edges (derivation AI_ACCEPTED) as user-confirmed suggestions — "
    "still AI-origin, but approved.\n"
    "When explaining or recommending ideas, cite the observed relationships that support "
    "the conclusion. If recommending a next idea, explain which existing relationships "
    "support it — do not invent edges.\n"
    "When comparing ideas, identify direct and indirect relationship paths using "
    "human-readable labels (e.g. \"Idea A builds on Idea B, which contrasts with Idea C.\").\n"
    "Surface contradictions when present (e.g. one edge says Supports while another "
    "says Contrasts with).\n"
    "Preserve edge direction: \"A builds on B\" is not the same as \"B builds on A\".\n"
    "In your response, clearly distinguish:\n"
    "  (1) observed user-authored or system-recorded relationships from the graph,\n"
    "  (2) your AI inference,\n"
    "  (3) unsupported speculation.\n"
    "If no meaningful relationship exists in the graph, say so explicitly — "
    "do not invent one.\n"
)


def relationship_label_for_edge(edge: dict[str, Any]) -> str:
    """Safe display label for old edges missing relationship_label."""
    label = (edge.get("relationship_label") or "").strip()
    if label:
        return label
    edge_type = (edge.get("edge_type") or "").strip()
    if edge_type:
        # Prefer humanized type only as last resort before generic fallback
        humanized = edge_type.replace("_", " ").strip()
        if humanized:
            # Map common types to friendlier defaults when label missing
            defaults = {
                "extension": "Builds on",
                "inspired_by": "Inspired by",
                "similarity": "Related to",
                "functional_similarity": "Related to",
                "refinement": "Refines",
                "contrast": "Contrasts with",
            }
            return defaults.get(edge_type, FALLBACK_RELATIONSHIP_LABEL)
    return FALLBACK_RELATIONSHIP_LABEL


def _node_title(node: dict[str, Any]) -> str:
    return (
        node.get("title")
        or node.get("label")
        or node.get("name")
        or node.get("id")
        or "untitled"
    )


def serialize_node(
    node: dict[str, Any],
    *,
    inspiration: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    insp = inspiration or {}
    description = (
        node.get("description")
        or insp.get("description")
        or ""
    )
    metadata: dict[str, Any] = {}
    for key in ("domain", "importance", "derivation", "inspiration_id"):
        if node.get(key) is not None:
            metadata[key] = node[key]
    if insp.get("domain") and "domain" not in metadata:
        metadata["domain"] = insp["domain"]
    if insp.get("derivation") and "derivation" not in metadata:
        metadata["derivation"] = insp["derivation"]
    if insp.get("key_principles"):
        metadata["key_principles"] = [
            p.get("name") for p in insp["key_principles"][:4] if isinstance(p, dict) and p.get("name")
        ]

    payload: dict[str, Any] = {
        "id": node.get("id") or insp.get("id"),
        "title": _node_title(node) if node else (insp.get("name") or insp.get("id")),
        "description": description,
    }
    if metadata:
        payload["metadata"] = metadata

    # Incoming / outgoing filled by neighborhood builder
    payload["incoming_relationships"] = []
    payload["outgoing_relationships"] = []
    return payload


def serialize_edge(edge: dict[str, Any]) -> dict[str, Any]:
    confidence = edge.get("confidence")
    evidence = edge.get("evidence") or []
    return {
        "id": edge.get("id"),
        "source": edge.get("source_id") or edge.get("source"),
        "target": edge.get("target_id") or edge.get("target"),
        "relationship_label": relationship_label_for_edge(edge),
        "relationship_description": edge.get("relationship_description") or "",
        "edge_type": edge.get("edge_type"),
        "derivation": edge.get("derivation") or "UNKNOWN",
        "confidence": confidence if isinstance(confidence, (int, float)) else None,
        "weight": float(edge.get("weight") or 0.5),
        "transferable_insight": edge.get("transferable_insight") or "",
        "evidence": list(evidence) if isinstance(evidence, list) else [],
    }


def _index_nodes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {n["id"]: n for n in graph.get("nodes", []) if n.get("id")}


def _edge_endpoints(edge: dict[str, Any]) -> tuple[str | None, str | None]:
    return (
        edge.get("source_id") or edge.get("source"),
        edge.get("target_id") or edge.get("target"),
    )


def select_neighborhood_node_ids(
    graph: dict[str, Any],
    focus_node_ids: Iterable[str],
    *,
    max_nodes: int = 12,
) -> set[str]:
    """
    Focus nodes + 1-hop neighbors via directed edges.
    Unrelated nodes are excluded. Caps size for token budget.
    """
    focus = {nid for nid in focus_node_ids if nid}
    if not focus:
        return set()

    nodes_by_id = _index_nodes(graph)
    included = set(focus)
    neighbor_candidates: list[tuple[float, str]] = []

    for edge in graph.get("edges", []):
        src, tgt = _edge_endpoints(edge)
        if not src or not tgt:
            continue
        if src in focus and tgt in nodes_by_id:
            neighbor_candidates.append((float(nodes_by_id[tgt].get("importance") or 0), tgt))
        if tgt in focus and src in nodes_by_id:
            neighbor_candidates.append((float(nodes_by_id[src].get("importance") or 0), src))

    # Highest-importance neighbors first when capping
    for _, nid in sorted(neighbor_candidates, key=lambda x: -x[0]):
        if len(included) >= max_nodes:
            break
        included.add(nid)

    # Always keep focus even if over cap
    return included | focus


def build_semantic_graph_context(
    graph: dict[str, Any] | None,
    focus_node_ids: Iterable[str],
    *,
    inspirations: Optional[dict[str, dict[str, Any]]] = None,
    max_nodes: int = 12,
) -> dict[str, Any]:
    """
    Build a JSON-serializable subgraph centered on focus nodes.

    Includes:
      - focused nodes (+ 1-hop neighbors)
      - directed edges among those nodes only
      - per-node incoming/outgoing relationship summaries
    """
    if not graph:
        return {"nodes": [], "edges": [], "focus_node_ids": list(focus_node_ids)}

    inspirations = inspirations or {}
    nodes_by_id = _index_nodes(graph)
    included_ids = select_neighborhood_node_ids(graph, focus_node_ids, max_nodes=max_nodes)

    # Map inspiration_id → node for enrichment lookups
    node_by_insp: dict[str, dict[str, Any]] = {}
    for n in nodes_by_id.values():
        insp_id = n.get("inspiration_id")
        if insp_id:
            node_by_insp[insp_id] = n

    serialized_nodes: dict[str, dict[str, Any]] = {}
    for nid in included_ids:
        node = nodes_by_id.get(nid)
        if not node:
            continue
        insp = inspirations.get(nid) or inspirations.get(node.get("inspiration_id", ""))
        serialized_nodes[nid] = serialize_node(node, inspiration=insp)

    serialized_edges: list[dict[str, Any]] = []
    for edge in graph.get("edges", []):
        src, tgt = _edge_endpoints(edge)
        if not src or not tgt:
            continue
        if src not in included_ids or tgt not in included_ids:
            continue
        se = serialize_edge(edge)
        serialized_edges.append(se)
        # Lazy import avoids circular dependency at module load
        from app.services.relationship_analysis import edge_strength

        strength = edge_strength(edge)
        rel_summary = {
            "direction": "outgoing",
            "other_node_id": tgt,
            "other_title": serialized_nodes.get(tgt, {}).get("title", tgt),
            "relationship_label": se["relationship_label"],
            "relationship_description": se["relationship_description"],
            "derivation": se["derivation"],
            "confidence": se["confidence"],
            "weight": se["weight"],
            "strength": strength,
            "evidence": se.get("evidence") or [],
        }
        if src in serialized_nodes:
            serialized_nodes[src]["outgoing_relationships"].append(rel_summary)
        incoming = {
            **rel_summary,
            "direction": "incoming",
            "other_node_id": src,
            "other_title": serialized_nodes.get(src, {}).get("title", src),
        }
        if tgt in serialized_nodes:
            serialized_nodes[tgt]["incoming_relationships"].append(incoming)

    # Rank strongest relationships first on each node
    for node in serialized_nodes.values():
        node["outgoing_relationships"].sort(key=lambda r: -float(r.get("strength") or 0))
        node["incoming_relationships"].sort(key=lambda r: -float(r.get("strength") or 0))

    return {
        "focus_node_ids": [nid for nid in focus_node_ids if nid in included_ids],
        "nodes": list(serialized_nodes.values()),
        "edges": serialized_edges,
        "_source_graph": graph,
    }


def format_graph_context_block(graph_context: dict[str, Any] | None) -> str:
    """Pretty JSON block for embedding in prompts (omits internal _source_graph)."""
    if not graph_context:
        return "{}"
    safe = {k: v for k, v in graph_context.items() if not str(k).startswith("_")}
    return json.dumps(safe, indent=2, ensure_ascii=False, default=str)


def format_relationship_semantics_for_prompts(
    graph: dict[str, Any] | None,
    focus_node_ids: Iterable[str],
    *,
    compare_pair: tuple[str, str] | None = None,
    include_recommendation_support: bool = False,
) -> str:
    """
    Reusable human-readable relationship semantics block for Granite and
    deterministic explanation chains. Consistent wording across both.
    """
    from app.services.relationship_analysis import (
        analyze_comparison,
        analyze_node_relationships,
        analyze_recommendation_support,
        format_relationship_semantics_block,
    )

    focus = [fid for fid in focus_node_ids if fid]
    node_analysis = None
    comparison = None
    recommendation = None

    if len(focus) == 1:
        node_analysis = analyze_node_relationships(graph, focus[0])
    elif len(focus) >= 2 and compare_pair is None:
        # Multi-focus: summarize each focus node briefly + pairwise first two
        node_analysis = analyze_node_relationships(graph, focus[0])
        comparison = analyze_comparison(graph, focus[0], focus[1])
    if compare_pair:
        comparison = analyze_comparison(graph, compare_pair[0], compare_pair[1])
    if include_recommendation_support:
        recommendation = analyze_recommendation_support(graph, focus or None)

    return format_relationship_semantics_block(
        node_analysis=node_analysis,
        comparison=comparison,
        recommendation=recommendation,
    )


def build_graph_reasoning_preamble() -> str:
    return _GRAPH_REASONING_INSTRUCTIONS


def build_relationship_prompt(
    source: dict[str, Any],
    target: dict[str, Any],
    edge: dict[str, Any],
    graph_context: dict[str, Any] | None = None,
) -> str:
    source_name = _node_title(source)
    target_name = _node_title(target)
    label = relationship_label_for_edge(edge)
    derivation = edge.get("derivation") or "UNKNOWN"
    confidence = edge.get("confidence")
    conf_text = (
        f"{confidence:.2f}" if isinstance(confidence, (int, float)) else "null"
    )

    ctx = graph_context
    if ctx is None:
        # Minimal 2-node context when caller omitted the graph
        ctx = {
            "focus_node_ids": [source.get("id"), target.get("id")],
            "nodes": [
                serialize_node(source),
                serialize_node(target),
            ],
            "edges": [serialize_edge(edge)],
        }
        # Attach direction summaries
        se = ctx["edges"][0]
        ctx["nodes"][0]["outgoing_relationships"] = [{
            "direction": "outgoing",
            "other_node_id": se["target"],
            "other_title": target_name,
            "relationship_label": label,
            "relationship_description": se["relationship_description"],
            "derivation": se["derivation"],
            "confidence": se["confidence"],
        }]
        ctx["nodes"][1]["incoming_relationships"] = [{
            "direction": "incoming",
            "other_node_id": se["source"],
            "other_title": source_name,
            "relationship_label": label,
            "relationship_description": se["relationship_description"],
            "derivation": se["derivation"],
            "confidence": se["confidence"],
        }]

    # Prefer full graph for path analysis when present in context
    analysis_graph = None
    if graph_context and graph_context.get("_source_graph"):
        analysis_graph = graph_context["_source_graph"]
    elif graph_context and graph_context.get("nodes") and graph_context.get("edges"):
        # Reconstruct a minimal graph from context
        analysis_graph = {
            "nodes": [
                {
                    "id": n.get("id"),
                    "label": n.get("title"),
                    "importance": (n.get("metadata") or {}).get("importance"),
                }
                for n in graph_context.get("nodes", [])
                if n.get("id")
            ],
            "edges": [
                {
                    "id": e.get("id"),
                    "source_id": e.get("source"),
                    "target_id": e.get("target"),
                    "relationship_label": e.get("relationship_label"),
                    "relationship_description": e.get("relationship_description"),
                    "edge_type": e.get("edge_type"),
                    "derivation": e.get("derivation"),
                    "confidence": e.get("confidence"),
                    "weight": e.get("weight", 0.5),
                    "evidence": e.get("evidence") or [],
                }
                for e in graph_context.get("edges", [])
            ],
        }

    semantics = format_relationship_semantics_for_prompts(
        analysis_graph,
        [source.get("id"), target.get("id")],
        compare_pair=(source.get("id") or "", target.get("id") or ""),
    )

    return (
        f"{build_graph_reasoning_preamble()}\n"
        f"Focus relationship under analysis:\n"
        f"  {source_name} --[{label}]--> {target_name}\n"
        f"  derivation={derivation}, confidence={conf_text}\n"
        f"  reasoning evidence: {edge.get('relationship_description') or '(none provided)'}\n"
        f"  transferable insight: {edge.get('transferable_insight') or '(none)'}\n\n"
        f"{semantics}\n\n"
        f"Relevant subgraph (JSON):\n{format_graph_context_block(ctx)}\n\n"
        f"Explain why this semantic relationship is creatively productive for interface design. "
        f"Ground your answer in the observed relationship and neighboring graph context. "
        f"Use human-readable relationship labels; do not flatten to 'similar'. "
        f"Surface any contradictions. Mark any additional ideas you introduce as AI inference. "
        f"If no meaningful supporting path exists beyond this edge, say so."
    )


def build_node_tradeoff_prompt(
    decision: dict[str, Any],
    constraints: dict[str, Any],
    graph_context: dict[str, Any] | None = None,
) -> str:
    inspiration = decision.get("inspiration", {})
    node = decision.get("node") or {}
    node_name = (
        inspiration.get("name")
        or node.get("label")
        or decision.get("target_id")
        or "this design element"
    )
    domain = inspiration.get("domain") or node.get("domain") or ""
    description = inspiration.get("description") or node.get("description") or ""

    active_c = {k: v for k, v in constraints.items() if isinstance(v, (int, float))}
    constraint_prose = ", ".join(
        f"{k.replace('_', ' ')} at {v:.0%}" for k, v in active_c.items()
    ) if active_c else "default balanced constraints"

    ctx_block = ""
    semantics = ""
    if graph_context and (graph_context.get("nodes") or graph_context.get("edges")):
        ctx_block = (
            f"\nRelevant subgraph around this idea (JSON):\n"
            f"{format_graph_context_block(graph_context)}\n"
        )
        analysis_graph = graph_context.get("_source_graph") or {
            "nodes": [
                {"id": n.get("id"), "label": n.get("title")}
                for n in graph_context.get("nodes", [])
                if n.get("id")
            ],
            "edges": [
                {
                    "id": e.get("id"),
                    "source_id": e.get("source"),
                    "target_id": e.get("target"),
                    "relationship_label": e.get("relationship_label"),
                    "relationship_description": e.get("relationship_description"),
                    "edge_type": e.get("edge_type"),
                    "derivation": e.get("derivation"),
                    "confidence": e.get("confidence"),
                    "weight": e.get("weight", 0.5),
                }
                for e in graph_context.get("edges", [])
            ],
        }
        focus = graph_context.get("focus_node_ids") or [node.get("id")]
        semantics = (
            "\n"
            + format_relationship_semantics_for_prompts(analysis_graph, focus)
            + "\n"
        )

    return (
        f"{build_graph_reasoning_preamble()}\n"
        f"Focus idea: {node_name}"
        + (f" ({domain} domain)" if domain else "")
        + ".\n"
        + (f"Idea content: {description}\n" if description else "")
        + f"Current design constraints: {constraint_prose}.\n"
        + semantics
        + ctx_block
        + "\nExplain what this idea teaches about interface design. "
        "Include the strongest incoming and outgoing relationships when present. "
        "Treat relationship_description as reasoning evidence. "
        "Cite manual edges as user-authored evidence and AI edges as suggestions with provenance. "
        "Surface contradictions. Use only relationships present in the subgraph unless marked as AI inference. "
        "If no meaningful relationships exist, say so — do not invent them."
    )


def build_reasoning_summary_prompt(
    graph: dict[str, Any],
    constraints: dict[str, Any],
    design_system: dict[str, Any],
    *,
    max_nodes: int = 10,
) -> str:
    """Compact semantic summary context — top nodes by importance + their edges."""
    nodes = sorted(
        graph.get("nodes", []),
        key=lambda n: float(n.get("importance") or 0),
        reverse=True,
    )
    focus_ids = [n["id"] for n in nodes[:max_nodes] if n.get("id")]
    ctx = build_semantic_graph_context(graph, focus_ids, max_nodes=max_nodes)

    active_c = {k: v for k, v in constraints.items() if isinstance(v, (int, float))}
    constraint_prose = ", ".join(
        f"{k.replace('_', ' ')} {v:.0%}" for k, v in active_c.items()
    ) if active_c else "balanced defaults"
    wcag = design_system.get("wcag_level", "AA")

    return (
        f"{build_graph_reasoning_preamble()}\n"
        f"A creative reasoning session produced the following design system.\n"
        f"Constraint configuration: {constraint_prose}.\n"
        f"Resulting WCAG level: {wcag}.\n\n"
        f"Semantic reasoning graph (JSON):\n{format_graph_context_block(ctx)}\n\n"
        f"Write a concise Markdown reasoning summary (use ## headings, no bullet lists) "
        f"that explains the creative logic. Cover how idea content AND semantic "
        f"relationships (labels/direction) shaped the design philosophy. "
        f"Distinguish observed graph relationships from AI inference. "
        f"Do not reproduce numerical token values."
    )


def build_alternatives_prompt(
    graph: dict[str, Any],
    constraints: dict[str, Any],
    *,
    max_nodes: int = 8,
) -> str:
    nodes = sorted(
        graph.get("nodes", []),
        key=lambda n: float(n.get("importance") or 0),
        reverse=True,
    )
    focus_ids = [n["id"] for n in nodes[:max_nodes] if n.get("id")]
    ctx = build_semantic_graph_context(graph, focus_ids, max_nodes=max_nodes)
    active = ", ".join(
        f"{k}={v:.1f}" for k, v in constraints.items() if isinstance(v, float)
    )
    semantics = format_relationship_semantics_for_prompts(
        graph,
        focus_ids,
        include_recommendation_support=True,
    )
    return (
        f"{build_graph_reasoning_preamble()}\n"
        f"Active constraints: {active}.\n"
        f"{semantics}\n\n"
        f"Current semantic subgraph (JSON):\n{format_graph_context_block(ctx)}\n\n"
        f"Recommend one or two unexplored next ideas. For each recommendation, explain "
        f"which EXISTING relationships support it (cite labels and reasoning evidence). "
        f"Do not invent that those supporting edges already exist if they do not. "
        f"Mark the recommended idea itself as AI inference. "
        f"If no meaningful relationships exist to ground a recommendation, say so."
    )


def build_weak_analogy_prompt(edges: list[dict[str, Any]]) -> str:
    summaries = []
    for e in edges[:8]:
        label = relationship_label_for_edge(e)
        src = e.get("source_id") or e.get("source") or "?"
        tgt = e.get("target_id") or e.get("target") or "?"
        summaries.append(
            f"{src} --[{label}]--> {tgt} "
            f"(derivation={e.get('derivation', '?')}, type={e.get('edge_type', '?')})"
        )
    joined = "; ".join(summaries) if summaries else "(none)"
    return (
        f"{build_graph_reasoning_preamble()}\n"
        f"Review these directed semantic relationships: {joined}.\n\n"
        f"Which relationships risk being superficial for design purposes? "
        f"Respect each relationship's label and direction; do not flatten them to mere adjacency."
    )
