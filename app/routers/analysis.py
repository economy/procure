from fastapi import APIRouter, Depends, BackgroundTasks
from uuid import uuid4
from app.models import AnalyzeRequest, AnalyzeResponse, TaskStatusResponse
from app.dependencies import get_api_key

router = APIRouter()

# In-memory storage for tasks
tasks = {}

def run_analysis(task_id: str, request: AnalyzeRequest):
    """Placeholder function for running the agentic analysis."""
    tasks[task_id] = {"status": "in_progress", "result_url": None}
    # In the future, this will trigger the AgentZero workflow
    print(f"Starting analysis for task {task_id} on '{request.product_category}'")
    # Simulate work
    import time
    time.sleep(10)
    tasks[task_id] = {"status": "completed", "result_url": f"/results/{task_id}.csv"}
    print(f"Analysis for task {task_id} completed.")

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    task_id = str(uuid4())
    background_tasks.add_task(run_analysis, task_id, request)
    tasks[task_id] = {"status": "pending", "result_url": None}
    return AnalyzeResponse(task_id=task_id, status="pending")

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_status(task_id: str, api_key: str = Depends(get_api_key)):
    task = tasks.get(task_id)
    if not task:
        return TaskStatusResponse(task_id=task_id, status="not_found", result_url=None)

    status = task.get("status") or "error"
    result_url = task.get("result_url")
    return TaskStatusResponse(task_id=task_id, status=status, result_url=result_url) 