# Development Plan: Agentic Procurement Analysis API

This document outlines the development plan for creating the Agentic Procurement Analysis API. We will follow this plan to ensure a structured and incremental development process.

## Phase 1: Project Scaffolding and Core Setup

*   [ ] **1.1: Initialize Project Structure**:
    *   Create the `app` directory.
    *   Move `main.py` into `app`.

*   [ ] **1.2: Install Core Dependencies**:
    *   Install `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`.

*   [ ] **1.3: Basic FastAPI Application**:
    *   Set up a basic "Hello World" FastAPI app in `main.py`.
    *   Implement basic configuration management to load environment variables.

*   [ ] **1.4: API Key Authentication**:
    *   Implement a dependency to secure endpoints with an `x-api-key` header.

## Phase 2: BAML and Agent Framework Integration

*   [ ] **2.1: Install Agent-related Dependencies**:
    *   Install `boundary-baml`, `google-generativeai`, and `agentzero`.

*   [ ] **2.2: Set up BAML**:
    *   Initialize BAML in the project (`baml init`).
    *   Define initial BAML functions for the **Extraction Agent**, including schemas for `Tool`, `Feature`, and `Pricing`.

*   [ ] **2.3: Set up AgentZero**:
    *   Create a directory for agents (`app/agents`).
    *   Define the basic state machine structure for the procurement workflow.

## Phase 3: API Endpoint and Workflow Implementation

*   [ ] **3.1: Implement API Models**:
    *   Create Pydantic models in `app/models` for the `/analyze` request and response bodies.

*   [ ] **3.2: Create API Endpoints**:
    *   Implement the `POST /analyze` endpoint to accept a research request and kick off the agent workflow as a background task.
    *   Implement the `GET /status/{task_id}` endpoint to check the status of a research task.

*   [ ] **3.3: Task Management**:
    *   Set up a simple in-memory dictionary to store task statuses and results.

## Phase 4: Agent Development

*   [ ] **4.1: Clarification Agent**:
    *   Develop the logic to refine the user's query.

*   [ ] **4.2: Search Agent**:
    *   Implement web search functionality to find a list of candidate solutions.

*   [ ] **4.3: Extraction Agent**:
    *   Integrate BAML calls to the Google Gemini API to extract structured information from URLs.

*   [ ] **4.4: Formatting Agent**:
    *   Develop the logic to convert the list of JSON objects into a CSV file.

## Phase 5: Testing and Deployment

*   [ ] **5.1: Unit and Integration Testing**:
    *   Write tests for individual agents and the full API workflow.

*   [ ] **5.2: Dockerization**:
    *   Create a `Dockerfile` for the application.
    *   Create a `docker-compose.yml` for easy local development.

*   [ ] **5.3: Documentation**:
    *   Update the `README.md` with detailed API usage instructions and examples. 