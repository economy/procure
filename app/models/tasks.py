from pydantic import BaseModel, Field
from typing import Optional, Any

from enum import Enum, auto

class ProcurementState(Enum):
    START = auto()
    CLARIFYING = auto()
    AWAITING_CLARIFICATION = auto()
    SEARCHING = auto()
    EXTRACTING = auto()
    FORMATTING = auto()
    DONE = auto()
    ERROR = auto()

class ProcurementData(BaseModel):
    task_id: str
    current_state: ProcurementState = ProcurementState.START
    initial_query: str
    clarified_query: str = ""
    comparison_factors: list[str] = []
    search_results: list[str] = []
    extracted_data: list[dict[str, Any]] = Field(default_factory=list)
    formatted_output: Optional[str] = None
    error_message: Optional[str] = None

class AnalyzeRequest(BaseModel):
    query: str
    comparison_factors: list[str] = Field(default_factory=list)

class AnalyzeResponse(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    data: Optional[dict[str, Any]] = None 