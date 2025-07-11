from pydantic import BaseModel, Field
from typing import Literal, Optional

class EnrichedQuery(BaseModel):
    """
    A model to hold the clarified query and the selected product category key.
    """
    clarified_query: str = Field(
        ...,
        description="The clarified and enriched search query."
    )
    product_category_key: Optional[Literal["crm", "cloud_monitoring", "api_gateway"]] = Field(
        None,
        description="The matching product category key from the available templates. Null if ambiguous."
    )
    comparison_factors: list[str] = Field(
        default_factory=list,
        description="A list of comparison factors loaded from the selected template."
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