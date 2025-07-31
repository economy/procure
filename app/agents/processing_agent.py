import asyncio
from typing import Any, Dict, List

from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from app.models.factors import (
    CategorizedFactor,
    FactorDefinition,
    KeywordSummary,
    ProseSummary,
)


async def process_value(
    factor_definition: FactorDefinition, value: Any, api_key: str
) -> Any:
    """
    Refines a value based on the specific processing_type defined in its
    FactorDefinition. This agent does not guess; it follows instructions.
    Structured data (lists, objects) or values marked 'none' are passed through.
    """
    processing_type = factor_definition.processing_type

    if processing_type == "none" or not isinstance(value, str):
        return value  # Pass through non-strings or if no processing is needed

    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)

    try:
        if processing_type == "categorize" and factor_definition.categories:
            agent = Agent(
                model=llm,
                system_prompt=f"Classify the following text into one of these categories: {', '.join(factor_definition.categories)}.",
                output_type=CategorizedFactor,
            )
            result = await agent.run(f"Text to classify: '{value}'")
            return result.output.category

        elif processing_type == "summarize_prose":
            agent = Agent(
                model=llm,
                system_prompt="Summarize the following text into a single, concise sentence.",
                output_type=ProseSummary,
            )
            result = await agent.run(f"Text to summarize: '{value}'")
            return result.output.summary

        elif processing_type == "summarize_keywords":
            agent = Agent(
                model=llm,
                system_prompt="Summarize the following text into a list of 1-3 descriptive keywords.",
                output_type=KeywordSummary,
            )
            result = await agent.run(f"Text to summarize: '{value}'")
            return ", ".join(result.output.summary_tags)

    except Exception as e:
        logger.warning(
            f"Processing for factor failed, returning original value. Error: {e}"
        )
        return value

    return value


async def process_data(
    extracted_data: List[Dict[str, Any]], api_key: str
) -> List[Dict[str, Any]]:
    """
    Iterates through extracted data, refining values based on the
    processing instructions in their attached FactorDefinition.
    """
    processing_tasks = []
    for product in extracted_data:
        for factor in product.get("extracted_factors", []):
            definition = FactorDefinition(**factor["definition"])
            task = process_value(definition, factor["value"], api_key)
            processing_tasks.append(task)

    processed_values = await asyncio.gather(*processing_tasks)

    value_iterator = iter(processed_values)
    for product in extracted_data:
        for factor in product.get("extracted_factors", []):
            factor["value"] = next(value_iterator)
            del factor["definition"]  # Clean up definition before final output

    return extracted_data
