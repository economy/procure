from typing import List
from tavily import TavilyClient  # type: ignore[import]
import os


def execute_search_for_solutions(
    product_category: str, comparison_factors: List[str]
) -> List[str]:
    """
    Uses the Tavily API to search for product/service solutions based on a category
    and specific comparison factors.

    Args:
        product_category: The type of product to research (e.g., "CRM software").
        comparison_factors: A list of specific factors to research.

    Returns:
        A list of relevant URLs.
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")

    client = TavilyClient(api_key=tavily_api_key)

    # Refine the search query for better accuracy and brevity
    search_query = f"top {product_category} solutions comparison"

    response = client.search(
        query=search_query,
        search_depth="advanced",
        max_results=7,
        include_answer=True,
        include_raw_content=False,
        topic="general",
    )

    # Extract URLs from the search results
    urls = [result["url"] for result in response["results"]]
    return urls 