from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.models.challenge import PresetChallenge

from app.models.inspiration import Inspiration
from app.models.graph import GraphEdge

class Repository(ABC):
    @abstractmethod
    async def save_project(self, project_id: str, name: str, challenge_id: str, graph_state: Dict[str, Any], constraint_state: Dict[str, Any]) -> None:
        pass
        
    @abstractmethod
    async def load_project(self, project_id: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def save_snapshot(self, project_id: str, label: str, state: Dict[str, Any]) -> str:
        pass
        
    @abstractmethod
    async def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def create_challenge(self, challenge: PresetChallenge) -> None:
        pass

    @abstractmethod
    async def get_all_challenges(self) -> List[PresetChallenge]:
        pass

    @abstractmethod
    async def create_inspiration(self, challenge_id: str, inspiration: Inspiration) -> None:
        pass

    @abstractmethod
    async def get_inspirations_for_challenge(self, challenge_id: str) -> List[Inspiration]:
        pass

    @abstractmethod
    async def create_edge(self, challenge_id: str, edge: GraphEdge) -> None:
        pass

    @abstractmethod
    async def get_edges_for_challenge(self, challenge_id: str) -> List[GraphEdge]:
        pass

    @abstractmethod
    async def delete_challenge(self, challenge_id: str) -> None:
        pass
