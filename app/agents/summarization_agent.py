from typing import List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import GoogleModel
from pydantic_ai.providers import GoogleProvider
import asyncio

class SummarizedFactor(BaseModel):
    """A model to hold a summarized value, represented as a list of concise tags."""
    summary_tags: List[str] = Field(..., description="A list of 1-3 word tags summarizing the original text.")

async def summarize_value(value: str, api_key: str) -> str:
    """
    If a value is a long string, this function uses an LLM to summarize it 
    into a few concise tags. Otherwise, it returns the original value.

    Args:
        value: The string value to potentially summarize.
        api_key: The Google API key.

    Returns:
        A summarized string of tags, or the original value.
    """
    # Only summarize strings that are likely to be long-form text.
    if not isinstance(value, str) or len(value.split()) < 10:
        return value

    provider = GoogleProvider(api_key=api_key)
    llm = GoogleModel(model_name="gemini-1.5-flash", provider=provider)
    
    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a data summarization expert. Your task is to read the provided text "
            "and summarize it into a short list of 1-3 word descriptive tags. "
            "Focus on the most important keywords and concepts."
        ),
        output_type=SummarizedFactor,
    )

    try:
        response = await agent.run(f"Summarize the following text: '{value}'")
        return ", ".join(response.output.summary_tags)
    except Exception:
        # If summarization fails for any reason, return the original value.
        return value

async def process_and_summarize_data(
    extracted_data: List[Dict[str, Any]], 
    api_key: str
) -> List[Dict[str, Any]]:
    """
    Iterates through extracted data and summarizes long-form text fields.

    Args:
        extracted_data: The list of product data from the search_and_extract agent.
        api_key: The Google API key.

    Returns:
        The same list of data, but with long text fields summarized.
    """
    summarization_tasks = []
    
    # Create a list of all values that need summarization
    values_to_summarize = []
    for product in extracted_data:
        for factor in product.get("extracted_factors", []):
            values_to_summarize.append(factor["value"])

    # Run summarization tasks in parallel
    summarized_values = await asyncio.gather(
        *[summarize_value(value, api_key) for value in values_to_summarize]
    )
    
    # Reconstruct the data with the summarized values
    value_iterator = iter(summarized_values)
    for product in extracted_data:
        for factor in product.get("extracted_factors", []):
            factor["value"] = next(value_iterator)
            
    return extracted_data
