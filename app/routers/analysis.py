from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from uuid import uuid4
import os

from app.models.tasks import AnalyzeRequest, AnalyzeResponse, TaskStatusResponse
from app.dependencies import get_api_key
from app.agents.clarification_agent import clarify_query
from app.agents.search_agent import search_for_products
from app.agents.extraction_agent import extract_information
from app.agents.formatting_agent import format_data_as_csv
from app.models.tasks import ProcurementData, ProcurementState


router = APIRouter()

# In-memory storage for tasks
tasks: dict[str, ProcurementData] = {}


async def run_analysis(task_id: str, api_key: str):
    """Orchestrates the agentic analysis workflow."""
    task_data = tasks[task_id]
    try:
        # State: CLARIFYING
        task_data.current_state = ProcurementState.CLARIFYING
        clarification_result = await clarify_query(task_data.initial_query, api_key)
        task_data.clarified_query = clarification_result.clarified_query
        task_data.comparison_factors.extend(clarification_result.comparison_factors)

        # State: SEARCHING
        task_data.current_state = ProcurementState.SEARCHING
        # search_for_products is not async
        search_results = search_for_products(task_data.clarified_query, api_key)
        task_data.search_results = search_results

        # State: EXTRACTING
        task_data.current_state = ProcurementState.EXTRACTING
        task_data.extracted_data = []
        for url in task_data.search_results:
            extracted_product = await extract_information(
                url=url,
                comparison_factors=task_data.comparison_factors,
                api_key=api_key,
            )
            task_data.extracted_data.append(extracted_product.model_dump())

        # State: FORMATTING
        task_data.current_state = ProcurementState.FORMATTING
        csv_output = format_data_as_csv(
            extracted_data=task_data.extracted_data,
            comparison_factors=task_data.comparison_factors,
        )
        task_data.formatted_output = csv_output

        # For now, just simulate work and complete
        task_data.current_state = ProcurementState.DONE

    except Exception as e:
        task_data.current_state = ProcurementState.ERROR
        task_data.error_message = str(e)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
):
    """
    Starts a new analysis task.
    """
    task_id = str(uuid4())
    task_data = ProcurementData(
        task_id=task_id,
        initial_query=request.query,
        comparison_factors=request.comparison_factors,
    )
    tasks[task_id] = task_data

    # Add the long-running analysis to the background
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")

    background_tasks.add_task(run_analysis, task_id, google_api_key)

    return AnalyzeResponse(task_id=task_id)


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_status(task_id: str):
    """
    Retrieves the status of an analysis task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.current_state.name,
        data=task.model_dump(),
    ) 