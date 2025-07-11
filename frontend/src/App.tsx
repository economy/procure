import { useState } from "react";
import { AnalysisForm } from "@/components/analysis-form";
import { startAnalysis } from "@/services/api";
import { TaskListItem } from "@/components/task-list-item";
import { Toaster, toast } from "sonner";

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [tasks, setTasks] = useState<string[]>([]);

  const handleAnalysisSubmit = async (query: string, comparisonFactors: string[]) => {
    setIsLoading(true);
    try {
      const response = await startAnalysis({
        query: query,
        comparison_factors: comparisonFactors,
      });
      setTasks(prevTasks => [...prevTasks, response.task_id]);
      toast.success("Analysis started!", {
        description: `Task ID: ${response.task_id}`,
      });
    } catch (error) {
      console.error("Analysis submission failed:", error);
      toast.error("Analysis submission failed", {
        description: "Please check the console for more details.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <Toaster />
      <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur-sm">
        <div className="container flex h-14 max-w-screen-2xl items-center">
          <h1 className="font-bold">Agentic Procurement</h1>
        </div>
      </header>
      <main className="container mx-auto py-8">
        <div className="grid gap-8">
          <AnalysisForm onSubmit={handleAnalysisSubmit} isLoading={isLoading} />
          <div>
            <h2 className="text-xl font-semibold mb-4">Tracked Tasks</h2>
            {tasks.length > 0 ? (
              <ul className="space-y-2">
                {tasks.map(taskId => (
                  <TaskListItem key={taskId} taskId={taskId} />
                ))}
              </ul>
            ) : (
              <p>No tasks submitted yet.</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
