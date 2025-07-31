from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

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

    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)

    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a search query enhancement expert. Your job is to refine a user's query for a software product category. You have two rules:\n"
            "1.  **NEVER CHANGE THE CORE SUBJECT.** 'CICD platforms' can become 'top CICD platforms for enterprise', but it can NEVER become 'CRM software'. If the user asks for X, the output must be about X.\n"
            "2.  **BE MINIMAL.** Only add 1-3 descriptive keywords if it improves clarity for a search engine. Otherwise, return the original query verbatim.\n"
            "If the query is too generic (e.g., 'software'), set 'needs_clarification' to true and ask a clarifying question."
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
