from enum import Enum
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class DerivationLabel(str, Enum):
    CURATED = "CURATED"
    SYSTEM = "SYSTEM"
    RETRIEVED = "RETRIEVED"
    AI = "AI"
    AI_ACCEPTED = "AI_ACCEPTED"  # User-accepted (possibly edited) Granite suggestion
    MANUAL = "MANUAL"

class LabeledValue(BaseModel, Generic[T]):
    value: T
    derivation: DerivationLabel

class DomainType(str, Enum):
    architecture = "architecture"
    biology = "biology"
    music = "music"
    industrial_design = "industrial_design"
    psychology = "psychology"
    nature = "nature"
    fashion = "fashion"
    engineering = "engineering"
    history = "history"
    film = "film"
    economics = "economics"
    graphic_design = "graphic_design"
