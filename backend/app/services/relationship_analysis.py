"""
Deterministic semantic relationship analysis for explanations and Granite prompts.

Produces human-readable relationship prose, strongest in/out rankings, path
discovery, contradiction detection, and provenance-aware evidence blocks.
Never invents relationships — missing links are stated explicitly.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from app.services.graph_context import relationship_label_for_edge

# Edge types that imply tension / opposition
CONTRASTIVE_TYPES = frozenset({"contrast", "opposition"})
# Edge types that imply alignment / support (not mere similarity)
SUPPORTIVE_TYPES = frozenset({
    "support",
    "extension",
    "refinement",
    "dependency",
    "inspired_by",
    "combination",
    "reference",
    "transferable_principle",
})
# Labels that also signal contrast / support when type is missing or generic
CONTRASTIVE_LABEL_HINTS = frozenset({
    "contrasts with",
    "opposes",
    "tensions",
    "conflicts with",
    "productively opposes",
})
SUPPORTIVE_LABEL_HINTS = frozenset({
    "supports",
    "builds on",
    "refines",
    "depends on",
    "inspired by",
    "composed of",
    "references",
})

MISSING_RELATIONSHIP_MESSAGE = (
    "No meaningful semantic relationship is recorded between these ideas in the graph. "
    "Do not invent one."
)

AUTHORITATIVE_DERIVATIONS = frozenset({"MANUAL", "SYSTEM", "CURATED", "AI_ACCEPTED"})


@dataclass
class PathHop:
    source_id: str
    target_id: str
    source_title: str
    target_title: str
    relationship_label: str
    relationship_description: str
    derivation: str
    edge_type: str
    edge_id: str | None = None
    weight: float = 0.5
    confidence: float | None = None


@dataclass
class RelationshipPath:
    hops: list[PathHop] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.hops)


@dataclass
class Contradiction:
    description: str
    edge_a_id: str | None
    edge_b_id: str | None
    labels: tuple[str, str]


def _node_title(node: dict[str, Any] | None, fallback: str = "untitled") -> str:
    if not node:
        return fallback
    return (
        node.get("title")
        or node.get("label")
        or node.get("name")
        or node.get("id")
        or fallback
    )


def _edge_endpoints(edge: dict[str, Any]) -> tuple[str | None, str | None]:
    return (
        edge.get("source_id") or edge.get("source"),
        edge.get("target_id") or edge.get("target"),
    )


def _index_nodes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {n["id"]: n for n in graph.get("nodes", []) if isinstance(n, dict) and n.get("id")}


def _normalize_id(nid: str | None, nodes_by_id: dict[str, dict[str, Any]]) -> str | None:
    if not nid:
        return None
    if nid in nodes_by_id:
        return nid
    prefixed = f"n-{nid}"
    if prefixed in nodes_by_id:
        return prefixed
    if nid.startswith("n-") and nid[2:] in nodes_by_id:
        return nid[2:]
    # Match by inspiration_id
    for node_id, node in nodes_by_id.items():
        if node.get("inspiration_id") == nid or node.get("inspiration_id") == nid.removeprefix("n-"):
            return node_id
    return nid


def provenance_phrase(derivation: str | None) -> str:
    d = (derivation or "UNKNOWN").upper()
    return {
        "MANUAL": "user-authored evidence",
        "SYSTEM": "system-recorded relationship",
        "CURATED": "curated knowledge-base relationship",
        "AI": "AI suggestion (not yet accepted)",
        "AI_ACCEPTED": "accepted AI suggestion (user-confirmed)",
        "RETRIEVED": "retrieved knowledge",
    }.get(d, f"relationship with provenance {d}")


def is_contrastive(edge: dict[str, Any]) -> bool:
    et = str(edge.get("edge_type") or "").lower()
    if et in CONTRASTIVE_TYPES:
        return True
    label = relationship_label_for_edge(edge).lower()
    return any(h in label for h in CONTRASTIVE_LABEL_HINTS)


def is_supportive(edge: dict[str, Any]) -> bool:
    et = str(edge.get("edge_type") or "").lower()
    if et in SUPPORTIVE_TYPES:
        return True
    label = relationship_label_for_edge(edge).lower()
    return any(h in label for h in SUPPORTIVE_LABEL_HINTS)


def edge_strength(edge: dict[str, Any]) -> float:
    """Rank edges for 'strongest' selection — never flattens to similarity alone."""
    weight = float(edge.get("weight") or 0.5)
    conf = edge.get("confidence")
    if isinstance(conf, (int, float)):
        conf_factor = 0.55 + 0.45 * float(conf)
    else:
        conf_factor = 0.75

    derivation = str(edge.get("derivation") or "").upper()
    authority = {
        "MANUAL": 1.15,
        "SYSTEM": 1.05,
        "CURATED": 1.0,
        "AI_ACCEPTED": 1.05,
        "AI": 0.75,
        "RETRIEVED": 0.9,
    }.get(derivation, 0.85)

    # Prefer specific semantics over generic similarity
    et = str(edge.get("edge_type") or "").lower()
    specificity = 1.0
    if et in ("similarity", "functional_similarity", "visual_similarity"):
        specificity = 0.85
    elif is_contrastive(edge) or is_supportive(edge):
        specificity = 1.1

    return weight * conf_factor * authority * specificity


def format_directed_clause(
    source_title: str,
    relationship_label: str,
    target_title: str,
) -> str:
    label = (relationship_label or "relates to").strip()
    # Mid-sentence: lowercase first letter unless it looks like an acronym
    if label and label[0].isupper() and not label.isupper():
        label_mid = label[0].lower() + label[1:]
    else:
        label_mid = label
    return f"{source_title} {label_mid} {target_title}"


def format_path_prose(path: RelationshipPath) -> str:
    """
    Human-readable multi-hop path, e.g.:
    'Idea A builds on Idea B, which contrasts with Idea C.'
    """
    if not path.hops:
        return MISSING_RELATIONSHIP_MESSAGE
    first = path.hops[0]
    parts = [
        format_directed_clause(
            first.source_title, first.relationship_label, first.target_title
        )
    ]
    for hop in path.hops[1:]:
        label = hop.relationship_label.strip()
        if label and label[0].isupper() and not label.isupper():
            label_mid = label[0].lower() + label[1:]
        else:
            label_mid = label or "relates to"
        parts.append(f"which {label_mid} {hop.target_title}")
    return ", ".join(parts) + "."


def serialize_reasoning_path(path: RelationshipPath) -> dict[str, Any]:
    """
    Structured path payload for explain API + frontend visualization.
    Preserves directed hop order; never invents nodes/edges.
    """
    if not path.hops:
        return {
            "nodes": [],
            "edges": [],
            "prose": MISSING_RELATIONSHIP_MESSAGE,
        }

    nodes: list[dict[str, str]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()

    first = path.hops[0]
    nodes.append({"id": first.source_id, "title": first.source_title})
    seen_nodes.add(first.source_id)

    for hop in path.hops:
        edges.append({
            "id": hop.edge_id,
            "source": hop.source_id,
            "target": hop.target_id,
            "relationship_label": hop.relationship_label,
            "relationship_description": hop.relationship_description,
            "derivation": hop.derivation,
            "confidence": hop.confidence,
        })
        if hop.target_id not in seen_nodes:
            nodes.append({"id": hop.target_id, "title": hop.target_title})
            seen_nodes.add(hop.target_id)
        elif hop.source_id not in seen_nodes:
            # Rare undirected case: ensure both endpoints present
            nodes.append({"id": hop.source_id, "title": hop.source_title})
            seen_nodes.add(hop.source_id)

    return {
        "nodes": nodes,
        "edges": edges,
        "prose": format_path_prose(path),
    }


def paths_from_edges(
    edges: list[dict[str, Any]],
    graph: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert observed edges into 1-hop structured paths (no fabrication)."""
    nodes_by_id = _index_nodes(graph)
    result: list[dict[str, Any]] = []
    for edge in edges:
        hop = _hop_from_edge(edge, nodes_by_id)
        if not hop:
            continue
        result.append(serialize_reasoning_path(RelationshipPath(hops=[hop])))
    return result


def format_edge_evidence_line(
    edge: dict[str, Any],
    *,
    source_title: str,
    target_title: str,
) -> str:
    label = relationship_label_for_edge(edge)
    derivation = edge.get("derivation") or "UNKNOWN"
    desc = (edge.get("relationship_description") or "").strip()
    clause = format_directed_clause(source_title, label, target_title)
    line = f"{clause} [{provenance_phrase(str(derivation))}]"
    if desc:
        line += f" Reasoning evidence: {desc}"
    conf = edge.get("confidence")
    if isinstance(conf, (int, float)) and str(derivation).upper() in ("AI", "AI_ACCEPTED"):
        line += f" (confidence {conf:.2f})"
    return line


def _hop_from_edge(
    edge: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
) -> PathHop | None:
    src, tgt = _edge_endpoints(edge)
    if not src or not tgt:
        return None
    return PathHop(
        source_id=src,
        target_id=tgt,
        source_title=_node_title(nodes_by_id.get(src), src),
        target_title=_node_title(nodes_by_id.get(tgt), tgt),
        relationship_label=relationship_label_for_edge(edge),
        relationship_description=(edge.get("relationship_description") or "").strip(),
        derivation=str(edge.get("derivation") or "UNKNOWN"),
        edge_type=str(edge.get("edge_type") or ""),
        edge_id=edge.get("id"),
        weight=float(edge.get("weight") or 0.5),
        confidence=edge.get("confidence") if isinstance(edge.get("confidence"), (int, float)) else None,
    )


def strongest_incident_edges(
    graph: dict[str, Any],
    node_id: str,
    *,
    direction: str = "both",
    limit: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """
    Return strongest incoming and/or outgoing edges for a node.
    direction: 'incoming' | 'outgoing' | 'both'
    """
    nodes_by_id = _index_nodes(graph)
    nid = _normalize_id(node_id, nodes_by_id) or node_id
    incoming: list[tuple[float, dict[str, Any]]] = []
    outgoing: list[tuple[float, dict[str, Any]]] = []

    for edge in graph.get("edges", []):
        src, tgt = _edge_endpoints(edge)
        if not src or not tgt:
            continue
        strength = edge_strength(edge)
        enriched = {
            **edge,
            "relationship_label": relationship_label_for_edge(edge),
            "_strength": strength,
            "_source_title": _node_title(nodes_by_id.get(src), src),
            "_target_title": _node_title(nodes_by_id.get(tgt), tgt),
        }
        if tgt == nid and direction in ("incoming", "both"):
            incoming.append((strength, enriched))
        if src == nid and direction in ("outgoing", "both"):
            outgoing.append((strength, enriched))

    incoming.sort(key=lambda x: -x[0])
    outgoing.sort(key=lambda x: -x[0])
    return {
        "incoming": [e for _, e in incoming[:limit]],
        "outgoing": [e for _, e in outgoing[:limit]],
    }


def find_paths(
    graph: dict[str, Any],
    source_id: str,
    target_id: str,
    *,
    max_hops: int = 3,
    max_paths: int = 5,
) -> list[RelationshipPath]:
    """
    Find directed paths from source → target (direct and multi-hop).
    Also searches reverse direction as separate paths if no forward path exists,
    then undirected exploration for indirect connectivity (preserving hop direction).
    """
    nodes_by_id = _index_nodes(graph)
    src = _normalize_id(source_id, nodes_by_id) or source_id
    tgt = _normalize_id(target_id, nodes_by_id) or target_id
    if src == tgt:
        return []

    # Adjacency: directed
    out_adj: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.get("edges", []):
        s, t = _edge_endpoints(edge)
        if s and t and s in nodes_by_id and t in nodes_by_id:
            out_adj[s].append(edge)

    def bfs_directed(start: str, end: str) -> list[RelationshipPath]:
        paths: list[RelationshipPath] = []
        queue: deque[tuple[str, list[dict[str, Any]]]] = deque([(start, [])])
        # Track visited edges per path exploration
        while queue and len(paths) < max_paths:
            current, edge_chain = queue.popleft()
            if len(edge_chain) >= max_hops:
                continue
            for edge in out_adj.get(current, []):
                _, next_id = _edge_endpoints(edge)
                if not next_id or next_id == current:
                    continue
                # Avoid cycles
                visited_nodes = {start}
                for e in edge_chain:
                    es, et = _edge_endpoints(e)
                    if et:
                        visited_nodes.add(et)
                if next_id in visited_nodes:
                    continue
                new_chain = edge_chain + [edge]
                if next_id == end:
                    hops = [_hop_from_edge(e, nodes_by_id) for e in new_chain]
                    hops = [h for h in hops if h]
                    if hops:
                        paths.append(RelationshipPath(hops=hops))
                else:
                    queue.append((next_id, new_chain))
        return paths

    forward = bfs_directed(src, tgt)
    if forward:
        return forward[:max_paths]

    reverse = bfs_directed(tgt, src)
    # Annotate reverse by returning as-is (direction preserved in hops)
    if reverse:
        return reverse[:max_paths]

    # Undirected: allow traversing edges in either direction for indirect links
    undirected_adj: dict[str, list[tuple[dict[str, Any], str]]] = defaultdict(list)
    for edge in graph.get("edges", []):
        s, t = _edge_endpoints(edge)
        if s and t and s in nodes_by_id and t in nodes_by_id:
            undirected_adj[s].append((edge, t))
            undirected_adj[t].append((edge, s))

    paths: list[RelationshipPath] = []
    queue2: deque[tuple[str, list[dict[str, Any]]]] = deque([(src, [])])
    while queue2 and len(paths) < max_paths:
        current, edge_chain = queue2.popleft()
        if len(edge_chain) >= max_hops:
            continue
        for edge, next_id in undirected_adj.get(current, []):
            if next_id == current:
                continue
            visited = {src}
            for e in edge_chain:
                # track both ends
                es, et = _edge_endpoints(e)
                if es:
                    visited.add(es)
                if et:
                    visited.add(et)
            if next_id in visited:
                continue
            new_chain = edge_chain + [edge]
            if next_id == tgt:
                hops = []
                cursor = src
                for e in new_chain:
                    es, et = _edge_endpoints(e)
                    hop = _hop_from_edge(e, nodes_by_id)
                    if not hop:
                        continue
                    # Orient hop along traversal
                    if es == cursor:
                        hops.append(hop)
                        cursor = et or cursor
                    else:
                        # Traversed against arrow — still report true edge direction in prose
                        hops.append(hop)
                        cursor = es or cursor
                if hops:
                    paths.append(RelationshipPath(hops=hops))
            else:
                queue2.append((next_id, new_chain))
    return paths[:max_paths]


def find_contradictions(
    graph: dict[str, Any],
    focus_node_ids: Iterable[str] | None = None,
) -> list[Contradiction]:
    """
    Detect opposing semantics on the same node pair (e.g. Supports vs Contrasts with).
    """
    nodes_by_id = _index_nodes(graph)
    focus = set()
    if focus_node_ids:
        for fid in focus_node_ids:
            nid = _normalize_id(fid, nodes_by_id)
            if nid:
                focus.add(nid)

    # Group edges by undirected pair
    pairs: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.get("edges", []):
        src, tgt = _edge_endpoints(edge)
        if not src or not tgt or src == tgt:
            continue
        if focus and src not in focus and tgt not in focus:
            continue
        key = tuple(sorted((src, tgt)))
        pairs[key].append(edge)

    contradictions: list[Contradiction] = []
    for (a, b), edges in pairs.items():
        supportive = [e for e in edges if is_supportive(e)]
        contrastive = [e for e in edges if is_contrastive(e)]
        if not supportive or not contrastive:
            continue
        e_sup = max(supportive, key=edge_strength)
        e_con = max(contrastive, key=edge_strength)
        a_title = _node_title(nodes_by_id.get(a), a)
        b_title = _node_title(nodes_by_id.get(b), b)
        lab_sup = relationship_label_for_edge(e_sup)
        lab_con = relationship_label_for_edge(e_con)
        contradictions.append(
            Contradiction(
                description=(
                    f"Contradiction between '{a_title}' and '{b_title}': "
                    f"one relationship says '{lab_sup}' while another says '{lab_con}'."
                ),
                edge_a_id=e_sup.get("id"),
                edge_b_id=e_con.get("id"),
                labels=(lab_sup, lab_con),
            )
        )
    return contradictions


def analyze_node_relationships(
    graph: dict[str, Any] | None,
    node_id: str,
    *,
    limit: int = 3,
) -> dict[str, Any]:
    """Structured analysis used by node explanations and prompts."""
    if not graph or not node_id:
        return {
            "node_id": node_id,
            "has_relationships": False,
            "strongest_incoming": [],
            "strongest_outgoing": [],
            "paths": [],
            "contradictions": [],
            "summary_lines": [MISSING_RELATIONSHIP_MESSAGE],
            "prose": MISSING_RELATIONSHIP_MESSAGE,
        }

    nodes_by_id = _index_nodes(graph)
    nid = _normalize_id(node_id, nodes_by_id) or node_id
    node_title = _node_title(nodes_by_id.get(nid), nid)
    ranked = strongest_incident_edges(graph, nid, limit=limit)
    incoming = ranked["incoming"]
    outgoing = ranked["outgoing"]
    contradictions = find_contradictions(graph, [nid])
    # Structured paths from strongest observed edges only (outgoing then incoming)
    paths = paths_from_edges(outgoing + incoming, graph)

    lines: list[str] = []
    if outgoing:
        lines.append(f"Strongest outgoing relationships from {node_title}:")
        for e in outgoing:
            lines.append(
                "  • "
                + format_edge_evidence_line(
                    e, source_title=e["_source_title"], target_title=e["_target_title"]
                )
            )
    if incoming:
        lines.append(f"Strongest incoming relationships to {node_title}:")
        for e in incoming:
            lines.append(
                "  • "
                + format_edge_evidence_line(
                    e, source_title=e["_source_title"], target_title=e["_target_title"]
                )
            )
    if not incoming and not outgoing:
        lines.append(
            f"No meaningful semantic relationships are recorded for '{node_title}'. "
            "Do not invent connections."
        )
    for c in contradictions:
        lines.append(f"⚠ {c.description}")

    return {
        "node_id": nid,
        "node_title": node_title,
        "has_relationships": bool(incoming or outgoing),
        "strongest_incoming": incoming,
        "strongest_outgoing": outgoing,
        "paths": paths,
        "contradictions": [
            {"description": c.description, "labels": list(c.labels)} for c in contradictions
        ],
        "summary_lines": lines,
        "prose": "\n".join(lines),
    }


def analyze_comparison(
    graph: dict[str, Any] | None,
    source_id: str,
    target_id: str,
    *,
    max_hops: int = 3,
) -> dict[str, Any]:
    """Direct + indirect paths between two nodes with contradiction notes."""
    if not graph:
        return {
            "has_relationship": False,
            "direct_paths": [],
            "indirect_paths": [],
            "paths": [],
            "contradictions": [],
            "summary_lines": [MISSING_RELATIONSHIP_MESSAGE],
            "prose": MISSING_RELATIONSHIP_MESSAGE,
        }

    nodes_by_id = _index_nodes(graph)
    src = _normalize_id(source_id, nodes_by_id) or source_id
    tgt = _normalize_id(target_id, nodes_by_id) or target_id
    src_title = _node_title(nodes_by_id.get(src), src)
    tgt_title = _node_title(nodes_by_id.get(tgt), tgt)

    paths = find_paths(graph, src, tgt, max_hops=max_hops)
    direct = [p for p in paths if p.length == 1]
    indirect = [p for p in paths if p.length > 1]
    contradictions = find_contradictions(graph, [src, tgt])

    lines: list[str] = [f"Comparing '{src_title}' and '{tgt_title}':"]
    if direct:
        lines.append("Direct relationship path(s):")
        for p in direct:
            lines.append(f"  • {format_path_prose(p)}")
            hop = p.hops[0]
            if hop.relationship_description:
                lines.append(f"    Reasoning evidence: {hop.relationship_description}")
            lines.append(f"    Provenance: {provenance_phrase(hop.derivation)}")
    if indirect:
        lines.append("Indirect relationship path(s):")
        for p in indirect:
            lines.append(f"  • {format_path_prose(p)}")
            for hop in p.hops:
                if hop.relationship_description:
                    lines.append(
                        f"    Via {hop.source_title}→{hop.target_title}: "
                        f"{hop.relationship_description} "
                        f"[{provenance_phrase(hop.derivation)}]"
                    )
    if not direct and not indirect:
        lines.append(MISSING_RELATIONSHIP_MESSAGE)
    for c in contradictions:
        lines.append(f"⚠ {c.description}")

    return {
        "source_id": src,
        "target_id": tgt,
        "source_title": src_title,
        "target_title": tgt_title,
        "has_relationship": bool(direct or indirect),
        "direct_paths": [format_path_prose(p) for p in direct],
        "indirect_paths": [format_path_prose(p) for p in indirect],
        "paths": [serialize_reasoning_path(p) for p in paths],
        "path_details": [
            {
                "length": p.length,
                "prose": format_path_prose(p),
                "hops": [
                    {
                        "source_id": h.source_id,
                        "target_id": h.target_id,
                        "source": h.source_title,
                        "target": h.target_title,
                        "edge_id": h.edge_id,
                        "label": h.relationship_label,
                        "description": h.relationship_description,
                        "derivation": h.derivation,
                        "confidence": h.confidence,
                    }
                    for h in p.hops
                ],
            }
            for p in paths
        ],
        "contradictions": [
            {"description": c.description, "labels": list(c.labels)} for c in contradictions
        ],
        "summary_lines": lines,
        "prose": "\n".join(lines),
    }


def analyze_recommendation_support(
    graph: dict[str, Any] | None,
    focus_node_ids: Iterable[str] | None = None,
    *,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Identify existing relationships that can support a 'next idea' recommendation.
    Does not invent edges — only cites recorded ones.
    """
    if not graph or not graph.get("edges"):
        return {
            "supporting_relationships": [],
            "paths": [],
            "has_support": False,
            "summary_lines": [
                "No existing semantic relationships are available to support a recommendation. "
                "Any suggested next idea must be marked as AI inference, not as an observed edge."
            ],
            "prose": (
                "No existing semantic relationships are available to support a recommendation. "
                "Any suggested next idea must be marked as AI inference, not as an observed edge."
            ),
        }

    nodes_by_id = _index_nodes(graph)
    focus = set()
    if focus_node_ids:
        for fid in focus_node_ids:
            nid = _normalize_id(fid, nodes_by_id)
            if nid:
                focus.add(nid)

    scored: list[tuple[float, dict[str, Any]]] = []
    for edge in graph.get("edges", []):
        src, tgt = _edge_endpoints(edge)
        if not src or not tgt:
            continue
        if focus and src not in focus and tgt not in focus:
            continue
        # Prefer supportive / specific edges for recommendations
        if str(edge.get("edge_type") or "").lower() in (
            "similarity",
            "functional_similarity",
            "visual_similarity",
        ) and not (edge.get("relationship_label") or "").strip():
            continue
        strength = edge_strength(edge)
        scored.append((strength, edge))

    scored.sort(key=lambda x: -x[0])
    top = [e for _, e in scored[:limit]]

    lines = [
        "Existing relationships that can support a next-idea recommendation "
        "(observed only — do not invent new edges):"
    ]
    supporting = []
    for e in top:
        src, tgt = _edge_endpoints(e)
        src_title = _node_title(nodes_by_id.get(src or ""), src or "?")
        tgt_title = _node_title(nodes_by_id.get(tgt or ""), tgt or "?")
        line = format_edge_evidence_line(e, source_title=src_title, target_title=tgt_title)
        lines.append(f"  • {line}")
        supporting.append({
            "prose": format_directed_clause(
                src_title, relationship_label_for_edge(e), tgt_title
            ),
            "relationship_label": relationship_label_for_edge(e),
            "relationship_description": e.get("relationship_description") or "",
            "derivation": e.get("derivation"),
            "source_title": src_title,
            "target_title": tgt_title,
        })

    if not supporting:
        lines = [
            "No specific supportive relationships found among focus ideas. "
            "Do not fabricate edges to justify a recommendation."
        ]

    contradictions = find_contradictions(graph, focus or None)
    for c in contradictions:
        lines.append(f"⚠ {c.description}")

    return {
        "supporting_relationships": supporting,
        "paths": paths_from_edges(top, graph),
        "has_support": bool(supporting),
        "contradictions": [
            {"description": c.description, "labels": list(c.labels)} for c in contradictions
        ],
        "summary_lines": lines,
        "prose": "\n".join(lines),
    }


def format_relationship_semantics_block(
    *,
    node_analysis: dict[str, Any] | None = None,
    comparison: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
) -> str:
    """
    Reusable prose block shared by deterministic explanations and Granite prompts.
    """
    sections: list[str] = ["## Observed relationship semantics"]
    if node_analysis:
        sections.append(node_analysis.get("prose") or MISSING_RELATIONSHIP_MESSAGE)
    if comparison:
        sections.append(comparison.get("prose") or MISSING_RELATIONSHIP_MESSAGE)
    if recommendation:
        sections.append(recommendation.get("prose") or MISSING_RELATIONSHIP_MESSAGE)
    if len(sections) == 1:
        sections.append(MISSING_RELATIONSHIP_MESSAGE)
    return "\n\n".join(sections)
