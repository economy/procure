from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.models.queries import EnrichedQuery
from app.utils import load_factor_templates


async def clarify_query(query: str, api_key: str) -> EnrichedQuery:
    """
    Uses an LLM to assess the user's query. If the query is specific enough, it
    enriches it for search and attaches a generic list of comparison factors.
    If the query is too ambiguous, it flags it for human clarification.
    """
    templates = load_factor_templates()
    generic_factors = templates.get("generic", [])

    provider = GoogleProvider(api_key=api_key)
    llm = GoogleModel(model_name="gemini-1.5-flash", provider=provider)

    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a procurement analysis expert. Your job is to evaluate a user's query about a software product. "
            "If the query is specific enough to yield meaningful search results (e.g., 'CRM software', 'API gateways for microservices'), "
            "set 'needs_clarification' to false and refine the query for a search engine. "
            "If the query is too broad (e.g., 'software', 'tools'), set 'needs_clarification' to true and formulate a 'question_for_user' "
            "to ask for more detail."
        ),
        output_type=EnrichedQuery,
    )

    response = await agent.run(
        f"Evaluate and refine the following product query: '{query}'"
    )

    enriched_result = response.output
    if not enriched_result.needs_clarification:
        enriched_result.comparison_factors = generic_factors

    return enriched_result 