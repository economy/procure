from pydantic import BaseModel, Field

class EnrichedQuery(BaseModel):
    """
    A model to hold the clarified query and potential comparison factors.
    """
    clarified_query: str = Field(
        ...,
        description="The clarified and enriched search query."
    )
    comparison_factors: list[str] = Field(
        default_factory=list,
        description="A list of potential comparison factors derived from the query."
    )

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