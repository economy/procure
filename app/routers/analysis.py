import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from uuid import uuid4
import os
from pydantic import BaseModel
from typing import Literal
from loguru import logger

from app.models.tasks import AnalyzeRequest, AnalyzeResponse, TaskStatusResponse
from app.dependencies import get_api_key
from app.agents.clarification_agent import clarify_query
from app.agents.search_agent import search_and_extract
from app.agents.summarization_agent import process_and_summarize_data
from app.agents.formatting_agent import format_data_as_csv
from app.models.tasks import ProcurementData, ProcurementState
from app.utils import load_factor_templates


class ClarificationRequest(BaseModel):
    query: str


router = APIRouter()

# In-memory storage for tasks
tasks: dict[str, ProcurementData] = {}


async def run_analysis(task_id: str, api_key: str):
    """Orchestrates the streamlined agentic analysis workflow."""
    task_data = tasks[task_id]

    try:
        # --- Clarification Step ---
        if task_data.current_state in [ProcurementState.START, ProcurementState.AWAITING_CLARIFICATION]:
            task_data.current_state = ProcurementState.CLARIFYING
            
            query_to_clarify = task_data.clarified_query or task_data.initial_query
            clarification_result = await clarify_query(query_to_clarify, api_key)

            if clarification_result.needs_clarification:
                task_data.current_state = ProcurementState.AWAITING_CLARIFICATION
                task_data.clarified_query = clarification_result.question_for_user or "Query is too ambiguous."
                return

            task_data.clarified_query = clarification_result.clarified_query
            if not task_data.comparison_factors:
                task_data.comparison_factors = clarification_result.comparison_factors
            task_data.comparison_factors = sorted(list(set(task_data.comparison_factors)))

        # --- Search and Extraction Step ---
        task_data.current_state = ProcurementState.EXTRACTING
        extracted_data = search_and_extract(
            product_category=task_data.clarified_query,
            comparison_factors=task_data.comparison_factors,
        )
        task_data.extracted_data = extracted_data

        if not task_data.extracted_data:
            raise Exception("Could not extract sufficient data using the search agent.")

        # --- Summarization Step ---
        task_data.extracted_data = await process_and_summarize_data(
            extracted_data=task_data.extracted_data,
            api_key=api_key,
        )

        # --- Formatting Step ---
        task_data.current_state = ProcurementState.FORMATTING
        csv_output = format_data_as_csv(
            extracted_data=task_data.extracted_data,
            comparison_factors=task_data.comparison_factors,
        )
        task_data.formatted_output = csv_output
        task_data.current_state = ProcurementState.COMPLETED

    except Exception as e:
        logger.exception(f"An error occurred while running analysis for task {task_id}")
        task_data.current_state = ProcurementState.ERROR
        task_data.error_message = str(e)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
):
    """Starts a new analysis task."""
    task_id = str(uuid4())
    task_data = ProcurementData(
        task_id=task_id,
        initial_query=request.query,
        comparison_factors=request.comparison_factors,
    )
    tasks[task_id] = task_data

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")

    background_tasks.add_task(run_analysis, task_id, google_api_key)

    return AnalyzeResponse(task_id=task_id)


def _map_procurement_state_to_status(state: ProcurementState) -> str:
    if state == ProcurementState.AWAITING_CLARIFICATION:
        return "paused_for_clarification"
    if state == ProcurementState.COMPLETED:
        return "completed"
    if state == ProcurementState.ERROR:
        return "failed"
    return "running"


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_status(task_id: str):
    """Retrieves the status of an analysis task."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    result_url = None
    if task.current_state == ProcurementState.COMPLETED and task.formatted_output:
        result_url = f"data:text/csv;charset=utf-8,{task.formatted_output}"

    task_dump = task.model_dump()
    if result_url:
        task_dump["result"] = result_url

    return TaskStatusResponse(
        task_id=task.task_id,
        status=_map_procurement_state_to_status(task.current_state),
        data=task_dump,
    )


@router.post("/tasks/{task_id}/clarify")
async def clarify_task(
    task_id: str,
    request: ClarificationRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
):
    """Provides a more specific query to a paused task and resumes it."""
    task_data = tasks.get(task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_data.current_state != ProcurementState.AWAITING_CLARIFICATION:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not awaiting clarification. Current state: {task_data.current_state.name}",
        )

    task_data.clarified_query = request.query
    task_data.current_state = ProcurementState.AWAITING_CLARIFICATION 

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")
    
    background_tasks.add_task(run_analysis, task_id, google_api_key)

    return {"message": "Task clarification received. Resuming analysis."}
