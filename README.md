# Agentic Procurement Analysis API

This project provides a powerful, agentic API built with FastAPI to automate technology procurement analysis. It transforms a simple user query (e.g., "enterprise CRM") into a structured CSV comparison of relevant solutions, streamlining the entire research process.

The system leverages the **Exa API** to perform intelligent, deep-web searches and extract structured data in a single, efficient step. This modern approach replaces traditional web scraping with a more reliable and powerful "search-and-extract" workflow.

## Key Features

-   **Intelligent Search & Extraction**: Uses the Exa Answer API to both find relevant software solutions and extract structured information based on dynamic comparison factors, all in one call.
-   **Clarification Agent**: Refines vague user queries into precise search instructions using Google's Gemini API.
-   **Human-in-the-Loop (HITL)**: If a query is too ambiguous, the process pauses and requests clarification from the user before resuming.
-   **Dynamic CSV Output**: Consolidates all extracted data into a clean, well-formatted CSV string, ready for analysis.
-   **Dockerized Environment**: Fully containerized backend and frontend services for easy, consistent setup and deployment with Docker Compose.
-   **Modern Python Stack**: Built with FastAPI, Pydantic, and `uv` for high performance and a great developer experience.

## Project Structure

-   `app/`: Main application source code.
    -   `agents/`: Contains the agents for the clarification and search-and-extract steps.
    -   `routers/`: Defines the API endpoints.
    -   `dependencies.py`: Handles API key authentication.
    -   `main.py`: The main FastAPI application entry point.
    -   `models/`: Defines Pydantic models for API requests, responses, and internal state.
    -   `utils.py`: Helper functions.
    -   `factor_templates.json`: A default list of comparison factors.
-   `frontend/`: The React-based user interface.
-   `Dockerfile`: Defines the container for the FastAPI backend.
-   `docker-compose.yml`: Orchestrates the backend and frontend services.
-   `pyproject.toml`: Project dependencies managed by `uv`.
-   `.env`: Local environment variables (you will need to create this).

## Setup and Installation with Docker

This project is designed to be run with Docker Compose, which simplifies setup and ensures a consistent environment.

1.  **Clone the repository.**

2.  **Ensure Docker Desktop is running.**

3.  **Create a `.env` file** in the root directory by copying the example:
    ```bash
    cp env.example .env
    ```

4.  **Edit the `.env` file** and add your API keys:
    ```
    API_KEY="your-secret-server-key"  # A secret key for authenticating with your API
    GOOGLE_API_KEY="your_google_api_key"
    EXA_API_KEY="your_exa_api_key"
    ```

5.  **Build and run the services:**
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker images for both the frontend and backend and start the containers.

6.  **Access the application:**
    -   **Frontend**: [http://localhost:5173](http://localhost:5173)
    -   **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Documentation

The API is designed around a simple, asynchronous task-based workflow.

### 1. Start an Analysis (`POST /analyze`)

Triggers the procurement analysis workflow.

**Headers:**
-   `x-api-key`: Your secret API key (matches `API_KEY` in your `.env`).

**Request Body:**
```json
{
  "query": "best enterprise crm software",
  "comparison_factors": ["custom reporting features", "lead scoring algorithm"]
}
```
-   `query` (str): The high-level query for a product category.
-   `comparison_factors` (List[str], optional): Specific factors to research. If omitted, a generic list is used.

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

### 2. Check Task Status (`GET /status/{task_id}`)

Retrieves the status and results of an analysis task.

**Workflow States:**
The `status` field in the response will progress through:
-   `running` (covers `CLARIFYING`, `EXTRACTING`, `FORMATTING`)
-   `paused_for_clarification`
-   `completed`
-   `failed`

When the status is `completed`, the `data` object will contain a `result` key with a data URI for the final CSV content.

### 3. Provide Clarification (`POST /tasks/{task_id}/clarify`)

If a task is paused, this endpoint allows you to provide the necessary clarification to resume the analysis.

**Request Body:**
```json
{
  "query": "customer relationship management software"
}
```
-   `query` (str): A more specific query to unblock the agent.

**Response:**
```json
{
  "message": "Task clarification received. Resuming analysis."
}
```

## Frontend Development

The frontend is a React application built with Vite. The Docker setup includes hot-reloading for development.

-   **Location**: The frontend code is in the `frontend/` directory.
-   **API Key**: The frontend is configured to use the `API_KEY` you provide in the main `.env` file. You no longer need to edit any frontend files manually.
-   **Hot-Reloading**: When running with `docker-compose up`, any changes made to the files in `frontend/src` will trigger an automatic reload in your browser.
