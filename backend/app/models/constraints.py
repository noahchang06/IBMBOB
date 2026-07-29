from enum import Enum
from typing import Dict
from pydantic import BaseModel
from app.models.common import DerivationLabel

class ConstraintKey(str, Enum):
    visual_tension = "visual_tension"
    information_density = "information_density"
    accessibility = "accessibility"
    playfulness = "playfulness"
    material_scarcity = "material_scarcity"

ConstraintSet = Dict[ConstraintKey, float]

class ConstraintEffect(BaseModel):
    edge_id: str
    original_weight: float
    modified_weight: float
    reason: str
    derivation: DerivationLabel = DerivationLabel.SYSTEM
