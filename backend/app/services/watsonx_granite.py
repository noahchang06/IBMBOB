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
from app.services.graph_context import (
    build_alternatives_prompt,
    build_node_tradeoff_prompt,
    build_reasoning_summary_prompt,
    build_relationship_prompt,
    build_semantic_graph_context,
    build_weak_analogy_prompt,
)

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
        # Graph structure stays deterministic; Granite only handles interpretive prose.
        from app.services.mock_granite import MockGraniteAdapter
        self._structural = MockGraniteAdapter()

    async def generate_inspirations(self, challenge: "PresetChallenge") -> list["Inspiration"]:
        """Delegate graph seeding to the deterministic structural adapter."""
        return await self._structural.generate_inspirations(challenge)

    async def generate_edges(self, challenge_id: str, inspirations: list["Inspiration"]) -> list["GraphEdge"]:
        """Delegate edge construction to the deterministic structural adapter."""
        return await self._structural.generate_edges(challenge_id, inspirations)

    async def generate_edges_for_new_inspiration(self, challenge_id: str, new_inspiration: "Inspiration", existing_inspirations: list["Inspiration"]) -> list["GraphEdge"]:
        """Delegate incremental edge construction to the deterministic structural adapter."""
        return await self._structural.generate_edges_for_new_inspiration(
            challenge_id, new_inspiration, existing_inspirations
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
        graph_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Explain WHY two inspirations are connected and what makes the analogy
        creatively valuable.  Does NOT alter the edge weight (that is [SYSTEM]).
        Uses semantic edge neighborhood context when provided.
        """
        prompt = build_relationship_prompt(source, target, edge, graph_context)
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
        prompt = build_alternatives_prompt(graph, constraints)
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
        prompt = build_weak_analogy_prompt(edges)
        text = await self._call(prompt)
        return [{"critique": text, "derivation": "AI"}]

    async def explain_design_tradeoff(
        self,
        decision: dict[str, Any],
        constraints: dict[str, Any],
        graph_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Explain the qualitative implications of the current constraint configuration
        for a specific design node or token decision.  No values are generated.
        """
        # Build neighborhood if full graph is in the decision payload
        if graph_context is None and decision.get("graph"):
            focus = []
            node = decision.get("node") or {}
            insp = decision.get("inspiration") or {}
            if node.get("id"):
                focus.append(node["id"])
            elif decision.get("target_id"):
                focus.append(decision["target_id"])
            if insp.get("id") and f"n-{insp['id']}" not in focus:
                # Prefer node id forms already in graph
                focus.append(insp["id"])
            graph_context = build_semantic_graph_context(
                decision["graph"],
                focus,
                inspirations={insp["id"]: insp} if insp.get("id") else None,
            )
        prompt = build_node_tradeoff_prompt(decision, constraints, graph_context)
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
        prompt = build_reasoning_summary_prompt(graph, constraints, design_system)
        text = await self._call(prompt)

        # Ensure Markdown heading structure
        if not text.startswith("#"):
            text = f"## Design Reasoning Summary\n\n{text}"
        return text

    async def suggest_relationships(
        self,
        source_idea: dict[str, Any],
        target_idea: dict[str, Any],
        graph_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Ask Granite for up to three directed semantic relationship suggestions.
        Returns validated suggestion dict — never persists edges.
        """
        from app.services.relationship_suggestions import (
            build_suggest_relationships_prompt,
            parse_relationship_suggestions,
        )

        prompt = build_suggest_relationships_prompt(source_idea, target_idea, graph_context)
        logger.info(
            "Granite relationship suggestion requested source=%s target=%s neighborhood_nodes=%s",
            source_idea.get("id") or source_idea.get("title"),
            target_idea.get("id") or target_idea.get("title"),
            len((graph_context or {}).get("nodes") or []),
        )
        text = await self._call(prompt)
        parsed = parse_relationship_suggestions(text)
        return parsed.model_dump()
