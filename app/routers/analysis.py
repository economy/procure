import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from uuid import uuid4
import os
from pydantic import BaseModel
from typing import Literal

from app.models.tasks import AnalyzeRequest, AnalyzeResponse, TaskStatusResponse
from app.dependencies import get_api_key
from app.agents.clarification_agent import clarify_query
from app.agents.search_agent import execute_search_for_solutions
from app.agents.extraction_agent import extract_information
from app.agents.formatting_agent import format_data_as_csv
from app.models.tasks import ProcurementData, ProcurementState
from app.models.queries import ExtractedProduct
from app.utils import load_factor_templates


class ClarificationRequest(BaseModel):
    query: str


router = APIRouter()

# In-memory storage for tasks
tasks: dict[str, ProcurementData] = {}


async def run_analysis(task_id: str, api_key: str):
    """Orchestrates the agentic analysis workflow with a retry loop."""
    task_data = tasks[task_id]

    try:
        # --- Clarification Step ---
        if task_data.current_state in [ProcurementState.START, ProcurementState.AWAITING_CLARIFICATION]:
            task_data.current_state = ProcurementState.CLARIFYING
            
            # Use the clarified query from the user if available, otherwise use the initial query
            query_to_clarify = task_data.clarified_query or task_data.initial_query
            clarification_result = await clarify_query(query_to_clarify, api_key)

            if clarification_result.needs_clarification:
                task_data.current_state = ProcurementState.AWAITING_CLARIFICATION
                task_data.clarified_query = clarification_result.question_for_user or "Query is too ambiguous. Please provide a more specific product category."
                return

            task_data.clarified_query = clarification_result.clarified_query
            # Combine user-provided factors with the generic template
            all_factors = task_data.comparison_factors + clarification_result.comparison_factors
            task_data.comparison_factors = list(set(all_factors))
            task_data.extracted_data = []

        # --- Main Workflow Loop ---
        max_retries = 1
        search_retries = 0
        min_successful_extractions = 15
        processed_urls: set[str] = set()

        while True:
            # State: SEARCHING
            task_data.current_state = ProcurementState.SEARCHING
            search_results = execute_search_for_solutions(
                product_category=task_data.clarified_query,
                comparison_factors=task_data.comparison_factors,
            )

            urls_to_process = [url for url in search_results if url not in processed_urls]
            processed_urls.update(urls_to_process)
            task_data.search_results.extend(urls_to_process)

            # State: EXTRACTING
            task_data.current_state = ProcurementState.EXTRACTING
            extraction_tasks = [
                extract_information(
                    url=url,
                    comparison_factors=task_data.comparison_factors,
                    api_key=api_key,
                )
                for url in urls_to_process
            ]
            extraction_results = await asyncio.gather(*extraction_tasks)

            for extracted_product in extraction_results:
                if len(task_data.extracted_data) >= min_successful_extractions:
                    break  # Stop adding more products if we have enough
                if extracted_product and extracted_product.extracted_factors:
                    # Filter out error objects
                    if extracted_product.product_name == "N/A" and any(f.name == "error" for f in extracted_product.extracted_factors):
                        continue
                    task_data.extracted_data.append(extracted_product.model_dump())

            # --- Data Quality Check ---
            # Decide if we need to retry the search based on data completeness.
            total_factors_possible = len(task_data.extracted_data) * len(task_data.comparison_factors)

            # Default to low completeness if no data, to allow retry
            completeness_ratio = 0.0

            if total_factors_possible > 0:
                total_factors_found = 0
                for product_data in task_data.extracted_data:
                    found_count = sum(
                        1
                        for factor in product_data.get("extracted_factors", [])
                        if factor.get("value") != "Not found"
                    )
                    total_factors_found += found_count

                completeness_ratio = total_factors_found / total_factors_possible

            # Conditions to break the loop:
            # 1. The data is complete enough (>= 60%)
            # 2. We have hit the maximum number of search retries
            if completeness_ratio >= 0.6 or search_retries >= max_retries:
                break

            search_retries += 1

        # State: FORMATTING
        task_data.current_state = ProcurementState.FORMATTING
        if not task_data.extracted_data:
            raise Exception("Could not extract sufficient data from any sources.")

        csv_output = format_data_as_csv(
            extracted_data=task_data.extracted_data,
            comparison_factors=task_data.comparison_factors,
        )
        task_data.formatted_output = csv_output
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


@router.post("/tasks/{task_id}/clarify")
async def clarify_task(
    task_id: str,
    request: ClarificationRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
):
    """
    Provides a more specific query to a paused task and resumes it.
    """
    task_data = tasks.get(task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_data.current_state != ProcurementState.AWAITING_CLARIFICATION:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not awaiting clarification. Current state: {task_data.current_state.name}",
        )

    # Update task with the user's new, more specific query
    task_data.clarified_query = request.query
    task_data.current_state = ProcurementState.AWAITING_CLARIFICATION # Will be switched to CLARIFYING in run_analysis

    # Resume the analysis
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")
    
    background_tasks.add_task(run_analysis, task_id, google_api_key)

    return {"message": "Task clarification received. Resuming analysis."} 