from typing import Dict, Any, List
from app.services.granite_adapter import GraniteAdapter

class MockGraniteAdapter(GraniteAdapter):
    async def extract_principles(self, inspiration_description: str, target_domain: str) -> List[str]:
        return ["Focus on layered temporal data", "Avoid cultural color assumptions"]

    async def explain_relationship(self, source: Dict[str, Any], target: Dict[str, Any], edge: Dict[str, Any]) -> str:
        if edge.get("edge_type") == "functional_similarity":
            return "By aligning these two functionally similar domains, the design can leverage established human mental models from both areas, reducing cognitive load."
        return "This connection reveals a structural parallel that allows translating patterns from the source directly into the target interface."

    async def suggest_alternatives(self, graph: Dict[str, Any], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"id": "alt-1", "concept": "Sound as notification", "reason": "Reduces visual information density"}]

    async def identify_weak_analogies(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []

    async def explain_design_tradeoff(self, decision: Dict[str, Any], constraints: Dict[str, Any]) -> str:
        return "A high visual tension constraint directly conflicts with extreme accessibility needs. The system resolved this by isolating high-tension typography to non-critical headings, leaving data-heavy components optimized for readability."

    async def generate_reasoning_summary(self, graph: Dict[str, Any], constraints: Dict[str, Any], design_system: Dict[str, Any]) -> str:
        return "# Design Reasoning Summary\n\nThis design prioritizes clarity for clinical decision-making. High accessibility constraints drove the typography scale, while triage concepts influenced the error palette."
