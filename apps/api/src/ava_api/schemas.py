from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

BlockType = Literal[
    "prompt",
    "web",
    "note",
    "table",
    "list",
    "report",
    "memo",
    "file",
    "youtube",
    "image",
    "excel",
    "presentation",
    "dashboard",
    "app",
    "code",
    "connector",
    "human_gate",
]
BlockStatus = Literal["idle", "running", "complete", "error"]
RunStatus = Literal["pending", "running", "complete", "error", "paused"]


class BlockConfig(BaseModel):
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    system_prompt: str | None = None
    url: str | None = None
    export_pptx: bool | None = None
    file_path: str | None = None
    youtube_url: str | None = None
    connector_id: str | None = None
    resource: str | None = None
    approved: bool | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class BlockOutput(BaseModel):
    type: Literal["text", "table", "file_ref", "image_ref"] = "text"
    content: str | None = None
    artifact_id: str | None = None
    token_count: int | None = None


class CanvasBlock(BaseModel):
    id: str
    type: BlockType
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    data: dict[str, Any] = Field(default_factory=dict)
    connections: dict[str, list[str]] = Field(
        default_factory=lambda: {"inputs": [], "outputs": []}
    )


class CanvasEdge(BaseModel):
    id: str
    source: str
    target: str


class CanvasGraph(BaseModel):
    blocks: list[CanvasBlock]
    edges: list[CanvasEdge]


class CreateCanvasRequest(BaseModel):
    name: str = "Untitled canvas"
    graph: CanvasGraph | None = None


class CanvasResponse(BaseModel):
    id: UUID
    name: str
    graph: CanvasGraph


class StartRunRequest(BaseModel):
    canvas_id: UUID
    mode: Literal["canvas", "swarm"] = "canvas"


class RunResponse(BaseModel):
    id: UUID
    canvas_id: UUID | None = None
    status: RunStatus
    thread_id: str
    mode: str = "canvas"


class BlockRunEvent(BaseModel):
    block_id: str
    status: BlockStatus
    output: BlockOutput | None = None
    error: str | None = None
    tokens: str | None = None


# --- Plan JSON (L1/L2 contract, Document 2 §7) ---

PersonaType = Literal["researcher", "analyst", "writer", "coder"]
TaskOutputType = Literal["text", "table", "file", "image"]


class PlanTask(BaseModel):
    id: str
    description: str
    persona: PersonaType
    dependencies: list[str] = Field(default_factory=list)
    estimated_blocks: list[str] = Field(default_factory=list)
    output_type: TaskOutputType = "text"


class ExecutionPlan(BaseModel):
    run_id: str | None = None
    goal: str
    estimated_duration_minutes: int = 15
    tasks: list[PlanTask]
    deliverables: list[str] = Field(default_factory=list)
    clarifications_needed: list[str] = Field(default_factory=list)


class StartSwarmRunRequest(BaseModel):
    canvas_id: UUID | None = None
    plan: ExecutionPlan | None = None
    use_demo_plan: bool = False


class PlanningBriefRequest(BaseModel):
    brief: str
    user_id: str = "default"
