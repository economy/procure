"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ClarificationFormProps {
  onSubmit: (clarification: string) => void;
  isLoading: boolean;
  question?: string;
}

export function ClarificationForm({
  onSubmit,
  isLoading,
  question,
}: ClarificationFormProps) {
  const [clarification, setClarification] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(clarification);
    setClarification("");
  };

  return (
    <div className="mt-4 p-4 border rounded-lg bg-yellow-50/50">
      <form onSubmit={handleSubmit} className="space-y-3">
        <Label htmlFor="clarification-input" className="font-semibold">
          The agent needs more information:
        </Label>
        {question && (
          <p className="text-sm text-muted-foreground italic">
            "{question}"
          </p>
        )}
        <div className="flex items-center gap-2">
          <Input
            id="clarification-input"
            placeholder="Provide a more specific query..."
            value={clarification}
            onChange={(e) => setClarification(e.target.value)}
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !clarification} size="sm">
            {isLoading ? "Submitting..." : "Submit"}
          </Button>
        </div>
      </form>
    </div>
  );
}
