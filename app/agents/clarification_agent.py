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
            "You are an intelligent routing assistant. Your primary goal is to categorize a user's product query "
            "into one of the following predefined categories: "
            f"{', '.join(category_keys)}. "
            "You must make a choice if the query clearly fits a category. "
            "Only if the query is highly ambiguous or does not fit any category, you must ask a clarifying question "
            "and set the product_category_key to null. "
            "Finally, refine the user's query to be more specific based on the chosen category."
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