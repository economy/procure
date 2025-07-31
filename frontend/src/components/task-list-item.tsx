"use client";

import { useEffect, useState } from "react";
import { getTaskStatus, TaskStatus, submitClarification } from "@/services/api";
import { Button } from "@/components/ui/button";
import { ResultsViewer } from "./results-viewer";
import { ClarificationForm } from "./clarification-form";
import StatusStepper from "./status-stepper";
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
        const result = await getTaskStatus(taskId);
        setStatus(result);
        setError(null);

        if (result.status === "completed" || result.status === "failed") {
          return;
        }
      } catch (err) {
        console.error("Failed to fetch task status:", err);
        setError("Failed to fetch status");
      }
    };

    if (isSubmittingClarification) {
      return;
    }

    fetchStatus();
    const intervalId = setInterval(fetchStatus, 3000);

    return () => clearInterval(intervalId);
  }, [taskId, isSubmittingClarification]);

  return (
    <li className="p-4 border rounded-lg space-y-4">
      <div className="flex justify-between items-start">
        <div className="flex flex-col">
          {status?.data?.initial_query ? (
            <>
              <p className="font-semibold text-lg">
                "{status.data.initial_query}"
              </p>
              {status.data.clarified_query &&
                status.data.clarified_query !== status.data.initial_query && (
                  <p className="text-sm text-gray-500 mt-1 italic">
                    Refined Query: "{status.data.clarified_query}"
                  </p>
                )}
              <p className="font-mono text-xs text-muted-foreground mt-2">
                {taskId}
              </p>
            </>
          ) : (
            <p className="font-mono text-sm">{taskId}</p>
          )}
        </div>

        {status?.status === "completed" && (
          <div className="flex items-center gap-2">
            <Button
              onClick={() => {
                const link = document.createElement("a");
                link.href = status.data?.result || "";
                link.setAttribute(
                  "download",
                  `procurement-analysis-${taskId}.csv`
                );
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }}
              size="sm"
              variant="outline"
            >
              Download CSV
            </Button>
            <Button onClick={() => setShowResults(!showResults)} size="sm">
              {showResults ? "Hide Results" : "View Results"}
            </Button>
          </div>
        )}
      </div>

      <div className="pt-2">
        {status ? (
          <StatusStepper currentState={status.data?.current_state ?? status.status.toUpperCase()} />
        ) : error ? (
          <p className="text-red-500 text-sm">{error}</p>
        ) : (
          <p className="text-sm text-muted-foreground">Loading status...</p>
        )}
      </div>

      {showResults && status?.data?.result && (
        <ResultsViewer url={status.data.result} />
      )}
      {status?.status === "paused_for_clarification" && (
        <ClarificationForm
          onSubmit={handleClarificationSubmit}
          isLoading={isSubmittingClarification}
          question={status.data?.clarified_query}
        />
      )}
    </li>
  );
}
