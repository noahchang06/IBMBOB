from pydantic import BaseModel
from app.models.graph import ReasoningGraph
from app.models.design_system import DesignSystem
from app.models.inspiration import Inspiration
from app.models.constraints import ConstraintSet

class ExportRequest(BaseModel):
    graph_id: str
    include_tokens: bool
    include_graph: bool
    include_inspirations: bool
    include_reasoning: bool

class ExportPackage(BaseModel):
    challenge_name: str
    design_tokens: DesignSystem
    graph: ReasoningGraph
    selected_inspirations: list[Inspiration]
    constraints: ConstraintSet
    reasoning_summary_markdown: str
