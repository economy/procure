from agentzero import Agent, State, Stride

# Define the states for the procurement workflow
class ProcurementState(State):
    IDLE = "IDLE"
    CLARIFYING = "CLARIFYING"
    SEARCHING = "SEARCHING"
    EXTRACTING = "EXTRACTING"
    FORMATTING = "FORMATTING"
    DONE = "DONE"
    ERROR = "ERROR"

# Define the data structure for the workflow
class ProcurementData:
    def __init__(self, query: str, comparison_factors: list[str]):
        self.original_query = query
        self.comparison_factors = comparison_factors
        self.clarified_query = None
        self.search_results: list[str] = []
        self.extracted_data: list[dict] = []
        self.csv_output = None
        self.error_message = None

# Define the agent and its transitions
class ProcurementAgent(Agent):
    def __init__(self):
        super().__init__(id="procurement_agent")
        self.state = Stride(
            name="procurement_state",
            state_class=ProcurementState,
            initial_state=ProcurementState.IDLE,
            transitions={
                ProcurementState.IDLE: [ProcurementState.CLARIFYING],
                ProcurementState.CLARIFYING: [ProcurementState.SEARCHING, ProcurementState.ERROR],
                ProcurementState.SEARCHING: [ProcurementState.EXTRACTING, ProcurementState.ERROR],
                ProcurementState.EXTRACTING: [ProcurementState.FORMATTING, ProcurementState.ERROR],
                ProcurementState.FORMATTING: [ProcurementState.DONE, ProcurementState.ERROR],
                ProcurementState.DONE: [],
                ProcurementState.ERROR: [],
            },
        ) 