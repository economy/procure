import asyncio
import json
from typing import Any, Dict, List
import os

from exa_py import Exa
from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from app.models.factors import FactorDefinition


async def determine_factor_definition(
    factor_name: str, api_key: str
) -> FactorDefinition:
    """
    Dynamically determines the complete definition for a factor, including its
    JSON schema and the appropriate processing type, using a single LLM call.
    """
    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)
    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a data pipeline architect. Your job is to define how to extract and process a data field based on its name.\n"
            "1.  **Define the `factor_schema_json`**: For simple text, return a JSON string like `'{\\\"type\\\": \\\"string\\\"}'`. For fields implying a list (e.g., 'Subscription Plans'), return a JSON string for an array of objects, like `'{\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"object\\\", \\\"properties\\\": {\\\"tier_name\\\": {\\\"type\\\": \\\"string\\\"}, \\\"price\\\": {\\\"type\\\": \\\"string\\\"}}}}'`. Escape all quotes properly.\n"
            "2.  **Define the `processing_type`**: Choose 'categorize', 'summarize_prose', 'summarize_keywords', or 'none'.\n"
            "3.  **Define `categories`**: If you chose 'categorize', provide a list of 3-5 sensible category options."
        ),
        output_type=FactorDefinition,
    )
    try:
        result = await agent.run(f"Define handling for factor: '{factor_name}'")
        return result.output
    except Exception as e:
        logger.warning(
            f"Factor definition for '{factor_name}' failed, defaulting to basic string. Error: {e}"
        )
        return FactorDefinition(
            factor_schema_json='{"type": "string"}',
            processing_type="none",
            categories=None,
        )


async def search_and_extract(
    product_category: str, comparison_factors: List[str], api_key: str
) -> List[Dict[str, Any]]:
    """
    Uses Exa to find and extract structured information based on a dynamically
    generated schema from our new, intelligent FactorDefinition model.
    """
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        raise ValueError("EXA_API_KEY environment variable not set")
    exa = Exa(api_key=exa_api_key)

    definition_tasks = [
        determine_factor_definition(factor, api_key) for factor in comparison_factors
    ]
    factor_definitions = await asyncio.gather(*definition_tasks)

    properties = {"product_name": {"type": "string", "description": "The product name."}}
    instruction_lines = [
        f"Find and compare 10-15 of the leading software solutions for '{product_category}'.",
        "For each solution, extract the following information based on the described schema:",
    ]

    for factor, definition in zip(comparison_factors, factor_definitions):
        key = factor.lower().replace(" ", "_").replace("/", "_")
        try:
            schema = json.loads(definition.factor_schema_json)
            properties[key] = schema
            instruction_lines.append(f"- **{factor}**: Extract this value based on the schema.")
        except json.JSONDecodeError:
            properties[key] = {"type": "string"}
            instruction_lines.append(f"- **{factor}**: Extract this value.")

    output_schema = {
        "type": "object",
        "properties": {"products": {"type": "array", "items": {"type": "object", "properties": properties}}},
    }
    instructions = "\n".join(instruction_lines)

    task = exa.research.create_task(
        instructions=instructions, output_schema=output_schema, model="exa-research"
    )
    logger.info(f"Created Exa research task with ID: {task.id}")
    result = exa.research.poll_task(task.id)
    logger.debug(f"Received final result from Exa research poll: {result.data}")

    if not result.data or "products" not in result.data:
        return []

    formatted_products = []
    for product in result.data["products"]:
        formatted_product = {"product_name": product.get("product_name")}
        extracted_factors = []
        for factor, definition in zip(comparison_factors, factor_definitions):
            key = factor.lower().replace(" ", "_").replace("/", "_")
            value = product.get(key, "Not found")
            extracted_factors.append({
                "name": factor,
                "value": value,
                "definition": definition.dict(),
            })
        formatted_product["extracted_factors"] = extracted_factors
        formatted_products.append(formatted_product)
        
    return formatted_products
