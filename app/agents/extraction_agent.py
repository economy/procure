from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
import httpx
from bs4 import BeautifulSoup

from app.models.queries import ExtractedProduct, Factor


async def _fetch_and_parse_url(url: str) -> str:
    """Fetches the content of a URL and returns the clean text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"Error fetching or parsing URL {url}: {e}")
        return ""

async def extract_information(
    url: str, 
    comparison_factors: list[str],
    api_key: str
) -> ExtractedProduct:
    """
    Extracts information from a URL for a list of comparison factors in a single, efficient call.
    """
    page_content = await _fetch_and_parse_url(url)
    if not page_content:
        return ExtractedProduct(product_name="N/A", extracted_factors=[Factor(name="error", value="Failed to fetch content")])

    provider = GoogleProvider(api_key=api_key)
    llm = GoogleModel(model_name="gemini-1.5-flash", provider=provider)
    
    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a data extraction expert. Your task is to analyze the provided text "
            "and extract specific information. For each factor, you MUST provide a value that is between 1 and 5 words. "
            "Be extremely concise. For lists of features, provide only the top 3-4 keywords. "
            "If you cannot find information for a factor, your response must be 'Not found'."
        ),
        output_type=ExtractedProduct,
    )

    prompt = (
        f"From the following text, extract the product name and the information for these factors: {', '.join(comparison_factors)}.\n\n"
        f"--- Page Content ---\n{page_content[:10000]}\n--- End Content ---"
    )
    
    response = await agent.run(prompt)
    return response.output 