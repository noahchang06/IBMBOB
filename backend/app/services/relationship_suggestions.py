"""Pydantic models and normalization for Granite relationship suggestions."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.graph import EdgeType, EDGE_TYPE_DEFAULT_LABELS

logger = logging.getLogger(__name__)

# Preferred suggestion classes → existing EdgeType enum values
SUGGESTION_CLASS_TO_EDGE_TYPE: dict[str, EdgeType] = {
    "inspiration": EdgeType.inspired_by,
    "inspired_by": EdgeType.inspired_by,
    "extension": EdgeType.extension,
    "refinement": EdgeType.refinement,
    "contrast": EdgeType.contrast,
    "support": EdgeType.support,
    "dependency": EdgeType.dependency,
    "composition": EdgeType.combination,
    "combination": EdgeType.combination,
    "reference": EdgeType.reference,
    "similarity": EdgeType.similarity,
    # legacy / adjacent
    "functional_similarity": EdgeType.similarity,
    "structural_analogy": EdgeType.extension,
}


class RelationshipSuggestion(BaseModel):
    edge_type: EdgeType
    relationship_label: str = Field(min_length=1, max_length=120)
    relationship_description: str = Field(min_length=1, max_length=2000)
    confidence: Optional[float] = None

    @field_validator("relationship_label", "relationship_description", mode="before")
    @classmethod
    def strip_text(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if not isinstance(v, (int, float)):
            return None
        if v < 0 or v > 1:
            return max(0.0, min(1.0, float(v)))
        return float(v)

    @model_validator(mode="before")
    @classmethod
    def normalize_edge_type(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw = data.get("edge_type") or data.get("type") or data.get("relationship_class")
        if raw is None:
            return data
        key = str(raw).strip().lower().replace(" ", "_").replace("-", "_")
        mapped = SUGGESTION_CLASS_TO_EDGE_TYPE.get(key)
        if mapped is not None:
            data = {**data, "edge_type": mapped}
            return data
        # Try direct EdgeType
        try:
            data = {**data, "edge_type": EdgeType(key)}
        except ValueError:
            data = {**data, "edge_type": EdgeType.similarity}
            if not data.get("relationship_label"):
                data["relationship_label"] = "Related to"
        return data


class RelationshipSuggestionResponse(BaseModel):
    suggestions: list[RelationshipSuggestion] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def cap_suggestions_input(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("suggestions"), list):
            data = {**data, "suggestions": data["suggestions"][:3]}
        return data


def _extract_json_object(text: str) -> dict[str, Any]:
    """Pull the first JSON object from model text (handles fences / prose wrappers)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"suggestions": parsed}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("No JSON object found in model response")
    parsed = json.loads(match.group(0))
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list):
        return {"suggestions": parsed}
    raise ValueError("JSON payload was not an object or array")


def parse_relationship_suggestions(raw_text: str) -> RelationshipSuggestionResponse:
    """
    Validate and normalize Granite output into RelationshipSuggestionResponse.
    Raises ValueError on unrecoverable malformed output.
    """
    payload = _extract_json_object(raw_text)
    if "suggestions" not in payload and isinstance(payload.get("suggestion"), dict):
        payload = {"suggestions": [payload["suggestion"]]}
    if "suggestions" not in payload:
        # Single suggestion object
        if "edge_type" in payload or "relationship_label" in payload:
            payload = {"suggestions": [payload]}
        else:
            raise ValueError("Response missing 'suggestions' array")

    # Fill default labels from type when missing
    normalized_items = []
    for item in payload.get("suggestions") or []:
        if not isinstance(item, dict):
            continue
        item = dict(item)
        if not item.get("relationship_label") and item.get("edge_type"):
            try:
                et = EdgeType(str(item["edge_type"]))
                item["relationship_label"] = EDGE_TYPE_DEFAULT_LABELS.get(et, "Related to")
            except Exception:
                item["relationship_label"] = "Related to"
        if not item.get("relationship_description"):
            item["relationship_description"] = (
                f"Suggested semantic link: {item.get('relationship_label', 'Related to')}."
            )
        normalized_items.append(item)

    result = RelationshipSuggestionResponse(suggestions=normalized_items)
    if not result.suggestions:
        raise ValueError("No valid suggestions after normalization")
    return result


def build_suggest_relationships_prompt(
    source_idea: dict[str, Any],
    target_idea: dict[str, Any],
    graph_context: dict[str, Any] | None,
) -> str:
    from app.services.graph_context import format_graph_context_block

    source_title = source_idea.get("title") or source_idea.get("label") or source_idea.get("name") or "source"
    target_title = target_idea.get("title") or target_idea.get("label") or target_idea.get("name") or "target"
    source_desc = source_idea.get("description") or ""
    target_desc = target_idea.get("description") or ""

    ctx_block = format_graph_context_block(graph_context) if graph_context else "{}"

    return (
        "Suggest a meaningful semantic relationship from the source idea to the target idea. "
        "Preserve direction. Do not output generic similarity unless no more specific relationship "
        "is supported. Explain the connection using only the supplied idea content and graph context.\n\n"
        "Preferred relationship classes (map to edge_type): inspiration, extension, refinement, "
        "contrast, support, dependency, composition, reference, similarity.\n\n"
        f"Source idea: {source_title}\n"
        f"Source content: {source_desc}\n\n"
        f"Target idea: {target_title}\n"
        f"Target content: {target_desc}\n\n"
        f"Nearby graph context (JSON):\n{ctx_block}\n\n"
        "Return STRICT JSON only (no markdown fences, no prose) with this shape:\n"
        "{\n"
        '  "suggestions": [\n'
        "    {\n"
        '      "edge_type": "extension",\n'
        '      "relationship_label": "Builds on",\n'
        '      "relationship_description": "The target expands the source by adding...",\n'
        '      "confidence": 0.82\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Return at most 3 suggestions. Omit confidence if you cannot estimate it reliably."
    )
