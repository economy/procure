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
            "You are a procurement analysis expert. Your job is to evaluate a user's query about a software product category and clarify it for a search engine.\n"
            "1.  **Analyze**: Determine if the query is specific enough (e.g., 'CRM software', 'API gateways for microservices').\n"
            "2.  **Clarify, Don't Change**: If specific, make only minimal, additive changes to improve it for search. **Never change the core subject of the query.** For example, 'CICD platforms' should become something like 'top CICD platforms for enterprise', not 'CRM software'.\n"
            "3.  **Flag Ambiguity**: If the query is too broad (e.g., 'software', 'tools'), set 'needs_clarification' to true and formulate a question to ask the user for more detail."
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
