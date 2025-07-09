# Procurement Agent

This project implements a multi-agent system using FastAPI to automate the initial stages of a procurement workflow. Given a vague user query (e.g., "best enterprise crm"), the system will:

1.  **Clarify**: Use a language model to enrich the query and identify key comparison factors.
2.  **Search**: Use the Tavily Search API to find relevant product/service URLs.
3.  **Extract**: Scrape each URL and use a language model to extract structured information based on the comparison factors.
4.  **Format**: Consolidate all the extracted data into a final CSV-formatted string.

## Project Structure

-   `app/`: Main application source code.
    -   `agents/`: Contains the individual agents for each step of the workflow (clarification, search, extraction, formatting).
    -   `routers/`: Defines the API endpoints.
    -   `dependencies.py`: Handles API key authentication.
    -   `main.py`: The main FastAPI application entry point.
    -   `models.py`: Defines the Pydantic models for API requests and responses.
-   `pyproject.toml`: Project dependencies.
-   `.env`: Environment variables (you will need to create this).

## Setup and Installation

1.  **Clone the repository.**

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    uv pip install -r requirements.txt 
    # Note: A requirements.txt is not yet generated, but this is the standard command.
    # For now, install directly from pyproject.toml
    uv pip install -e .
    ```

3.  **Create a `.env` file** in the root directory and add your API keys:
    ```
    API_KEY="test-key" # Or any secret key for server authentication
    GOOGLE_API_KEY="your_google_api_key"
    TAVILY_API_KEY="your_tavily_api_key"
    ```

4.  **Run the application:**
    ```bash
    uv run uvicorn app.main:app --reload
    ```
    The server will be available at `http://127.0.0.1:8000`.

## API Documentation

### POST /analyze

This is the main endpoint to trigger the procurement analysis workflow.

**Request Body:**

```json
{
  "query": "best enterprise crm software",
  "comparison_factors": ["pricing", "integration capabilities", "customer support"]
}
```

-   `query` (str): The initial, high-level query for a product or service.
-   `comparison_factors` (List[str]): A list of factors to compare. These will be expanded upon by the Clarification Agent.

**Headers:**

-   `x-api-key` (str): Your secret API key for authenticating with the server (matches `API_KEY` in your `.env`).

**Response:**

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

-   `task_id` (str): A unique ID for the analysis task you just started.

### GET /status/{task_id}

Retrieves the status and results of a previously started analysis task.

**Path Parameters:**

-   `task_id` (str): The ID of the task returned from the `/analyze` endpoint.

**Response:**

A JSON object representing the current state of the task. The `status` field will progress through `CLARIFYING`, `SEARCHING`, `EXTRACTING`, `FORMATTING`, and finally `DONE`.

When the status is `DONE`, the `data.formatted_output` field will contain the final CSV data as a string.

```json
{
    "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "status": "DONE",
    "data": {
        "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "current_state": 6,
        "initial_query": "best enterprise crm software",
        "clarified_query": "...",
        "comparison_factors": [...],
        "search_results": [...],
        "extracted_data": [...],
        "formatted_output": "product_name,pricing,integration capabilities,customer support\\r\\nProduct A,10,Yes,Good\\r\\nProduct B,20,No,Average\\r\\n",
        "error_message": null
    }
}
```
