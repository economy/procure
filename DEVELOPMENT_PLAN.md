# Development Plan V2: Advanced Agentic Capabilities

This document outlines the next phase of development, focusing on enhancing the intelligence, flexibility, and accuracy of the Agentic Procurement Analysis API.

## Phase 1: Advanced Search and Extraction Workflow

*   [ ] **1.1: Enhance Search Agent**:
    *   Integrate a dedicated search API (e.g., Tavily, DuckDuckGo) to improve the quality and relevance of search results.
    *   Refine the search query generation logic to be more specific based on the product category and comparison factors.

*   [ ] **1.2: Implement Extraction-to-Search Feedback Loop**:
    *   Modify the AgentZero state machine to allow the **Extraction Agent** to re-engage the **Search Agent** if it fails to find specific information.
    *   Define a clear data structure for the **Extraction Agent** to report missing information back to the **Search Agent**.

## Phase 2: Dynamic and Consistent Comparison Factors

*   [ ] **2.1: Define Factor Templates**:
    *   Research and create standardized templates of `comparison_factors` for common product categories (e.g., "CRM," "Cloud Monitoring," "API Gateway").
    *   Store these templates in a structured format (e.g., YAML or JSON file) for easy loading.

*   [ ] **2.2: Implement Dynamic Factor Loading**:
    *   Update the **Clarification Agent** to select an appropriate factor template based on the request's `product_category`.
    *   Allow user-provided `comparison_factors` to extend or override the default template.

## Phase 3: Human-in-the-Loop (HITL) Integration

*   [ ] **3.1: Design HITL Workflow**:
    *   Determine the conditions under which the **Clarification Agent** should request human input (e.g., ambiguous `product_category`, low-confidence refinement).
    *   Update the task state management to include a `paused_for_clarification` status.

*   [ ] **3.2: Implement HITL Endpoints**:
    *   The `/status/{task_id}` endpoint should now indicate when a task is awaiting human input.
    *   Create a new `POST /tasks/{task_id}/clarify` endpoint to allow a user to submit the required information.
    *   Modify the agent workflow to resume once clarification is provided.

## Phase 4: Testing and Refinement

*   [ ] **4.1: Update and Extend Tests**:
    *   Write new unit and integration tests for the feedback loop, dynamic factor loading, and HITL workflow.
    *   Ensure all new API endpoints are thoroughly tested.

*   [ ] **4.2: Documentation**:
    *   Update the `README.md` and any API documentation to reflect the new features, especially the HITL workflow and the ability to use predefined factor templates. 