import asyncio
from exa_py import Exa
import os
from typing import List, Dict, Any
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider


class FactorSchema(BaseModel):
    """Defines the JSON schema for a single comparison factor."""

    property_schema: Dict[str, Any] = Field(
        ...,
        description="The JSON schema for this factor, e.g., {'type': 'string'}.",
    )


async def determine_factor_schema(factor_name: str, api_key: str) -> Dict[str, Any]:
    """
    Dynamically determines the appropriate JSON schema for a given factor.
    """
    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)
    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a JSON schema expert. Your task is to generate a schema for a data field based on its name. "
            "For most fields, use `{'type': 'string'}`. "
            "If the field implies a list of priced items (e.g., 'Subscription Plans', 'Pricing Tiers'), "
            "generate a schema for an array of objects with 'tier_name' (string) and 'price' (string). "
            "Ensure 'price' is a string to accommodate non-numeric values like 'Custom'."
        ),
        output_type=FactorSchema,
    )
    try:
        result = await agent.run(f"Generate schema for: '{factor_name}'")
        return result.output.property_schema
    except Exception as e:
        logger.warning(
            f"Schema generation for '{factor_name}' failed, defaulting to string. Error: {e}"
        )
        return {"type": "string", "description": factor_name}


async def search_and_extract(
    product_category: str, comparison_factors: List[str], api_key: str
) -> List[Dict[str, Any]]:
    """
    Uses Exa to find and extract structured information based on a dynamically
    generated schema and a highly descriptive, dynamically generated prompt.
    """
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        raise ValueError("EXA_API_KEY environment variable not set")
    exa = Exa(api_key=exa_api_key)

    # --- Dynamic Schema and Instruction Generation ---
    schema_tasks = [
        determine_factor_schema(factor, api_key) for factor in comparison_factors
    ]
    schemas = await asyncio.gather(*schema_tasks)

    properties = {"product_name": {"type": "string", "description": "The product name."}}
    instruction_lines = [
        f"Find and compare the leading software solutions for '{product_category}'.",
        "For each solution, extract the following information:",
    ]

    for factor, schema in zip(comparison_factors, schemas):
        key = factor.lower().replace(" ", "_").replace("/", "_")
        properties[key] = schema
        
        # Create a user-friendly description for the prompt
        description = factor
        if schema.get("type") == "array":
            description += " (extract a list of all available tiers with their names and prices)"
        
        properties[key]["description"] = description
        instruction_lines.append(f"- **{factor}**: {description}")

    instruction_lines.append("\nIf a value isn't found, use 'Not Found'.")
    instructions = "\n".join(instruction_lines)
    
    output_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["products"],
        "properties": {
            "products": {
                "type": "array",
                "items": {"type": "object", "properties": properties},
            }
        },
    }

    # --- Exa Research Task ---
    task = exa.research.create_task(
        instructions=instructions, output_schema=output_schema, model="exa-research"
    )
    logger.info(f"Created Exa research task with ID: {task.id}")
    result = exa.research.poll_task(task.id)
    logger.debug(f"Received final result from Exa research poll: {result.data}")

    # --- Result Formatting ---
    if result.data and "products" in result.data:
        formatted_products = []
        for product in result.data["products"]:
            formatted_product = {"product_name": product.get("product_name")}
            extracted_factors = []
            for factor in comparison_factors:
                key = factor.lower().replace(" ", "_").replace("/", "_")
                value = product.get(key, "Not found")
                extracted_factors.append({"name": factor, "value": value})
            formatted_product["extracted_factors"] = extracted_factors
            formatted_products.append(formatted_product)
        return formatted_products

    return []
