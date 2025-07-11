# Procurement Agent

This project implements a multi-agent system using FastAPI to automate procurement analysis. It transforms a user's query about a product category (e.g., "enterprise crm") into a detailed, CSV-formatted comparison of available solutions.

The system is designed to be robust and flexible, incorporating a high-volume, parallelized research workflow and a **Human-in-the-Loop (HITL)** process for handling ambiguity.

## Key Features

-   **Clarification Agent**: Refines vague queries and automatically selects a relevant set of comparison factors from predefined templates.
-   **High-Volume Search**: Gathers a large set of potential product/service URLs using the Tavily Search API.
-   **Parallelized Extraction**: Processes up to 25 URLs concurrently, scraping each page and using a Google Gemini model to extract structured information.
-   **Resilient Workflow**: Includes a search/extraction feedback loop to retry failed attempts and ensure a comprehensive dataset.
-   **Human-in-the-Loop (HITL)**: If a query is too ambiguous, the process will pause, ask for user clarification, and resume upon receiving input.
-   **CSV Output**: Consolidates all extracted data into a final CSV-formatted string.

## Project Structure

-   `app/`: Main application source code.
    -   `agents/`: Contains the individual agents for each step of the workflow.
    -   `routers/`: Defines the API endpoints.
    -   `dependencies.py`: Handles API key authentication.
    -   `main.py`: The main FastAPI application entry point.
    -   `models/`: Defines the Pydantic models for API requests, responses, and internal state.
    -   `utils.py`: Helper functions, including the factor template loader.
    -   `factor_templates.json`: Predefined lists of comparison factors for different product categories.
-   `pyproject.toml`: Project dependencies managed by `uv`.
-   `.env`: Local environment variables (you will need to create this).
-   `.gitignore`: Specifies untracked files to ignore.

## Setup and Installation

1.  **Clone the repository.**

2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv # Creates a .venv directory
    source .venv/bin/activate
    uv pip install -r requirements.txt
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

The API is designed around a simple, asynchronous task-based workflow.

### 1. Start an Analysis (`POST /analyze`)

This is the main endpoint to trigger the procurement analysis.

**Request Body:**

```json
{
  "query": "best enterprise crm software",
  "comparison_factors": ["custom reporting features", "lead scoring algorithm"]
}
```

-   `query` (str): The initial, high-level query for a product or service.
-   `comparison_factors` (List[str], optional): An optional list of specific factors to research. If omitted, the system will automatically select a template of factors based on the query.

**Headers:**

-   `x-api-key` (str): Your secret API key for authenticating with the server (matches `API_KEY` in your `.env`).

**Response:**

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

-   `task_id` (str): A unique ID for the analysis task.

### 2. Check Task Status (`GET /status/{task_id}`)

Retrieves the status and results of a previously started analysis task.

**Path Parameters:**

-   `task_id` (str): The ID of the task returned from the `/analyze` endpoint.

**Workflow States:**

The `status` field in the response will progress through the following states:
-   `CLARIFYING`
-   `SEARCHING`
-   `EXTRACTING`
-   `FORMATTING`
-   `AWAITING_CLARIFICATION` (Paused for user input)
-   `DONE`
-   `ERROR`

When the status is `DONE`, the `data.formatted_output` field will contain the final CSV data as a string.

### 3. Provide Clarification (`POST /tasks/{task_id}/clarify`)

If a task's status is `AWAITING_CLARIFICATION`, the `data.clarified_query` field will contain a question from the agent. You can provide an answer using this endpoint to resume the task.

**Request Body:**

```json
{
  "product_category_key": "crm"
}
```

-   `product_category_key` (str): The key corresponding to one of the predefined templates (`crm`, `cloud_monitoring`, `api_gateway`).

**Response:**

```json
{
  "message": "Task clarification received. Resuming analysis."
}
```

The task will then resume from the clarification step.

## Frontend

This project includes a React-based frontend for interacting with the API.

### Setup and Installation

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Update the API Key:**
    Before running, open `frontend/src/services/api.ts` and replace `"your-secret-api-key"` with the `API_KEY` value from your main `.env` file.

4.  **Run the development server:**
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173`.
