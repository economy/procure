# Product Requirements Document (PRD): Agentic Procurement Analysis API

## 1. Introduction

This document outlines the product requirements for an agentic Python API designed to automate procurement analysis for technological products and services. The system will leverage a multi-agent architecture to research, analyze, and compare various solutions based on user-defined criteria. The final output will be a structured CSV file, providing a clear and actionable comparison for decision-making.

## 2. Problem Statement

Procurement research is a time-consuming, manual process. It involves sifting through marketing materials, technical documentation, and pricing pages to extract comparable data points. This process is often repetitive and prone to inconsistency. This project aims to automate this research, providing users with a fast, reliable, and structured way to evaluate technology solutions.

## 3. Goals and Objectives

*   **Primary Goal**: To provide an API that accepts a research request for a technology product/service and returns a structured comparison of available options in a CSV format.
*   **Key Objectives**:
    *   Develop a robust FastAPI endpoint to manage and initiate procurement analysis tasks.
    *   Implement a multi-agent system using AgentZero for a stateful, managed research workflow.
    *   Utilize Google Gemini for natural language understanding and generation tasks.
    *   Use BAML to enforce structured data extraction from LLM responses, ensuring consistency and reliability.
    *   Deliver a well-structured, easy-to-parse CSV file as the final output.

## 4. Target Audience

*   Technology leaders (CTOs, VPs of Engineering)
*   Procurement managers
*   Software developers and architects looking for tools and services.

## 5. Features and Functionality

### 5.1. API Endpoint (`/analyze`)

*   **Method**: `POST`
*   **Request Body**: A Pydantic model defining the research query.
    *   `product_category` (string): The type of product to research (e.g., "CRM software", "Cloud Monitoring Tool").
    *   `comparison_factors` (list[string]): A list of specific factors to research for each solution.
*   **Response**: A task ID to track the analysis job. A status polling endpoint (`/status/{task_id}`) will be available to check progress and retrieve the final CSV file URL upon completion.

### 5.2. Agentic Workflow (AgentZero)

The core logic will be orchestrated as a stateful, multi-agent workflow:

1.  **Clarification Agent**:
    *   **Trigger**: A new analysis request is received.
    *   **Task**: Refines the user's query into a precise and actionable research plan. It will break down the `product_category` into specific keywords and identify reliable sources for information.
    *   **Output**: A structured research plan for the Search Agent.

2.  **Search Agent**:
    *   **Trigger**: A research plan is created.
    *   **Task**: Executes targeted web searches to compile a list of potential solutions.
    *   **Output**: A list of URLs for candidate product/service websites.

3.  **Extraction Agent**:
    *   **Trigger**: A list of solution URLs is available.
    *   **Task**: For each solution, this agent (or a pool of parallel agents) will navigate the corresponding website to find information related to the `comparison_factors`. It will leverage BAML to call the Google Gemini API and extract the information in a structured format.
    *   **Default Comparison Factors**:
        *   Solution Maturity / Community Base (e.g., years in market, key customers)
        *   Open / Closed Source
        *   Deployment Model (Hosted Cloud, Self-hosted)
        *   Pricing Information (including tiers and usage limits)
        *   Targeted Markets (e.g., SMB, Enterprise)
    *   **Output**: A list of structured JSON objects, one for each solution, containing the extracted data.

4.  **Formatting Agent**:
    *   **Trigger**: Structured data for all solutions has been extracted.
    *   **Task**: Aggregates the JSON objects into a clean, tabular format and generates a CSV file.
    *   **Output**: The final CSV file, stored and made available for download.

## 6. Technical Stack

*   **Backend Framework**: FastAPI
*   **Data Validation**: Pydantic
*   **Agent Framework**: AgentZero
*   **Structured LLM Output**: BAML (Boundary)
*   **LLM Provider**: Google Gemini
*   **Dependency Management**: `uv`

## 7. Assumptions and Dependencies

*   Access to the Google Gemini API is configured and available.
*   AgentZero and BAML libraries are compatible with the project's Python version.
*   The agents require unrestricted access to the public internet.
*   The variability of vendor website structures poses a risk to data extraction consistency. BAML is expected to mitigate this, but it remains a key challenge.

## 8. Success Metrics

*   **Data Accuracy**: Percentage of correctly extracted data points from vendor websites.
*   **Task Completion Rate**: Percentage of analysis requests that complete successfully.
*   **Turnaround Time**: Average time from request submission to CSV file generation.

## 9. Out of Scope (for V1)

*   A dedicated user interface (UI).
*   Real-time, interactive chat with agents.
*   Output formats other than CSV.
*   User authentication and multi-tenancy (a simple `x-api-key` will be used for authorization).

## 10. Future Work

*   Develop a React-based frontend for interactive use.
*   Add support for additional output formats like JSON and Google Sheets.
*   Implement a full-fledged user authentication system.
*   Allow users to save and compare reports over time. 