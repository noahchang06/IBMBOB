import json
import os
from typing import Dict, List, Optional
from app.config import settings
from app.models.challenge import PresetChallenge
from app.models.inspiration import Inspiration
from app.models.graph import GraphNode, GraphEdge, ReasoningGraph
from app.models.common import DomainType, DerivationLabel

class KnowledgeBase:
    def __init__(self):
        self.challenges: Dict[str, PresetChallenge] = {}
        self.inspirations_by_challenge: Dict[str, List[Inspiration]] = {}
        self.edges_by_challenge: Dict[str, List[Dict]] = {}
        self.load()
        
    def load(self):
        seed_dir = settings.SEED_DATA_PATH
        if not os.path.exists(seed_dir):
            return
            
        for filename in os.listdir(seed_dir):
            if filename.endswith(".json"):
                path = os.path.join(seed_dir, filename)
                with open(path, "r") as f:
                    data = json.load(f)
                    
                    # Parse challenge
                    c_data = data.get("challenge", {})
                    challenge = PresetChallenge(
                        id=c_data["id"],
                        name=c_data["name"],
                        subtitle=c_data.get("subtitle", ""),
                        description=c_data.get("description", ""),
                        domains=[DomainType(d) for d in c_data.get("domains", [])],
                        tags=c_data.get("tags", []),
                        node_count=len(data.get("inspirations", []))
                    )
                    self.challenges[challenge.id] = challenge
                    
                    # Parse inspirations
                    inspirations = []
                    for i_data in data.get("inspirations", []):
                        inspiration = Inspiration(**i_data)
                        inspirations.append(inspiration)
                    self.inspirations_by_challenge[challenge.id] = inspirations
                    
                    # Parse edges (raw dicts for now, to be used by GraphService)
                    self.edges_by_challenge[challenge.id] = data.get("edges", [])

    def get_challenges(self) -> List[PresetChallenge]:
        return list(self.challenges.values())
        
    def get_challenge(self, challenge_id: str) -> Optional[PresetChallenge]:
        return self.challenges.get(challenge_id)
        
    def get_inspirations(self, challenge_id: str) -> List[Inspiration]:
        return self.inspirations_by_challenge.get(challenge_id, [])
        
    def get_raw_edges(self, challenge_id: str) -> List[Dict]:
        return self.edges_by_challenge.get(challenge_id, [])

knowledge_base = KnowledgeBase()
