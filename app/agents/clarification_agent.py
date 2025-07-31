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
            "1.  **NEVER CHANGE THE CORE SUBJECT.** 'CICD platforms' can become 'top CICD platforms 2025', but it can NEVER become 'CRM software'.\n"
            "2.  **BE MINIMAL & GENERIC.** Only add generic, non-speculative keywords (like 'top', 'best', or a year) if it improves clarity. **NEVER add industry-specific terms like 'for enterprise' or 'for small business'.** The user will provide that context if needed. If no improvement is possible, return the original query verbatim.\n"
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
