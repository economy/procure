from typing import List
from tavily import TavilyClient  # type: ignore[import]
import os

def search_for_products(query: str, api_key: str) -> List[str]:
    """
    Uses the Tavily API to search for products online and returns a list of URLs.
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")

    client = TavilyClient(api_key=tavily_api_key)
    
    # For now, we are not using the google api_key, but we keep it in the signature
    # for consistency with the other agents.

    response = client.search(query=query, search_depth="basic", max_results=5)
    
    # Extract URLs from the search results
    urls = [result["url"] for result in response["results"]]
    return urls 