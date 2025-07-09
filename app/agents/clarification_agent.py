from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from typing import List
import os

class EnrichedQuery(BaseModel):
    """
    A model to hold the clarified query and potential comparison factors.
    """
    clarified_query: str = Field(
        ...,
        description="The clarified and enriched search query."
    )
    comparison_factors: List[str] = Field(
        default_factory=list,
        description="A list of potential comparison factors derived from the query."
    )


async def clarify_query(product_category: str, api_key: str) -> EnrichedQuery:
    """
    Uses a Pydantic AI agent to enrich the user's query.
    """
    provider = GoogleProvider(api_key=api_key)
    llm = GoogleModel(model_name="gemini-1.5-flash", provider=provider)
    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a procurement assistant. Your job is to take a user's vague product category "
            "and transform it into a clarified, specific, and actionable query. "
            "You must also identify the product category and suggest potential comparison factors."
        ),
        output_type=EnrichedQuery,
    )

    response = await agent.run(
        f"Clarify and enrich the following product category: {product_category}"
    )

    return response.output 