# Agentic Procurement Analysis API

This project is an agentic Python API designed to automate procurement analysis for technological products and services. The system leverages a multi-agent architecture to research, analyze, and compare various solutions based on user-defined criteria. The final output is a structured CSV file, providing a clear and actionable comparison for decision-making.

## Technical Stack

*   **Backend Framework**: FastAPI
*   **Data Validation**: Pydantic
*   **Agent Framework**: AgentZero
*   **Structured LLM Output**: BAML (Boundary)
*   **LLM Provider**: Google Gemini
*   **Dependency Management**: `uv`

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/procure.git
    cd procure
    ```

2.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    uvicorn main:app --reload
    ```
