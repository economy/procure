import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from uuid import uuid4
import os
from pydantic import BaseModel
from exa_py import Exa
from loguru import logger

from app.models.tasks import AnalyzeRequest, AnalyzeResponse, TaskStatusResponse
from app.dependencies import get_api_key
from app.agents.clarification_agent import clarify_query
from app.agents.search_agent import search_and_extract
from app.agents.processing_agent import process_data
from app.agents.targeting_agent import generate_enrichment_queries
from app.agents.enrichment_agent import enrich_product_data
from app.agents.formatting_agent import format_data_as_csv
from app.models.tasks import ProcurementData, ProcurementState


class ClarificationRequest(BaseModel):
    query: str


router = APIRouter()

tasks: dict[str, ProcurementData] = {}


async def run_analysis(task_id: str, api_key: str):
    """Orchestrates the self-correcting, multi-phase analysis workflow."""
    task_data = tasks[task_id]

    try:
        # --- 1. Clarification ---
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

        # --- 2. Discovery ---
        task_data.current_state = ProcurementState.EXTRACTING
        extracted_data = await search_and_extract(
            product_category=task_data.clarified_query,
            comparison_factors=task_data.comparison_factors,
            api_key=api_key,
        )
        task_data.extracted_data = extracted_data
        if not task_data.extracted_data:
            raise Exception("Phase 1 (Discovery) failed.")

        # --- 3. Initial Processing ---
        task_data.current_state = ProcurementState.PROCESSING
        task_data.extracted_data = await process_data(task_data.extracted_data, api_key)

        # --- 4. Dynamic Targeting & Enrichment ---
        task_data.current_state = ProcurementState.ENRICHING
        exa_client = Exa(api_key=os.getenv("EXA_API_KEY"))
        
        enriched_products = []
        for product in task_data.extracted_data:
            product_name = product.get("product_name")
            if not product_name:
                enriched_products.append(product)
                continue

            enrichment_queries = await generate_enrichment_queries(product, api_key)
            
            if not enrichment_queries:
                enriched_products.append(product)
                continue

            try:
                top_query = enrichment_queries[0]
                search_results = exa_client.search(top_query, num_results=1, type="keyword")
                
                if search_results.results:
                    top_result_url = search_results.results[0].url
                    page_content_response = exa_client.get_contents([top_result_url])
                    if page_content_response.results:
                        page_content = page_content_response.results[0].text
                        enriched_product = await enrich_product_data(product, page_content, api_key)
                        enriched_products.append(enriched_product)
                    else:
                        enriched_products.append(product)
                else:
                    enriched_products.append(product)
            except Exception as e:
                logger.error(f"Error during enrichment for {product_name}: {e}")
                enriched_products.append(product)

        task_data.extracted_data = enriched_products

        # --- 5. Final Formatting ---
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
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
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
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    result_url = None
    if task.current_state == ProcurementState.COMPLETED and task.formatted_output:
        result_url = f"data:text/csv;charset=utf-8,{task.formatted_output}"

    task_dump = task.model_dump()
    task_dump["current_state"] = task.current_state.name
    if result_url:
        task_dump["result"] = result_url

    return TaskStatusResponse(
        task_id=task.task_id,
        status=_map_procurement_state_to_status(task.current_state),
        data=task_dump,
    )

@router.post("/tasks/{task_id}/clarify")
async def clarify_task(task_id: str, request: ClarificationRequest, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
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
