from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.models.queries import EnrichedQuery
from app.utils import load_factor_templates


async def clarify_query(product_category: str, api_key: str) -> EnrichedQuery:
    """
    Uses a Pydantic AI agent to clarify the user's query and match it to a
    predefined category template.
    """
    templates = load_factor_templates()
    category_keys = list(templates.keys())

    provider = GoogleProvider(api_key=api_key)
    llm = GoogleModel(model_name="gemini-1.5-flash", provider=provider)
    
    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a routing assistant. Your job is to take a user's product category "
            "and match it to the most appropriate category from a predefined list. "
            "If the query is ambiguous or doesn't fit any category, you must ask a clarifying question "
            "and set the product_category_key to null. Otherwise, you must refine the user's query to be more specific. "
            f"The available categories are: {', '.join(category_keys)}."
        ),
        output_type=EnrichedQuery,
    )

    response = await agent.run(
        f"Clarify and categorize the following product query: '{product_category}'"
    )

    # Attach the factors from the selected template if a category was determined
    enriched_result = response.output
    if enriched_result.product_category_key:
        selected_factors = templates.get(enriched_result.product_category_key, [])
        enriched_result.comparison_factors = selected_factors

    return enriched_result 