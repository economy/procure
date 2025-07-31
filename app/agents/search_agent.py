from exa_py import Exa
import os
from typing import List, Dict, Any

def search_and_extract(
    product_category: str, 
    comparison_factors: List[str]
) -> List[Dict[str, Any]]:
    """
    Uses the Exa API's answer endpoint to find and extract information about 
    product/service solutions based on a category and comparison factors.

    Args:
        product_category: The type of product to research (e.g., "CRM software").
        comparison_factors: A list of specific factors to research.

    Returns:
        A list of dictionaries, where each dictionary represents a product 
        and its extracted information.
    """
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        raise ValueError("EXA_API_KEY environment variable not set")

    exa = Exa(api_key=exa_api_key)

    # Construct a detailed query for the answer endpoint
    factors_str = ", ".join(comparison_factors)
    query = (
        f"For the product category '{product_category}', find 5-10 leading solutions. "
        f"For each solution, provide its name and the following information: {factors_str}."
    )

    # Define the structured output we expect from Exa
    output_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["products"],
        "properties": {
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["product_name"] + [f.lower().replace(' ', '_') for f in comparison_factors],
                    "properties": {
                        "product_name": {"type": "string", "description": "The name of the product."},
                        **{
                            f.lower().replace(' ', '_'): {"type": "string", "description": f}
                            for f in comparison_factors
                        }
                    }
                }
            }
        }
    }

    response = exa.answer(
        query=query,
        output_schema=output_schema,
    )
    
    # The structured answer is in the `.answer` property
    if response.answer and 'products' in response.answer:
        # Convert the snake_case keys back to the original factor names
        formatted_products = []
        for product in response.answer['products']:
            formatted_product = {"product_name": product.get("product_name")}
            extracted_factors = []
            for factor in comparison_factors:
                key = factor.lower().replace(' ', '_')
                extracted_factors.append({
                    "name": factor,
                    "value": product.get(key, "Not found")
                })
            formatted_product["extracted_factors"] = extracted_factors
            formatted_products.append(formatted_product)
        return formatted_products

    return []
