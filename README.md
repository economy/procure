# Agentic Procurement Analysis API

This project provides a powerful, multi-agent API built with FastAPI to automate technology procurement analysis. It transforms a simple user query (e.g., "enterprise CRM") into a structured CSV comparison of relevant solutions, streamlining the entire research process.

The system uses a sophisticated, two-phase research process to ensure the highest quality results:
1.  **Discovery**: A broad, initial search using the **Exa API** discovers the key players in a given software category.
2.  **Enrichment**: For each discovered product, a series of targeted, dynamic Exa searches are performed to find authoritative information (like official pricing pages), which is then used to cross-reference, correct, and complete the initial data.

This self-correcting pipeline ensures the final output is not only comprehensive but also consistent, accurate, and up-to-date.

## Key Features

-   **Multi-Agent Workflow**: A sophisticated pipeline of agents for clarification, discovery, processing, targeting, enrichment, and formatting.
-   **Self-Correcting Enrichment**: Dynamically identifies weaknesses in the initial data and performs targeted searches to find authoritative sources and fill gaps.
-   **Intelligent Extraction**: Uses the Exa Research API with dynamically generated schemas to extract structured information.
-   **Human-in-the-Loop (HITL)**: If a query is too ambiguous, the process pauses and requests clarification from the user.
-   **Dockerized Environment**: Fully containerized backend and frontend services for easy, consistent setup and deployment.
-   **Modern Python Stack**: Built with FastAPI, Pydantic, and `uv` for high performance.

## Project Structure

-   `app/`: Main application source code.
    -   `agents/`: Contains all agents for the multi-phase workflow.
    -   `routers/`: Defines the API endpoints.
    -   `dependencies.py`: Handles API key authentication.
    -   `main.py`: The main FastAPI application entry point.
    -   `models/`: Defines Pydantic models for API requests, responses, and internal state.
-   `frontend/`: The React-based user interface.
-   `Dockerfile`: Defines the container for the FastAPI backend.
-   `docker-compose.yml`: Orchestrates the backend and frontend services.
-   `pyproject.toml`: Project dependencies managed by `uv`.
-   `.env`: Local environment variables (you will need to create this).

## Setup and Installation with Docker

1.  **Ensure Docker Desktop is running.**

2.  **Create a `.env` file** by copying the example:
    ```bash
    cp env.example .env
    ```

3.  **Edit the `.env` file** and add your API keys:
    ```
    API_KEY="your-secret-server-key"
    GOOGLE_API_KEY="your_google_api_key"
    EXA_API_KEY="your_exa_api_key"
    ```

4.  **Build and run the services:**
    ```bash
    docker-compose up --build
    ```

5.  **Access the application:**
    -   **Frontend**: [http://localhost:5173](http://localhost:5173)
    -   **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Documentation

The API is designed around a simple, asynchronous task-based workflow.

### 1. Start an Analysis (`POST /analyze`)
Triggers the procurement analysis workflow.

**Request Body:**
```json
{
  "query": "best enterprise crm software",
  "comparison_factors": ["custom reporting features", "lead scoring algorithm"]
}
```
-   `query` (str): The high-level query for a product category.
-   `comparison_factors` (List[str], optional): Specific factors to research. If omitted, a generic list is used.

### 2. Check Task Status (`GET /status/{task_id}`)
Retrieves the status and results of an analysis task.

**Workflow States:**
The `status` field in the response will progress through: `CLARIFYING`, `EXTRACTING`, `PROCESSING`, `ENRICHING`, `FORMATTING`, `COMPLETED`, `AWAITING_CLARIFICATION`, `ERROR`.

When `completed`, the `data` object will contain a `result` key with a data URI for the final CSV content.

### 3. Provide Clarification (`POST /tasks/{task_id}/clarify`)
If a task is paused, this endpoint allows you to provide the necessary clarification to resume the analysis.

**Request Body:**
```json
{
  "query": "customer relationship management software"
}
```
