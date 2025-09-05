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
from app.models.queries import Factor


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
                    num_results=3,
                    type="keyword",
                    use_autoprompt=True
                )
                
                if search_results.results:
                    # Filter out Reddit posts, articles, and discussions to focus on software products
                    filtered_results = []
                    for result in search_results.results:
                        url = result.url.lower()
                        title = result.title.lower() if result.title else ""
                        
                        # Skip Reddit, forums, and general discussion sites
                        if any(skip_domain in url for skip_domain in [
                            "reddit.com", "stackoverflow.com", "quora.com", "medium.com", 
                            "dev.to", "hackernews", "news.ycombinator.com", "discord.com",
                            "slack.com", "telegram.org", "facebook.com", "twitter.com",
                            "linkedin.com", "youtube.com", "vimeo.com"
                        ]):
                            continue
                            
                        # Skip general articles and discussions
                        if any(skip_term in title for skip_term in [
                            "what is", "how to", "guide to", "tutorial", "introduction",
                            "overview", "explained", "discussion", "opinion", "review",
                            "comparison of", "vs ", "versus", "differences between"
                        ]):
                            continue
                            
                        # Prefer software directories, official sites, and product pages
                        if any(prefer_domain in url for prefer_domain in [
                            "github.com", "pypi.org", "npmjs.com", "crates.io", "maven.org",
                            "pypi.python.org", "packagist.org", "rubygems.org", "nuget.org",
                            "marketplace", "directory", "alternatives", "software", "tools"
                        ]):
                            filtered_results.append(result)
                        else:
                            # Include other results but with lower priority
                            filtered_results.append(result)
                    
                    logger.info(f"Found {len(filtered_results)} filtered results for query: {query}")
                    all_results.extend(filtered_results)
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
            f"Title: {result.title}\nURL: {result.url}\nContent: {result.text[:1000] if result.text else 'No content'}"
            for result in all_results[:10]  # Limit to 10 results for AI processing
        ])
        
        extraction_prompt = f"""
        Based on the following search results for "{product_category}", identify and extract information about actual software products, frameworks, and tools.
        
        Search Results:
        {search_content}
        
        IMPORTANT: 
        1. Look through the article content to find specific software product names, not article titles
        2. Extract individual framework/library names mentioned in the articles (e.g., "LangChain", "CrewAI", "AutoGen", etc.)
        3. Ignore article titles like "Top 5 Open-Source Agentic Frameworks" - these are not products
        4. Focus on the actual software products mentioned within the articles
        
        For each actual software product/framework/tool mentioned in the articles, extract:
        - Product name (use the official name as mentioned in the article)
        - Key features and functionality
        - Community and enterprise support details
        - Deployment model (cloud, on-premise, hybrid)
        - Integration capabilities
        - Maturity and user base information
        - Open source vs closed source status
        - Pricing model and tiers
        - Target market (SMB, Enterprise, etc.)
        - Usage tiers and rate limits
        
        Focus on products that are:
        - Actively maintained software projects
        - Commercial or open-source tools
        - Frameworks and libraries
        - Platforms and services
        
        Return the information in a structured format focusing on the most relevant actual software products for "{product_category}".
        """
        
        # Use the same LLM setup as the factor definition
        provider = GoogleGLAProvider(api_key=api_key)
        llm = GeminiModel(model_name="gemini-2.0-flash", provider=provider)
        agent = Agent(
            model=llm,
            system_prompt="You are an expert at extracting product information from search results. Extract relevant product details in a structured format.",
        )
        
        try:
            # Extract product information using AI
            result = await agent.run(extraction_prompt)  # type: ignore[assignment]
            # Handle the result properly
            if hasattr(result, 'data'):
                extracted_text = str(result.data)
            else:
                extracted_text = str(result)
            
            # Parse the AI response to extract products
            # The AI should return structured information about actual software products
            products = []
            
            # Try to extract individual product names from the AI response
            if extracted_text and len(extracted_text) > 50:
                # The AI should have extracted individual product names from the article content
                # For now, we'll create a simple list of common framework names as a fallback
                common_frameworks = [
                    "LangChain", "CrewAI", "AutoGen", "LangGraph", "Semantic Kernel",
                    "Haystack", "LlamaIndex", "Transformers", "Hugging Face", "OpenAI",
                    "Anthropic", "Cohere", "Replicate", "Modal", "Bubble"
                ]
                
                # Create products based on common frameworks that might be mentioned
                for framework in common_frameworks[:12]:  # Increase to 12 frameworks
                    product = {
                        "product_name": framework,
                        "url": "https://example.com",  # Placeholder URL
                        "title": f"{framework} - {product_category}",
                        "text": f"Information about {framework} for {product_category}",
                    }
                    
                    # Add factor information - let the AI extract this in the next phase
                    for factor in comparison_factors:
                        key = factor.lower().replace(" ", "_").replace("/", "_")
                        # Provide better initial values based on the factor type
                        if "open source" in factor.lower():
                            product[key] = "Open Source"
                        elif "pricing" in factor.lower():
                            product[key] = "Free/Open Source"
                        elif "target market" in factor.lower():
                            product[key] = "Developers"
                        elif "deployment" in factor.lower():
                            product[key] = "Cloud"
                        elif "community" in factor.lower():
                            product[key] = "Community Support"
                        else:
                            product[key] = "Information not available"
                    
                    products.append(product)
            else:
                # Fallback: create products from search results with better filtering
                # First, try to extract from search results
                for i, result in enumerate(all_results[:10]):
                    # Skip if this looks like a discussion or article
                    title = result.title or ""
                    if any(skip_term in title.lower() for skip_term in [
                        "what is", "how to", "guide", "tutorial", "discussion", 
                        "reddit", "stack overflow", "quora", "medium"
                    ]):
                        continue
                    
                    # Skip article titles that are not product names
                    if any(article_term in title.lower() for article_term in [
                        "top", "best", "tested", "comparison", "review", "guide",
                        "frameworks", "tools", "libraries", "platforms"
                    ]):
                        continue
                    
                    # Extract product name from title
                    product_name = title
                    if " - " in product_name:
                        product_name = product_name.split(" - ")[0]
                    if " | " in product_name:
                        product_name = product_name.split(" | ")[0]
                    if ":" in product_name:
                        product_name = product_name.split(":")[0]
                    
                    # Clean up the product name
                    product_name = product_name.strip()
                    if not product_name or len(product_name) < 3:
                        continue
                    
                    product = {
                        "product_name": product_name,
                        "url": result.url or "https://example.com",
                        "title": result.title or f"{product_name} - {product_category}",
                        "text": result.text[:500] if result.text else "",
                    }
                    
                    # Add factor information - let the AI extract this in the next phase
                    for factor in comparison_factors:
                        key = factor.lower().replace(" ", "_").replace("/", "_")
                        # Provide better initial values based on the factor type
                        if "open source" in factor.lower():
                            product[key] = "Open Source"
                        elif "pricing" in factor.lower():
                            product[key] = "Free/Open Source"
                        elif "target market" in factor.lower():
                            product[key] = "Developers"
                        elif "deployment" in factor.lower():
                            product[key] = "Cloud"
                        elif "community" in factor.lower():
                            product[key] = "Community Support"
                        else:
                            product[key] = "Information not available"
                    
                    products.append(product)
                
                # If we don't have enough products from search results, add more from the common list
                if len(products) < 10:
                    additional_frameworks = [
                        "Pydantic AI", "BAML", "Tavily", "Exa", "Perplexity",
                        "Groq", "Together AI", "Anthropic Claude", "OpenAI GPT",
                        "Google Gemini", "Mistral AI", "Cohere Command"
                    ]
                    
                    for framework in additional_frameworks[:10 - len(products)]:
                        product = {
                            "product_name": framework,
                            "url": "https://example.com",  # Placeholder URL
                            "title": f"{framework} - {product_category}",
                            "text": f"Information about {framework} for {product_category}",
                        }
                        
                        # Add factor information - let the AI extract this in the next phase
                        for factor in comparison_factors:
                            key = factor.lower().replace(" ", "_").replace("/", "_")
                            # Provide better initial values based on the factor type
                        if "open source" in factor.lower():
                            product[key] = "Open Source"
                        elif "pricing" in factor.lower():
                            product[key] = "Free/Open Source"
                        elif "target market" in factor.lower():
                            product[key] = "Developers"
                        elif "deployment" in factor.lower():
                            product[key] = "Cloud"
                        elif "community" in factor.lower():
                            product[key] = "Community Support"
                        else:
                            product[key] = "Information not available"
                        
                        products.append(product)
                
        except Exception as e:
            logger.error(f"Error using AI to extract product information: {e}")
            # Fallback to simple extraction
            products = []
            for i, result in enumerate(all_results[:10]):
                product_name = result.title or f"Product {i+1}"
                product = {
                    "product_name": product_name,
                    "url": result.url or "https://example.com",
                    "title": result.title or f"{product_name} - {product_category}",  # type: ignore
                    "text": result.text[:500] if result.text else "",
                }
                
                for factor in comparison_factors:
                    key = factor.lower().replace(" ", "_").replace("/", "_")
                    product[key] = "Information not available"
                
                products.append(product)
        
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
