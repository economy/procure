from typing import Any, Dict, List

from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

class EnrichedData(BaseModel):
    """A model to hold the refined, corrected, and completed data for a single product."""
    product_name: str = Field(..., description="The name of the product.")
    extracted_factors: List[Dict[str, Any]] = Field(
        ...,
        description="The list of all factors for the product, updated with enriched information.",
    )

async def enrich_product_data(
    product_data: Dict[str, Any], page_content: str, api_key: str
) -> Dict[str, Any]:
    """
    Refines and enriches a product's data using the content of a specific,
    authoritative webpage (e.g., a pricing page).

    Args:
        product_data: The existing dictionary of data for a single product.
        page_content: The full text content of the authoritative page.
        api_key: The Google API key for the LLM.

    Returns:
        The updated product data dictionary.
    """
    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)

    # Prepare a string representation of the current data to provide as context
    current_data_str = ", ".join(
        f"{factor['name']}: {factor['value']}"
        for factor in product_data.get("extracted_factors", [])
    )

    system_prompt = (
        "You are a data enrichment specialist. Your job is to correct and complete a dataset for a specific product using the full text from its official webpage as the source of truth.\n"
        "1.  **Cross-reference**: Compare the 'Current Data' with the 'Source Webpage Content'.\n"
        "2.  **Correct**: Fix any inaccuracies in the 'Current Data' based on the webpage. For example, if 'Pricing Basis' is 'Freemium' but the webpage shows detailed paid plans, update it.\n"
        "3.  **Complete**: Fill in any missing information, especially for complex fields like 'Subscription Plans'. Extract all tier names, prices, and key features for each plan.\n"
        "4.  **Return the Full, Corrected Dataset**: Your final output should be the complete, authoritative data for the product."
    )
    
    agent = Agent(model=llm, system_prompt=system_prompt, output_type=EnrichedData)

    try:
        query = (
            f"Please enrich the following data:\n"
            f"**Product Name**: {product_data.get('product_name')}\n"
            f"**Current Data**: {current_data_str}\n\n"
            f"**Source Webpage Content**:\n"
            f"---BEGIN WEBPAGE---\n"
            f"{page_content}\n"
            f"---END WEBPAGE---"
        )
        result = await agent.run(query)
        logger.info(f"Successfully enriched data for {product_data.get('product_name')}")
        return result.output.dict()
    except Exception as e:
        logger.warning(
            f"Could not enrich data for {product_data.get('product_name')}. Returning original data. Error: {e}"
        )
        return product_data

