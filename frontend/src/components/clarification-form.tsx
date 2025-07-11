"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface ClarificationFormProps {
  onSubmit: (clarification: string) => void;
  isLoading: boolean;
}

export function ClarificationForm({ onSubmit, isLoading }: ClarificationFormProps) {
  const [clarification, setClarification] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(clarification)
    setClarification("")
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 mt-2">
      <Input
        placeholder="Provide clarification..."
        value={clarification}
        onChange={(e) => setClarification(e.target.value)}
        disabled={isLoading}
      />
      <Button type="submit" disabled={isLoading} size="sm">
        {isLoading ? "Submitting..." : "Submit"}
      </Button>
    </form>
  )
} 