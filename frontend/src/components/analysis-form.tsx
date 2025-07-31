"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface AnalysisFormProps {
  onSubmit: (query: string, comparisonFactors: string[]) => void;
  isLoading: boolean;
}

export function AnalysisForm({ onSubmit, isLoading }: AnalysisFormProps) {
  const [query, setQuery] = useState("")
  const [comparisonFactors, setComparisonFactors] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const factors = comparisonFactors.split(",").map(factor => factor.trim()).filter(factor => factor.length > 0)
    onSubmit(query, factors)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Analysis</CardTitle>
        <CardDescription>
          Enter a product category and the factors you want to compare.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="product-category">Product Category</Label>
            <Input
              id="product-category"
              placeholder="e.g., 'CRM software', 'Cloud Monitoring Tool'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="comparison-factors">Comparison Factors (comma-separated)</Label>
            <Textarea
              id="comparison-factors"
              placeholder="Optional: e.g., Pricing, Integrations, Support. Leave blank to use a default set of factors."
              value={comparisonFactors}
              onChange={(e) => setComparisonFactors(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Analyzing..." : "Start Analysis"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
} 