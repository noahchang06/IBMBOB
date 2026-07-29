from typing import Optional
from pydantic import BaseModel
from app.models.common import DerivationLabel

class TypeScale(BaseModel):
    heading_family: str
    heading_weight: str
    body_family: str
    body_weight: str
    base_size: int
    scale_ratio: float
    line_height: float

class ColorToken(BaseModel):
    name: str
    hex: str
    role: str
    contrast_ratio: Optional[float] = None
    derivation: DerivationLabel = DerivationLabel.SYSTEM

class Palette(BaseModel):
    colors: list[ColorToken]
    background: str
    foreground: str
    derivation: DerivationLabel = DerivationLabel.SYSTEM

class SpacingScale(BaseModel):
    base: int
    scale: list[int]
    unit: str

class ComponentStyle(BaseModel):
    name: str
    border_radius: str
    padding: str
    shadow: str
    notes: str

class DesignSystem(BaseModel):
    typography: TypeScale
    palette: Palette
    spacing: SpacingScale
    components: list[ComponentStyle]
    motion_duration_ms: int
    motion_easing: str
    wcag_level: str
    derivation: DerivationLabel = DerivationLabel.SYSTEM
