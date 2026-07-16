"use client";

import { useEffect, useState } from "react";

interface ScraperStatus {
  source: string;
  display_name: string;
  last_run: string | null;
  last_status: string;
  last_jobs: number;
  last_duration: number;
  last_error: string | null;
}

export function ScraperStatusPanel() {
  const [status, setStatus] = useState<ScraperStatus[] | null>(null);
  const [loading, setLoading] = useState(false);

  async function fetchStatus() {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/scrapers/status");
      const data = await res.json();
      setStatus(data.scrapers);
    } catch {}
    setLoading(false);
  }

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  if (!status) return null;

  return (
    <div className="space-y-2">
      {status.map((s) => (
        <div key={s.source} className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                s.last_status === "success"
                  ? "bg-green-500"
                  : s.last_status === "failed"
                  ? "bg-red-500"
                  : "bg-gray-300"
              }`}
            />
            <span className="capitalize text-muted-foreground">{s.display_name}</span>
          </div>
          <div className="flex gap-3 text-muted-foreground">
            {s.last_jobs > 0 && <span>{s.last_jobs} jobs</span>}
            {s.last_duration > 0 && <span>{s.last_duration.toFixed(1)}s</span>}
            {s.last_error && (
              <span className="text-red-500 truncate max-w-[120px]" title={s.last_error}>
                ⚠ {s.last_error.slice(0, 30)}
              </span>
            )}
          </div>
        </div>
      ))}
      <button
        onClick={fetchStatus}
        className="text-xs text-primary hover:underline mt-1"
      >
        {loading ? "Refreshing..." : "↻ Refresh"}
      </button>
    </div>
  );
}
