"use client";

import { useState } from "react";

export function RunScrapersButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function runAll() {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/scrapers/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      setResult(`${data.succeeded} succeeded, ${data.total_jobs} jobs`);
    } catch {
      setResult("Failed — is the backend running?");
    }
    setLoading(false);
  }

  return (
    <div className="flex items-center gap-3">
      {result && <span className="text-xs text-muted-foreground">{result}</span>}
      <button
        onClick={runAll}
        disabled={loading}
        className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {loading ? "Running..." : "▶ Run All Scrapers"}
      </button>
    </div>
  );
}
