from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.models.challenge import PresetChallenge
from app.models.inspiration import Inspiration

from app.models.graph import GraphEdge

class GraniteAdapter(ABC):
    @abstractmethod
    async def generate_inspirations(self, challenge: PresetChallenge) -> List[Inspiration]:
        """Generate a list of inspirations for a given challenge."""
        pass

    @abstractmethod
    async def generate_edges(self, challenge_id: str, inspirations: List[Inspiration]) -> List[GraphEdge]:
        """Generate a list of edges for a given list of inspirations."""
        pass

    @abstractmethod
    async def generate_edges_for_new_inspiration(self, challenge_id: str, new_inspiration: Inspiration, existing_inspirations: List[Inspiration]) -> List[GraphEdge]:
        """Generate edges for a single new inspiration against a list of existing ones."""
        pass

    @abstractmethod
    async def extract_principles(self, inspiration_description: str, target_domain: str) -> List[str]:
        """Extract transferable principles from an inspiration for a target domain."""
        pass
    
    @abstractmethod
    async def explain_relationship(self, source: Dict[str, Any], target: Dict[str, Any], edge: Dict[str, Any]) -> str:
        """Explain why two inspirations connect and what makes the connection creatively productive."""
        pass
    
    @abstractmethod
    async def suggest_alternatives(self, graph: Dict[str, Any], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest alternative creative paths not yet explored in the graph."""
        pass
    
    @abstractmethod
    async def identify_weak_analogies(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify edges that represent superficial or weak analogies."""
        pass
    
    @abstractmethod
    async def explain_design_tradeoff(self, decision: Dict[str, Any], constraints: Dict[str, Any]) -> str:
        """Explain design tradeoffs when constraints conflict."""
        pass
    
    @abstractmethod  
    async def generate_reasoning_summary(self, graph: Dict[str, Any], constraints: Dict[str, Any], design_system: Dict[str, Any]) -> str:
        """Generate a markdown reasoning summary for export."""
        pass
