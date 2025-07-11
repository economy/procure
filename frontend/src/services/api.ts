import ky from "ky";

const apiClient = ky.create({
  prefixUrl: "http://127.0.0.1:8000", // This should be in an env variable
});

export interface AnalyzeRequest {
  query: string;
  comparison_factors: string[];
}

export interface AnalyzeResponse {
  task_id: string;
}

export const startAnalysis = async (data: AnalyzeRequest): Promise<AnalyzeResponse> => {
  const response = await apiClient.post("analyze", {
    json: data,
    headers: {
      "x-api-key": "test-key",
    },
  });
  return response.json();
};

export interface TaskStatus {
  task_id: string;
  status: string;
  data: {
    result?: string;
    [key: string]: any;
  } | null;
}

export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await apiClient.get(`status/${taskId}`, {
    headers: {
      "x-api-key": "test-key",
    },
  });
  return response.json();
};

export const submitClarification = async (taskId: string, clarification: string): Promise<void> => {
  await apiClient.post(`tasks/${taskId}/clarify`, { json: { clarification } });
}; 