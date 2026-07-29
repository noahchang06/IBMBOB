from typing import Optional
from pydantic import BaseModel
from app.models.common import DerivationLabel, DomainType

class TransferablePrinciple(BaseModel):
    name: str
    description: str
    source_domain: str
    derivation: DerivationLabel = DerivationLabel.CURATED

class Inspiration(BaseModel):
    id: str
    name: str
    domain: DomainType
    description: str
    historical_context: str
    key_principles: list[TransferablePrinciple]
    transferable_lessons: list[str]
    related_concepts: list[str]
    design_implications: list[str]
    image_url: Optional[str] = None
    derivation: DerivationLabel = DerivationLabel.CURATED
