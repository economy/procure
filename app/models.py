from pydantic import BaseModel
from typing import List, Optional

class AnalyzeRequest(BaseModel):
    product_category: str
    comparison_factors: Optional[List[str]] = None

class AnalyzeResponse(BaseModel):
    task_id: str
    status: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result_url: Optional[str] = None 