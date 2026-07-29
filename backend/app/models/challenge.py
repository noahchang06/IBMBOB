from pydantic import BaseModel
from app.models.common import DomainType

class PresetChallenge(BaseModel):
    id: str
    name: str
    subtitle: str
    description: str
    domains: list[DomainType]
    node_count: int = 0
    tags: list[str]

class ChallengeListResponse(BaseModel):
    challenges: list[PresetChallenge]
