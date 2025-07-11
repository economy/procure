"use client"

import { useEffect, useState } from "react"
import { getTaskStatus, TaskStatus } from "@/services/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ResultsViewer } from "./results-viewer";
import { ClarificationForm } from "./clarification-form";
import { submitClarification } from "@/services/api";
import { toast } from "sonner";

interface TaskListItemProps {
  taskId: string;
}

export function TaskListItem({ taskId }: TaskListItemProps) {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [isSubmittingClarification, setIsSubmittingClarification] = useState(false);

  const handleClarificationSubmit = async (clarification: string) => {
    setIsSubmittingClarification(true);
    try {
      await submitClarification(taskId, clarification);
      const result = await getTaskStatus(taskId);
      setStatus(result);
      toast.success("Clarification submitted successfully!");
    } catch (err) {
      console.error("Failed to submit clarification:", err);
      toast.error("Failed to submit clarification.");
    } finally {
      setIsSubmittingClarification(false);
    }
  };

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const result = await getTaskStatus(taskId)
        setStatus(result)
        setError(null)

        if (result.status === "completed" || result.status === "failed") {
          return
        }
      } catch (err) {
        console.error("Failed to fetch task status:", err)
        setError("Failed to fetch status")
      }
    };

    // Stop polling if clarification is being submitted
    if (isSubmittingClarification) {
      return;
    }

    fetchStatus(); // Initial fetch
    const intervalId = setInterval(fetchStatus, 5000); // Poll every 5 seconds

    return () => clearInterval(intervalId);
  }, [taskId, isSubmittingClarification]);

  const getStatusVariant = (currentStatus: string) => {
    switch (currentStatus) {
      case "running":
        return "default"
      case "completed":
        return "outline"
      case "failed":
        return "destructive"
      case "paused_for_clarification":
        return "secondary"
      default:
        return "outline"
    }
  };

  return (
    <li className="p-4 border rounded-md">
      <div className="flex justify-between items-center">
        <p className="font-mono text-sm">{taskId}</p>
        {status ? (
          <div className="flex items-center gap-4">
            {status.status === "completed" && (
              <Button onClick={() => setShowResults(!showResults)} size="sm">
                {showResults ? "Hide Results" : "View Results"}
              </Button>
            )}
            <Badge variant={getStatusVariant(status.status)}>
              {status.status}
            </Badge>
          </div>
        ) : error ? (
          <p className="text-red-500 text-sm">{error}</p>
        ) : (
          <p className="text-sm text-muted-foreground">Loading...</p>
        )}
      </div>
      {showResults && status?.data?.result && (
        <ResultsViewer url={status.data.result} />
      )}
      {status?.status === "paused_for_clarification" && (
        <ClarificationForm
          onSubmit={handleClarificationSubmit}
          isLoading={isSubmittingClarification}
        />
      )}
    </li>
  );
} 