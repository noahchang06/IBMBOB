from abc import ABC, abstractmethod
from typing import Dict, Any, List

class GraniteAdapter(ABC):
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
