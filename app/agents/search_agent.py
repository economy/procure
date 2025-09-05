import asyncio
import json
from typing import Any, Dict, List
import os

from exa_py import Exa
from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from app.models.factors import FactorDefinition


def is_valid_software_product(product_name: str) -> bool:
    """
    Validates that a product name represents an actual software product,
    not an article title or generic term.
    """
    if not product_name or len(product_name) < 3:
        return False
    
    # Skip article-like titles
    article_indicators = [
        "what is", "how to", "guide", "tutorial", "introduction", "overview",
        "explained", "discussion", "opinion", "review", "comparison", "vs ",
        "versus", "differences", "top 10", "best of", "list of", "complete guide",
        "ultimate guide", "everything you need", "getting started", "beginner's",
        "advanced", "comprehensive", "in-depth", "detailed", "step by step",
        "tutorial", "walkthrough", "explanation", "analysis", "breakdown"
    ]
    
    product_lower = product_name.lower()
    
    # Check for article indicators
    if any(indicator in product_lower for indicator in article_indicators):
        return False
    
    # Skip generic terms
    generic_terms = [
        "software", "tools", "platforms", "solutions", "services", "products",
        "frameworks", "libraries", "technologies", "systems", "applications",
        "programs", "utilities", "resources", "options", "alternatives"
    ]
    
    if product_lower in generic_terms:
        return False
    
    # Must contain at least one letter and not be just numbers
    if not any(c.isalpha() for c in product_name):
        return False
    
    return True


async def determine_factor_definition(
    factor_name: str, api_key: str
) -> FactorDefinition:
    """
    Dynamically determines the complete definition for a factor, including its
    JSON schema and the appropriate processing type, using a single LLM call.
    """
    provider = GoogleGLAProvider(api_key=api_key)
    llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)
    agent = Agent(
        model=llm,
        system_prompt=(
            "You are a data pipeline architect. Your job is to define how to extract and process a data field based on its name.\n"
            "1.  **Define the `factor_schema_json`**: For simple text, return a JSON string like `'{\\\"type\\\": \\\"string\\\"}'`. For fields implying a list (e.g., 'Subscription Plans'), return a JSON string for an array of objects, like `'{\\\"type\\\": \\\"array\\\", \\\"items\\\": {\\\"type\\\": \\\"object\\\", \\\"properties\\\": {\\\"tier_name\\\": {\\\"type\\\": \\\"string\\\"}, \\\"price\\\": {\\\"type\\\": \\\"string\\\"}}}}'`. Escape all quotes properly.\n"
            "2.  **Define the `processing_type`**: Choose 'categorize', 'summarize_prose', 'summarize_keywords', or 'none'.\n"
            "3.  **Define `categories`**: If you chose 'categorize', provide a list of 3-5 sensible category options."
        ),
        output_type=FactorDefinition,
    )
    try:
        result = await agent.run(f"Define handling for factor: '{factor_name}'")
        return result.output
    except Exception as e:
        logger.warning(
            f"Factor definition for '{factor_name}' failed, defaulting to basic string. Error: {e}"
        )
        return FactorDefinition(
            factor_schema_json='{"type": "string"}',
            processing_type="none",
            categories=None,
        )


async def search_and_extract(
    product_category: str, comparison_factors: List[str], api_key: str
) -> List[Dict[str, Any]]:
    """
    Uses Exa to find and extract structured information based on a dynamically
    generated schema from our new, intelligent FactorDefinition model.
    """
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        raise ValueError("EXA_API_KEY environment variable not set")
    
    logger.info(f"Using Exa API key: {exa_api_key[:8]}...")
    try:
        # Use v1 API - the exa-py library should handle v1 automatically
        exa = Exa(api_key=exa_api_key)
        logger.info(f"Exa client created successfully: {exa}")
    except Exception as e:
        logger.error(f"Failed to create Exa client: {e}")
        return []

    logger.info(f"Generating factor definitions for {len(comparison_factors)} factors")
    definition_tasks = [
        determine_factor_definition(factor, api_key) for factor in comparison_factors
    ]
    try:
        factor_definitions = await asyncio.gather(*definition_tasks)
        logger.info(f"Successfully generated {len(factor_definitions)} factor definitions")
    except Exception as e:
        logger.error(f"Failed to generate factor definitions: {e}")
        return []

    properties = {"product_name": {"type": "string", "description": "The product name."}}
    instruction_lines = [
        f"Find and compare 10-15 of the leading software solutions for '{product_category}'.",
        "For each solution, extract the following information based on the described schema:",
    ]

    for factor, definition in zip(comparison_factors, factor_definitions):
        key = factor.lower().replace(" ", "_").replace("/", "_")
        try:
            schema = json.loads(definition.factor_schema_json)
            properties[key] = schema
            instruction_lines.append(f"- **{factor}**: Extract this value based on the schema.")
        except json.JSONDecodeError:
            properties[key] = {"type": "string"}
            instruction_lines.append(f"- **{factor}**: Extract this value.")

    # Simplify the schema to avoid Exa's depth limit
    # Flatten complex nested structures to simple strings
    simplified_properties = {"product_name": {"type": "string"}}
    for factor, definition in zip(comparison_factors, factor_definitions):
        key = factor.lower().replace(" ", "_").replace("/", "_")
        # Always use simple string type to avoid depth issues
        simplified_properties[key] = {"type": "string", "description": f"Information about {factor}"}
    
    output_schema = {
        "type": "object",
        "required": ["products"],
        "properties": {
            "products": {
                "type": "array", 
                "items": {
                    "type": "object", 
                    "properties": simplified_properties
                }
            }
        },
    }
    instructions = "\n".join(instruction_lines)
    
    logger.info(f"Creating Exa research task with schema: {output_schema}")
    logger.info(f"Instructions: {instructions[:200]}...")

    try:
        # Use Exa's search_and_contents API instead of research tasks
        logger.info("Using Exa search_and_contents API for research")
        
        # Create search queries that target specific software products and comparisons
        search_queries = [
            f"{product_category} software comparison 2024",
            f"best {product_category} tools list",
            f"{product_category} platforms and solutions",
            f"top {product_category} software products",
            f"{product_category} alternatives comparison",
            f"{product_category} software directory",
            f"{product_category} tools marketplace"
        ]
        
        logger.info(f"Generated search queries: {search_queries}")
        
        all_results = []
        for query in search_queries:
            try:
                logger.info(f"Searching with query: {query}")
                search_results = exa.search_and_contents(
                    query=query,
                    num_results=5,  # Get more results per query
                    type="keyword",
                    use_autoprompt=True
                )
                
                if search_results.results:
                    logger.info(f"Found {len(search_results.results)} results for query: {query}")
                    all_results.extend(search_results.results)
                else:
                    logger.warning(f"No results found for query: {query}")
                    
            except Exception as e:
                logger.error(f"Error searching with query '{query}': {e}")
                logger.error(f"Exception type: {type(e)}")
                logger.error(f"Exception details: {str(e)}")
                continue
        
        if not all_results:
            logger.error("No search results found from any query")
            return []
        
        logger.info(f"Total search results collected: {len(all_results)}")
        logger.info(f"First few results: {[{'title': r.title, 'url': r.url} for r in all_results[:3]]}")
        
        # Use AI to extract product information from search results
        logger.info("Using AI to extract product information from search results")
        
        # Create a prompt for the AI to extract product information
        search_content = "\n\n".join([
            f"Title: {result.title}\nURL: {result.url}\nContent: {result.text[:1500] if result.text else 'No content'}"
            for result in all_results[:15]  # Use more results for better product discovery
        ])
        
        extraction_prompt = f"""
        You are a software product analyst. Extract actual software products, frameworks, and tools from the search results about "{product_category}".

        Search Results:
        {search_content}
        
        INSTRUCTIONS:
        1. Look through the article content to find specific software product names
        2. Extract individual framework/library/tool names mentioned in the articles
        3. Focus on actual software products that developers can use
        4. Each product should be a distinct software tool, framework, or platform
        5. Ignore article titles, discussions, and generic terms
        
        For each software product you find, extract:
        - Product name (exact official name as mentioned)
        - Brief description
        - Key features
        - Open source vs commercial status
        - Target use cases
        - Community info (if mentioned)
        
        Return a JSON array of products:
        [
            {{
                "product_name": "Exact Product Name",
                "description": "What this product does",
                "features": "Key features mentioned",
                "type": "Open Source/Commercial/Free",
                "use_cases": "Primary use cases",
                "community": "Community info if available"
            }}
        ]
        
        Find 8-12 distinct software products relevant to "{product_category}".
        """
        
        # Use the same LLM setup as the factor definition
        provider = GoogleGLAProvider(api_key=api_key)
        llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)
        agent = Agent(
            model=llm,
            system_prompt="You are an expert software product analyst. Extract actual software products from search results and return them as a valid JSON array. Always return valid JSON format.",
        )
        
        try:
            # Extract product information using AI
            result = await agent.run(extraction_prompt)  # type: ignore[assignment]
            # Handle the result properly
            if hasattr(result, 'data'):
                extracted_text = str(result.data)
            else:
                extracted_text = str(result)
            
            logger.info(f"AI extraction result: {extracted_text[:200]}...")
            
            # Parse the AI response to extract products
            products = []
            
            if extracted_text and len(extracted_text) > 50:
                try:
                    # Try to parse the AI response as JSON
                    # Look for JSON array in the response
                    import re
                    json_match = re.search(r'\[.*\]', extracted_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        ai_products = json.loads(json_str)
                        
                        logger.info(f"Successfully parsed {len(ai_products)} products from AI response")
                        
                        # Convert AI products to our format
                        for ai_product in ai_products:
                            if isinstance(ai_product, dict) and "product_name" in ai_product:
                                product_name = ai_product.get("product_name", "Unknown Product")
                                
                                # Validate that this is an actual software product
                                if not is_valid_software_product(product_name):
                                    logger.info(f"Skipping invalid product name: {product_name}")
                                    continue
                                
                                product = {
                                    "product_name": product_name,
                                    "url": "https://example.com",  # Will be enriched later
                                    "title": f"{product_name} - {product_category}",
                                    "text": f"{ai_product.get('description', '')} {ai_product.get('features', '')}".strip(),
                                }
                                
                                # Add factor information based on AI extraction
                                for factor in comparison_factors:
                                    key = factor.lower().replace(" ", "_").replace("/", "_")
                                    
                                    # Map AI extracted data to factors
                                    if "open source" in factor.lower() or "type" in factor.lower():
                                        product[key] = ai_product.get("type", "Information not available")
                                    elif "description" in factor.lower() or "features" in factor.lower():
                                        product[key] = ai_product.get("description", ai_product.get("features", "Information not available"))
                                    elif "use cases" in factor.lower() or "target" in factor.lower():
                                        product[key] = ai_product.get("use_cases", "Information not available")
                                    elif "community" in factor.lower():
                                        product[key] = ai_product.get("community", "Information not available")
                                    else:
                                        product[key] = "Information not available"
                                
                                products.append(product)
                    else:
                        logger.warning("No JSON array found in AI response, falling back to search results")
                        raise ValueError("No JSON array found")
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse AI response as JSON: {e}")
                    # Fallback: let AI try again with a simpler approach
                    logger.info("Retrying with simpler AI extraction approach")
                    
                    simple_prompt = f"""
                    From the following search results about "{product_category}", extract the names of actual software products, frameworks, or tools mentioned in the content.
                    
                    Search Results:
                    {search_content}
                    
                    Return ONLY a simple list of product names, one per line. Do not include article titles or generic terms.
                    Focus on actual software that developers can use.
                    """
                    
                    try:
                        simple_result = await agent.run(simple_prompt)
                        simple_text = str(simple_result.data) if hasattr(simple_result, 'data') else str(simple_result)
                        
                        # Extract product names from the simple response
                        product_names = [line.strip() for line in simple_text.split('\n') if line.strip()]
                        
                        products = []
                        for product_name in product_names[:10]:  # Limit to 10 products
                            if is_valid_software_product(product_name):
                                product = {
                                    "product_name": product_name,
                                    "url": "https://example.com",
                                    "title": f"{product_name} - {product_category}",
                                    "text": "",
                                }
                                
                                # Add factor information
                                for factor in comparison_factors:
                                    key = factor.lower().replace(" ", "_").replace("/", "_")
                                    product[key] = "Information not available"
                                
                                products.append(product)
                    except Exception as simple_e:
                        logger.error(f"Simple AI extraction also failed: {simple_e}")
                        products = []
            else:
                logger.warning("AI response too short or empty, falling back to search results")
                products = []
                
        except Exception as e:
            logger.error(f"Error using AI to extract product information: {e}")
            # Final fallback: return empty list and let the system handle it
            logger.warning("All AI extraction methods failed, returning empty product list")
            products = []
        
        if not products:
            logger.error("No products could be extracted from search results")
            return []
        
        logger.info(f"Successfully extracted {len(products)} products from Exa search results")
        logger.info(f"Product names: {[p.get('product_name', 'Unknown') for p in products[:5]]}")
        
        # Create the expected result structure
        result_data = {"products": products}
        
    except Exception as e:
        logger.error(f"Failed to search with Exa API: {e}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Exception details: {str(e)}")
        return []

    if not result_data or "products" not in result_data:
        logger.warning("Exa search returned no data")
        return []
    
    logger.info(f"Found {len(result_data['products'])} products in Exa search results")

    formatted_products = []
    for product in result_data["products"]:
        formatted_product: Dict[str, Any] = {"product_name": product.get("product_name")}
        extracted_factors: List[Dict[str, Any]] = []
        for factor, definition in zip(comparison_factors, factor_definitions):
            key = factor.lower().replace(" ", "_").replace("/", "_")
            value = product.get(key, "Not found") or "Not found"
            # Create factor dictionary
            extracted_factors.append({
                "name": factor,
                "value": value,
                "definition": definition.dict(),
            })
        formatted_product["extracted_factors"] = extracted_factors
        formatted_products.append(formatted_product)
        
    return formatted_products
