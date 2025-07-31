from exa_py import Exa
import os
from typing import List, Dict, Any
from loguru import logger

def search_and_extract(
    product_category: str, 
    comparison_factors: List[str]
) -> List[Dict[str, Any]]:
    """
    Uses the Exa API's research endpoint to create and poll an asynchronous task
    that finds and extracts structured information about product/service solutions.

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

    instructions = f"What are the leading solutions for '{product_category}'?"

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

    # 1. Create the asynchronous research task
    task = exa.research.create_task(
        instructions=instructions,
        output_schema=output_schema,
        model="exa-research"
    )
    
    logger.info(f"Created Exa research task with ID: {task.id}")

    # 2. Poll the task until it's complete. This returns the final result.
    result = exa.research.poll_task(task.id)
    
    logger.debug(f"Received final result from Exa research poll: {result}")

    # The structured JSON is in the `.data` attribute of the completed task result.
    if result and result.data and isinstance(result.data, dict) and 'products' in result.data:
        structured_data = result.data
        formatted_products = []
        for product in structured_data.get('products', []):
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
