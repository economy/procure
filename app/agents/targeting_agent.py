from typing import List, Dict, Any

from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

class TargetedQueries(BaseModel):
    """A model to hold a list of targeted search queries for enriching data."""
    queries: List[str] = Field(
        ...,
        description="A list of 1-3 highly specific search queries to find authoritative information and fill data gaps.",
    )

async def generate_enrichment_queries(
    product_data: Dict[str, Any], api_key: str
) -> List[str]:
    """
    Analyzes a product's current data to identify weaknesses and generates
    targeted search queries to find missing or incomplete information.

    Args:
        product_data: The dictionary of data for a single product.
        api_key: The Google API key for the LLM.

    Returns:
        A list of specific search query strings.
    """
    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)

    current_data_str = ", ".join(
        f"{factor['name']}: {factor['value']}"
        for factor in product_data.get("extracted_factors", [])
    )

    system_prompt = (
        "You are a research strategist. Your job is to analyze an incomplete dataset for a product and generate highly specific search queries to find the missing information.\n"
        "1.  **Analyze the Data**: Look for vague fields, logical inconsistencies (e.g., 'Freemium' with no free plan listed), or missing details, especially for important factors like 'Subscription Plans', 'Pricing', or 'Key Features'.\n"
        "2.  **Generate Queries**: Create a list of 1-3 precise Google search queries to find the most authoritative pages (like official pricing or feature pages) that will fill these gaps.\n"
        "   - Good Query Example: 'official CircleCI pricing and plans for enterprise'\n"
        "   - Bad Query Example: 'CircleCI info'\n"
        "3.  **Focus on Authority**: The queries should aim to find the product's official website."
    )
    
    agent = Agent(model=llm, system_prompt=system_prompt, output_type=TargetedQueries)

    try:
        query = (
            f"Analyze the following data and generate targeted search queries to find missing information:\n"
            f"**Product Name**: {product_data.get('product_name')}\n"
            f"**Current Data**: {current_data_str}"
        )
        result = await agent.run(query)
        logger.info(f"Generated {len(result.output.queries)} enrichment queries for {product_data.get('product_name')}")
        return result.output.queries
    except Exception as e:
        logger.warning(
            f"Could not generate enrichment queries for {product_data.get('product_name')}. Error: {e}"
        )
        return []
