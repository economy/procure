from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from app.models.queries import EnrichedQuery
from app.utils import load_factor_templates


async def clarify_query(query: str, api_key: str) -> EnrichedQuery:
    """
    Uses an LLM to assess the user's query. It can only pass the query through
    verbatim or flag it for clarification. It cannot modify the query.
    """
    templates = load_factor_templates()
    generic_factors = templates.get("generic", [])

    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)

    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a search query assistant. Your only job is to evaluate a user's query about a software product category. You have two possible outputs:\n"
            "1.  If the query is specific and clear (e.g., 'CRM software', 'API gateways'), set 'needs_clarification' to false and return the user's query **VERBATIM** in the 'clarified_query' field.\n"
            "2.  If the query is too generic (e.g., 'software', 'tools'), set 'needs_clarification' to true and formulate a question for the user.\n"
            "**ABSOLUTELY DO NOT MODIFY, REFINE, OR CHANGE THE USER'S ORIGINAL QUERY IN ANY WAY.**"
        ),
        output_type=EnrichedQuery,
    )

    response = await agent.run(
        f"Evaluate the following product query: '{query}'"
    )

    enriched_result = response.output
    if not enriched_result.needs_clarification:
        enriched_result.comparison_factors = generic_factors

    logger.info(f"Clarification agent processing for query '{query}': Result -> '{enriched_result.clarified_query}', Needs Clarification -> {enriched_result.needs_clarification}")
    return enriched_result
