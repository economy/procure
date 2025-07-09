from enum import Enum, auto
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ProcurementState(Enum):
    START = auto()
    CLARIFYING = auto()
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
    comparison_factors: List[str] = []
    search_results: List[str] = []
    extracted_data: List[Dict[str, Any]] = Field(default_factory=list)
    formatted_output: Optional[str] = None
    error_message: Optional[str] = None