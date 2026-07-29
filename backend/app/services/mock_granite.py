"""
MockGraniteAdapter
==================
Offline fallback that mirrors the contract of WatsonXGraniteAdapter.

All responses are clearly interpretive prose — no numerical values, no
weights, no token specifications.  Used when USE_MOCK_GRANITE=True (default).

Each method's response demonstrates what real Granite would return so the
UI provenance labels remain semantically accurate in development.
"""

from typing import Any

from app.services.granite_adapter import GraniteAdapter


class MockGraniteAdapter(GraniteAdapter):

    async def extract_principles(
        self, inspiration_description: str, target_domain: str
    ) -> list[str]:
        return [
            (
                f"The key transferable principle from this inspiration to the "
                f"{target_domain} domain is layered temporal organisation: "
                f"grouping information by natural rhythm rather than arbitrary "
                f"categories reduces the cognitive burden on the user."
            ),
            (
                "A second principle is phase-aware presentation — the interface "
                "should adapt its level of detail to match the user's current "
                "cognitive mode, showing more when attention is at its peak and "
                "simplifying during fatigue-prone periods."
            ),
        ]

    async def explain_relationship(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
        edge: dict[str, Any],
    ) -> str:
        source_name = source.get("label") or source.get("name", "the source concept")
        target_name = target.get("label") or target.get("name", "the target concept")
        edge_type = edge.get("edge_type", "connection").replace("_", " ")

        if edge_type == "functional similarity":
            return (
                f"Both {source_name} and {target_name} solve the same underlying "
                f"problem: communicating critical state to a user who cannot afford "
                f"to consciously process every detail. The shared mechanism — "
                f"encoding urgency through redundant visual channels — is precisely "
                f"what makes this analogy actionable for interface design. "
                f"Rather than borrowing aesthetics, this connection borrows a "
                f"decision-making architecture that has been validated under "
                f"real-world stress conditions."
            )
        if edge_type == "structural analogy":
            return (
                f"The structural parallel between {source_name} and {target_name} "
                f"runs deeper than appearance. Both systems impose a mathematical "
                f"order on complexity — one through spatial organisation, the other "
                f"through typographic hierarchy — and in doing so they allow users "
                f"to build reliable mental models. When exceptions break the pattern, "
                f"they are immediately perceptible because the pattern itself was "
                f"consistent enough to be internalised."
            )
        if edge_type == "behavioral analogy":
            return (
                f"The connection between {source_name} and {target_name} operates "
                f"at the level of human behaviour rather than visual form. Both "
                f"exploit pre-attentive processing — the part of perception that "
                f"operates before conscious thought. Designing with this analogy "
                f"means engineering for reflexive responses, not just aesthetic "
                f"appreciation, which is essential in high-stakes contexts."
            )
        return (
            f"The link between {source_name} and {target_name} reveals a "
            f"transferable principle that transcends both domains: when a system "
            f"must guide users through complexity without overwhelming them, the "
            f"most effective strategy is progressive revelation — presenting "
            f"information in layers that match the user's current decision context. "
            f"This principle applies equally whether the medium is a hospital "
            f"corridor, a garden path, or a data dashboard."
        )

    async def suggest_alternatives(
        self,
        graph: dict[str, Any],
        constraints: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "mock-alt-1",
                "concept": (
                    "Musical notation systems — particularly the way a conductor's "
                    "score encodes simultaneous temporal streams at different levels "
                    "of abstraction — could enrich the dashboard's approach to "
                    "multi-patient monitoring. Each patient becomes a 'voice' in a "
                    "larger composition, with the interface surfacing ensemble-level "
                    "patterns rather than forcing clinicians to aggregate data manually."
                ),
                "derivation": "AI",
            }
        ]

    async def identify_weak_analogies(
        self,
        edges: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "critique": (
                    "The visual similarity connections in this graph carry the most "
                    "risk of being superficial. A shared aesthetic quality (e.g., "
                    "both systems use colour gradients) does not imply a shared "
                    "cognitive mechanism. Designers should interrogate whether the "
                    "underlying information architecture of the source domain is "
                    "genuinely analogous to the target, not just whether the two "
                    "things look similar."
                ),
                "derivation": "AI",
            }
        ]

    async def explain_design_tradeoff(
        self,
        decision: dict[str, Any],
        constraints: dict[str, Any],
    ) -> str:
        inspiration = decision.get("inspiration", {})
        node_name = (
            inspiration.get("name")
            or decision.get("target_id")
            or "this design element"
        )
        domain = inspiration.get("domain", "")
        domain_clause = f" from the {domain} domain" if domain else ""

        active_c = {
            k: v for k, v in constraints.items() if isinstance(v, (int, float))
        }
        if not active_c:
            constraint_clause = "balanced defaults"
        else:
            highest = max(active_c, key=lambda k: active_c[k])
            constraint_clause = (
                f"with {highest.replace('_', ' ')} as the dominant constraint"
            )

        return (
            f"The inspiration '{node_name}'{domain_clause} teaches that clarity "
            f"under cognitive load is not achieved through reduction alone — it "
            f"requires a principled hierarchy where the most critical information "
            f"is always at the surface, and supporting context is available on "
            f"demand. Applied {constraint_clause}, this means the interface should "
            f"reserve visual emphasis for genuine anomalies, treating the "
            f"'everything normal' state as an invisible baseline rather than a "
            f"canvas for decoration. The tradeoff is between information density "
            f"and immediate legibility: the current constraint configuration "
            f"resolves this by privileging legibility at the top level and "
            f"permitting density only in deliberate drill-down contexts."
        )

    async def generate_reasoning_summary(
        self,
        graph: dict[str, Any],
        constraints: dict[str, Any],
        design_system: dict[str, Any],
    ) -> str:
        node_labels = [
            n.get("label", n.get("id", "?")) for n in graph.get("nodes", [])
        ][:5]
        top_nodes = ", ".join(node_labels)
        wcag = design_system.get("wcag_level", "AA")

        return (
            f"## Design Reasoning Summary\n\n"
            f"This session assembled a reasoning graph from {len(graph.get('nodes', []))} "
            f"cross-domain inspirations including {top_nodes}. "
            f"The graph connects concepts through functional similarities, structural "
            f"analogies, and behavioural parallels — each edge representing a "
            f"transferable principle rather than a surface aesthetic match.\n\n"
            f"## Constraint Philosophy\n\n"
            f"The active constraints shaped the graph's topology by amplifying edges "
            f"connected to high-relevance nodes and attenuating those linked to "
            f"lower-priority concepts. This is a deterministic process: the "
            f"constraint engine applies documented mathematical rules, not AI "
            f"inference, to every edge weight. The result is a system where "
            f"design decisions are traceable to explicit constraint values.\n\n"
            f"## Accessibility & Token Derivation\n\n"
            f"The design system achieved WCAG {wcag} compliance through constraint "
            f"propagation rather than post-hoc correction. Typography scale, colour "
            f"contrast, and spacing were derived directly from constraint arithmetic, "
            f"ensuring that accessibility is baked into the system's generative logic "
            f"rather than applied as a remediation layer. Every token carries a "
            f"[SYSTEM] provenance tag confirming its deterministic origin."
        )
