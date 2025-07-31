from __future__ import annotations
from enum import Enum, auto
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class ProcurementState(Enum):
    START = auto()
    CLARIFYING = auto()
    AWAITING_CLARIFICATION = auto()
    EXTRACTING = auto()
    PROCESSING = auto()
    ENRICHING = auto()
    FORMATTING = auto()
    COMPLETED = auto()
    ERROR = auto()


class ProcurementData(BaseModel):
    task_id: str
    current_state: ProcurementState = ProcurementState.START
    initial_query: str
    clarified_query: str = ""
    comparison_factors: List[str] = []
    extracted_data: List[Dict[str, Any]] = []
    formatted_output: Optional[str] = None
    error_message: Optional[str] = None


class AnalyzeRequest(BaseModel):
    query: str
    comparison_factors: Optional[List[str]] = None


class AnalyzeResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    data: Dict[str, Any]
