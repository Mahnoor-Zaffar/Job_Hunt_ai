"use client";

import { useState } from "react";

export function RunScrapersButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null);

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
      setResult({
        ok: data.succeeded > 0,
        msg: `${data.succeeded}/${data.total_scrapers} succeeded · ${data.total_jobs} jobs`,
      });
    } catch {
      setResult({ ok: false, msg: "Backend unavailable" });
    }
    setLoading(false);
  }

  return (
    <div className="flex items-center gap-3">
      {result && (
        <span className={`text-xs font-medium ${result.ok ? "text-emerald-600" : "text-red-500"}`}>
          {result.msg}
        </span>
      )}
      <button
        onClick={runAll}
        disabled={loading}
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-all shadow-sm"
      >
        {loading ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
            Running...
          </>
        ) : (
          <>▶ Run All Scrapers</>
        )}
      </button>
    </div>
  );
}
