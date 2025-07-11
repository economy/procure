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