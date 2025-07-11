"use client"

import { useEffect, useState } from "react"
import Papa from "papaparse"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

interface ResultsViewerProps {
  url: string;
}

export function ResultsViewer({ url }: ResultsViewerProps) {
  const [data, setData] = useState<string[][]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`Failed to fetch CSV: ${response.statusText}`)
        }
        const text = await response.text()
        Papa.parse(text, {
          complete: (result) => {
            setData(result.data as string[][])
          },
          error: (err: Error) => {
            throw new Error(`CSV parsing error: ${err.message}`)
          },
        })
      } catch (err) {
        if (err instanceof Error) {
            setError(err.message)
        } else {
            setError("An unknown error occurred")
        }
      }
    }

    fetchData()
  }, [url])

  if (error) {
    return <p className="text-red-500">{error}</p>
  }

  if (data.length === 0) {
    return <p>Loading results...</p>
  }

  const headers = data[0]
  const rows = data.slice(1)

  return (
    <div className="w-full overflow-auto border-2 border-foreground rounded-lg mt-4 shadow-lg">
      <Table>
        <TableHeader>
          <TableRow>
            {headers.map((header, index) => (
              <TableHead
                key={index}
                className="p-2 font-bold text-foreground bg-muted text-sm whitespace-normal break-words"
              >
                {header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, rowIndex) => (
            <TableRow key={rowIndex} className="border-t border-foreground">
              {row.map((cell, cellIndex) => (
                <TableCell
                  key={cellIndex}
                  className="p-2 text-xs whitespace-normal break-words"
                >
                  {cell}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
} 