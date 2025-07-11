import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from uuid import uuid4
import os

from app.models.tasks import AnalyzeRequest, AnalyzeResponse, TaskStatusResponse
from app.dependencies import get_api_key
from app.agents.clarification_agent import clarify_query
from app.agents.search_agent import execute_search_for_solutions
from app.agents.extraction_agent import extract_information
from app.agents.formatting_agent import format_data_as_csv
from app.models.tasks import ProcurementData, ProcurementState
from app.models.queries import ExtractedProduct


router = APIRouter()

# In-memory storage for tasks
tasks: dict[str, ProcurementData] = {}


async def run_analysis(task_id: str, api_key: str):
    """Orchestrates the agentic analysis workflow with a retry loop."""
    task_data = tasks[task_id]
    max_retries = 1  # Number of search retries after the initial one
    search_retries = 0
    min_successful_extractions = 15
    processed_urls: set[str] = set()

    try:
        # State: CLARIFYING
        task_data.current_state = ProcurementState.CLARIFYING
        clarification_result = await clarify_query(task_data.initial_query, api_key)
        task_data.clarified_query = clarification_result.clarified_query
        
        # Combine and unique factors
        all_factors = task_data.comparison_factors + clarification_result.comparison_factors
        task_data.comparison_factors = list(set(all_factors))

        task_data.extracted_data = []

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
            
            extraction_tasks = []
            for url in urls_to_process:
                extraction_tasks.append(
                    extract_information(
                        url=url,
                        comparison_factors=task_data.comparison_factors,
                        api_key=api_key,
                    )
                )

            extraction_results = await asyncio.gather(*extraction_tasks)

            for extracted_product in extraction_results:
                if len(task_data.extracted_data) >= min_successful_extractions:
                    break

                if extracted_product and extracted_product.extracted_factors:
                    # Filter out error objects before processing
                    if extracted_product.product_name == "N/A" and any(f.name == "error" for f in extracted_product.extracted_factors):
                        continue

                    not_found_count = sum(
                        1
                        for factor in extracted_product.extracted_factors
                        if factor.value == "Not found"
                    )
                    failure_threshold = len(task_data.comparison_factors) / 2

                    if not_found_count <= failure_threshold:
                        task_data.extracted_data.append(extracted_product.model_dump())

            if len(task_data.extracted_data) >= min_successful_extractions:
                break

            if search_retries >= max_retries:
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