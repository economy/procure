import asyncio
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

ProcessingType = Literal["categorize", "summarize_prose", "summarize_keywords", "none"]


class FactorAnalysis(BaseModel):
    """
    Analyzes a factor to determine the correct processing method and,
    if applicable, a list of categories.
    """

    processing_type: ProcessingType = Field(
        ...,
        description="The type of processing to apply to this factor's value.",
    )
    categories: Optional[List[str]] = Field(
        None,
        description="If categorizable, a list of 3-5 sensible categories.",
    )


class CategorizedFactor(BaseModel):
    category: str = Field(..., description="The most fitting category from the list.")


class ProseSummary(BaseModel):
    summary: str = Field(..., description="A concise, one-sentence summary.")


class KeywordSummary(BaseModel):
    summary_tags: List[str] = Field(..., description="A list of 1-3 word keywords.")


async def analyze_factor_type(factor_name: str, api_key: str) -> FactorAnalysis:
    """
    Determines how to process a factor based on its name.
    """
    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)
    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a data analysis expert. Your job is to determine how to process a data field based on its name. "
            "Choose one of four processing types: 'categorize', 'summarize_prose', 'summarize_keywords', or 'none'.\n"
            "- Use 'categorize' for fields with a limited set of options (e.g., 'Pricing Model', 'Open Source'). Also generate 3-5 sensible categories for it.\n"
            "- Use 'summarize_prose' for descriptive fields that should be a short sentence (e.g., 'Key Use Case', 'Product Description').\n"
            "- Use 'summarize_keywords' for fields that list multiple features where a few keywords are a good summary.\n"
            "- Use 'none' for everything else, especially identifiers or already short values."
        ),
        output_type=FactorAnalysis,
    )
    result = await agent.run(f"Analyze this factor: '{factor_name}'")
    return result.output


async def process_value(factor_name: str, value: Any, api_key: str) -> Any:
    """
    Intelligently processes a value based on an analysis of its factor name.
    It can categorize, summarize into prose, or summarize into keywords.
    Non-string values are passed through untouched.
    """
    if not isinstance(value, str):
        return value  # Pass through non-strings untouched
    
    # Also pass through short strings that don't need summarization
    # If a factor that is typically complex (like pricing) is returned as a single string,
    # it's likely a descriptive fallback from the source. Preserve it.
    complex_keywords = ["pricing", "plan", "tier", "subscription"]
    if any(keyword in factor_name.lower() for keyword in complex_keywords):
        return value
        
    if "not found" in value.lower() or "not applicable" in value.lower():
        return value

    try:
        analysis = await analyze_factor_type(factor_name, api_key)
        provider = GoogleGLAProvider(api_key=api_key)
        llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)

        if analysis.processing_type == "categorize" and analysis.categories:
            agent = Agent(
                model=llm,
                system_prompt=f"Classify the following text into one of these categories: {', '.join(analysis.categories)}.",
                output_type=CategorizedFactor,
            )
            result = await agent.run(f"Text to classify: '{value}'")
            return result.output.category

        elif analysis.processing_type == "summarize_prose":
            agent = Agent(
                model=llm,
                system_prompt="Summarize the following text into a single, concise sentence.",
                output_type=ProseSummary,
            )
            result = await agent.run(f"Text to summarize: '{value}'")
            return result.output.summary

        elif analysis.processing_type == "summarize_keywords":
            agent = Agent(
                model=llm,
                system_prompt="Summarize the following text into a list of 1-3 descriptive keywords.",
                output_type=KeywordSummary,
            )
            result = await agent.run(f"Text to summarize: '{value}'")
            return ", ".join(result.output.summary_tags)

    except Exception as e:
        # If any part of the dynamic processing fails, just return the original value.
        print(f"Processing failed for '{factor_name}', returning original value. Error: {e}")
        return value

    return value # Default to returning the original value if processing_type is 'none'


async def process_data(
    extracted_data: List[Dict[str, Any]], api_key: str
) -> List[Dict[str, Any]]:
    """
    Iterates through extracted data, dynamically processing values.
    """
    processing_tasks = []
    for product in extracted_data:
        for factor in product.get("extracted_factors", []):
            task = process_value(factor["name"], factor["value"], api_key)
            processing_tasks.append(task)

    processed_values = await asyncio.gather(*processing_tasks)

    value_iterator = iter(processed_values)
    for product in extracted_data:
        for factor in product.get("extracted_factors", []):
            factor["value"] = next(value_iterator)

    return extracted_data
