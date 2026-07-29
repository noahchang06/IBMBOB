"""
WatsonXGraniteAdapter
=====================
Real IBM Granite integration via the ibm-watsonx-ai SDK.

Granite's SOLE responsibility is qualitative interpretation:
  - explaining cross-domain analogies
  - summarising reasoning chains
  - critiquing transferability of principles
  - describing design implications

Granite MUST NOT:
  - produce numerical scores or weights
  - generate graph structure or edge definitions
  - create design tokens or CSS values
  - override or validate deterministic engine outputs

Every response from this class is tagged [AI] at the call site.
All [CURATED] / [SYSTEM] / [RETRIEVED] data is assembled before
Granite is invoked and is never modified by the AI response.
"""

from __future__ import annotations

import logging
from typing import Any

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from app.services.granite_adapter import GraniteAdapter
from app.config import settings

logger = logging.getLogger(__name__)

# ── Generation parameters ─────────────────────────────────────────────────────
# Kept conservative: deterministic outputs stay in the engine;
# Granite only produces interpretive prose.
_GEN_PARAMS: dict[str, Any] = {
    GenParams.MAX_NEW_TOKENS: 350,
    GenParams.MIN_NEW_TOKENS: 40,
    GenParams.TEMPERATURE: 0.4,
    GenParams.TOP_P: 0.9,
    GenParams.REPETITION_PENALTY: 1.15,
    GenParams.STOP_SEQUENCES: ["\n\n\n"],
}

# ── System instruction prepended to every prompt ─────────────────────────────
_SYSTEM_PREAMBLE = (
    "You are a creative reasoning assistant embedded inside a design system platform. "
    "Your role is strictly interpretive: explain analogies, summarise connections, "
    "and describe implications in clear, professional prose. "
    "You must NEVER produce numerical scores, weights, CSS values, or code. "
    "Respond with one or two focused paragraphs. Do not use bullet lists or headers.\n\n"
)


def _extract_text(response: dict[str, Any]) -> str:
    """Pull the generated_text string out of the raw agenerate() response dict."""
    try:
        return response["results"][0]["generated_text"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("Unexpected Granite response shape: %s — %s", response, exc)
        return "IBM Granite did not return a usable response."


class WatsonXGraniteAdapter(GraniteAdapter):
    """
    Production IBM Granite adapter.

    Requires three environment variables (set in .env or shell):
      GRANITE_API_URL     — e.g. https://us-south.ml.cloud.ibm.com
      GRANITE_API_KEY     — IBM Cloud API key
      WATSONX_PROJECT_ID  — watsonx.ai project ID
      GRANITE_MODEL_ID    — defaults to ibm/granite-13b-instruct-v2
    """

    def __init__(self) -> None:
        credentials = Credentials(
            url=settings.GRANITE_API_URL,
            api_key=settings.GRANITE_API_KEY,
        )
        self._model = ModelInference(
            model_id=settings.GRANITE_MODEL_ID,
            credentials=credentials,
            project_id=settings.WATSONX_PROJECT_ID,
            params=_GEN_PARAMS,
            validate=False,          # skip online model-list check at startup
        )

    async def _call(self, prompt: str) -> str:
        """Send a single prompt asynchronously; extract and return the text."""
        response = await self._model.agenerate(
            prompt=_SYSTEM_PREAMBLE + prompt,
        )
        return _extract_text(response)

    # ── GraniteAdapter interface ──────────────────────────────────────────────

    async def extract_principles(
        self, inspiration_description: str, target_domain: str
    ) -> list[str]:
        """
        Ask Granite to articulate transferable principles in plain English.
        Returns a list so callers can render each principle as a separate item.
        """
        prompt = (
            f"The following inspiration comes from outside the {target_domain} domain.\n\n"
            f"Inspiration: {inspiration_description}\n\n"
            f"Identify and explain the two or three most transferable design principles "
            f"from this inspiration that could improve a {target_domain} experience. "
            f"Focus on conceptual insights, not implementation details."
        )
        text = await self._call(prompt)
        # Split on sentence boundaries for the list; caller can join if needed
        sentences = [s.strip() for s in text.split(". ") if s.strip()]
        return sentences or [text]

    async def explain_relationship(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
        edge: dict[str, Any],
    ) -> str:
        """
        Explain WHY two inspirations are connected and what makes the analogy
        creatively valuable.  Does NOT alter the edge weight (that is [SYSTEM]).
        """
        source_name = source.get("label") or source.get("name", "the source concept")
        target_name = target.get("label") or target.get("name", "the target concept")
        edge_type = edge.get("edge_type", "connection").replace("_", " ")
        relationship = edge.get("relationship_description", "")
        insight = edge.get("transferable_insight", "")

        prompt = (
            f"Two concepts are connected in a cross-domain reasoning graph.\n\n"
            f"Source: {source_name}\n"
            f"Target: {target_name}\n"
            f"Connection type: {edge_type}\n"
            f"Curated relationship: {relationship}\n"
            f"Transferable insight: {insight}\n\n"
            f"Explain in your own words why this analogy is creatively productive "
            f"for interface design. What deeper structural or behavioural pattern "
            f"makes this connection valuable beyond the surface similarity?"
        )
        return await self._call(prompt)

    async def suggest_alternatives(
        self,
        graph: dict[str, Any],
        constraints: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Propose unexplored creative directions given the current graph and constraints.
        Returns lightweight suggestion dicts — no numerical values.
        """
        node_labels = [n.get("label", n.get("id", "?")) for n in graph.get("nodes", [])][:6]
        active = ", ".join(f"{k}={v:.1f}" for k, v in constraints.items() if isinstance(v, float))

        prompt = (
            f"A reasoning graph contains these inspiration nodes: {', '.join(node_labels)}.\n"
            f"Active constraints: {active}.\n\n"
            f"Suggest one or two unexplored creative directions — concepts from other "
            f"domains that are not yet in the graph but would enrich the design system. "
            f"Explain briefly why each would be valuable."
        )
        text = await self._call(prompt)
        return [{"id": "ai-suggestion-1", "concept": text, "derivation": "AI"}]

    async def identify_weak_analogies(
        self,
        edges: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Critique which connections in the graph are superficial or potentially
        misleading for design purposes.  No weights are modified.
        """
        if not edges:
            return []
        summaries = "; ".join(
            f"'{e.get('id', '?')}' ({e.get('edge_type', '?')})"
            for e in edges[:8]
        )
        prompt = (
            f"Review these cross-domain connections: {summaries}.\n\n"
            f"Which of these analogies risk being superficial — where the surface "
            f"similarity might mislead a designer rather than genuinely inform the "
            f"interface? Explain your reasoning briefly."
        )
        text = await self._call(prompt)
        return [{"critique": text, "derivation": "AI"}]

    async def explain_design_tradeoff(
        self,
        decision: dict[str, Any],
        constraints: dict[str, Any],
    ) -> str:
        """
        Explain the qualitative implications of the current constraint configuration
        for a specific design node or token decision.  No values are generated.
        """
        inspiration = decision.get("inspiration", {})
        node_name = (
            inspiration.get("name")
            or decision.get("target_id")
            or "this design element"
        )
        domain = inspiration.get("domain", "")
        description = inspiration.get("description", "")
        principles_raw = inspiration.get("key_principles", [])
        principles = "; ".join(
            p.get("name", "") for p in principles_raw[:3] if p.get("name")
        )

        active_c = {k: v for k, v in constraints.items() if isinstance(v, (int, float))}
        constraint_prose = ", ".join(
            f"{k.replace('_', ' ')} at {v:.0%}" for k, v in active_c.items()
        ) if active_c else "default balanced constraints"

        prompt = (
            f"Inspiration: {node_name}"
            + (f" ({domain} domain)" if domain else "")
            + ".\n"
            + (f"Context: {description}\n" if description else "")
            + (f"Key principles: {principles}\n" if principles else "")
            + f"\nCurrent design constraints: {constraint_prose}.\n\n"
            f"Explain what this inspiration teaches us about interface design "
            f"and how the current constraints shape which aspects of it are most "
            f"relevant. Focus on qualitative reasoning about implications and tradeoffs."
        )
        return await self._call(prompt)

    async def generate_reasoning_summary(
        self,
        graph: dict[str, Any],
        constraints: dict[str, Any],
        design_system: dict[str, Any],
    ) -> str:
        """
        Generate a Markdown reasoning summary for the export package.
        Describes the creative logic of the session — does not reproduce or
        invent any numerical token values.
        """
        node_labels = [
            n.get("label", n.get("id", "?")) for n in graph.get("nodes", [])
        ][:8]
        top_nodes = ", ".join(node_labels)

        edge_types: dict[str, int] = {}
        for e in graph.get("edges", []):
            et = e.get("edge_type", "unknown")
            edge_types[et] = edge_types.get(et, 0) + 1
        edge_summary = ", ".join(
            f"{count} {et.replace('_', ' ')}"
            for et, count in sorted(edge_types.items(), key=lambda x: -x[1])
        )

        active_c = {k: v for k, v in constraints.items() if isinstance(v, (int, float))}
        constraint_prose = ", ".join(
            f"{k.replace('_', ' ')} {v:.0%}" for k, v in active_c.items()
        ) if active_c else "balanced defaults"

        wcag = design_system.get("wcag_level", "AA")
        base_size = design_system.get("typography", {}).get("base_size", 16)

        prompt = (
            f"A creative reasoning session produced the following design system.\n\n"
            f"Inspiration nodes: {top_nodes}.\n"
            f"Graph connections: {edge_summary}.\n"
            f"Constraint configuration: {constraint_prose}.\n"
            f"Resulting WCAG level: {wcag}. Base typography size: {base_size}px.\n\n"
            f"Write a concise Markdown reasoning summary (use ## headings, no bullet "
            f"lists) that explains the creative logic behind this design system. "
            f"Cover: why these inspirations were combined, what the constraints "
            f"prioritised, and what design philosophy emerged. "
            f"Do not reproduce numerical token values — explain the reasoning."
        )
        text = await self._call(prompt)

        # Ensure Markdown heading structure
        if not text.startswith("#"):
            text = f"## Design Reasoning Summary\n\n{text}"
        return text
