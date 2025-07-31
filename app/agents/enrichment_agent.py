from typing import Any, Dict, List

from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from app.models.factors import Factor


class EnrichedData(BaseModel):
    """A model to hold the refined, corrected, and completed data for a single product."""
    product_name: str = Field(..., description="The name of the product.")
    extracted_factors: List[Factor] = Field(
        ...,
        description="The list of all factors for the product, updated with enriched information.",
    )

async def enrich_product_data(
    product_data: Dict[str, Any], page_content: str, api_key: str
) -> Dict[str, Any]:
    """
    Refines and enriches a product's data using the content of a specific,
    authoritative webpage (e.g., a pricing page).
    """
    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)

    current_data_str = ", ".join(
        f"{factor['name']}: {factor['value']}"
        for factor in product_data.get("extracted_factors", [])
    )

    system_prompt = (
        "You are a data enrichment specialist. Your job is to correct and complete a structured dataset for a product using a webpage as a source of truth.\n"
        "1.  **Analyze**: Compare the 'Current Data' with the 'Source Webpage'.\n"
        "2.  **Correct & Complete**: Fix inaccuracies and fill in missing information in the 'Current Data', especially for complex fields like 'Subscription Plans'.\n"
        "3.  **Return Full Structured Data**: Your final output must be the complete, authoritative, and structured data for the product. Ensure every original factor is present in the output."
    )
    
    agent = Agent(model=llm, system_prompt=system_prompt, output_type=EnrichedData)

    try:
        query = (
            f"Enrich the following dataset:\n"
            f"**Product Name**: {product_data.get('product_name')}\n"
            f"**Current Data**: {current_data_str}\n\n"
            f"**Source Webpage Content**:\n{page_content}"
        )
        result = await agent.run(query)
        logger.info(f"Successfully enriched data for {product_data.get('product_name')}")
        return result.output.dict()
    except Exception as e:
        logger.warning(
            f"Could not enrich data for {product_data.get('product_name')}. Returning original data. Error: {e}"
        )
        return product_data
