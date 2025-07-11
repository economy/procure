from pydantic import BaseModel, Field
from typing import Optional

class EnrichedQuery(BaseModel):
    """
    Holds the output of the Clarification Agent.
    """
    clarified_query: str = Field(..., description="The refined query for the search agent.")
    needs_clarification: bool = Field(..., description="True if the query is too ambiguous and requires user input.")
    question_for_user: Optional[str] = Field(None, description="The question to ask the user if clarification is needed.")
    comparison_factors: list[str] = Field(default_factory=list, description="The list of factors to use for the analysis.")

class Factor(BaseModel):
    """A single extracted comparison factor and its value."""
    name: str = Field(..., description="The name of the comparison factor.")
    value: str = Field(..., description="The extracted value for the factor. If the information is not found, this should be 'Not found'.")

class ExtractedProduct(BaseModel):
    """A model to store all data extracted from a single webpage."""
    product_name: str = Field(..., description="The name of the product or service found.")
    extracted_factors: list[Factor] = Field(
        default_factory=list,
        description="A list of extracted key-value pairs for each comparison factor."
    )