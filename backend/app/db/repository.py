from abc import ABC, abstractmethod
from typing import Dict, Any, List

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
