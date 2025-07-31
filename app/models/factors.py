from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# --- Core Definitions ---

ProcessingType = Literal["categorize", "summarize_prose", "summarize_keywords", "none"]


class FactorDefinition(BaseModel):
    """
    Defines the complete handling logic for a single comparison factor,
    from its data schema for extraction to its final processing type.
    This model serves as the single source of truth for each factor.
    """

    schema: Dict[str, Any] = Field(
        ...,
        description="The JSON schema for this factor, e.g., {'type': 'string'} or a schema for a list of objects.",
    )
    processing_type: ProcessingType = Field(
        ...,
        description="The type of processing to apply to this factor's value after extraction.",
    )
    categories: Optional[List[str]] = Field(
        None,
        description="If 'processing_type' is 'categorize', a list of 3-5 sensible categories for classification.",
    )

# --- Pydantic AI Output Models for Processing ---

class CategorizedFactor(BaseModel):
    """The result of a categorization task."""
    category: str = Field(..., description="The most fitting category from the list.")


class ProseSummary(BaseModel):
    """The result of a prose summarization task."""
    summary: str = Field(..., description="A concise, one-sentence summary.")


class KeywordSummary(BaseModel):
    """The result of a keyword summarization task."""
    summary_tags: List[str] = Field(..., description="A list of 1-3 word keywords.")
