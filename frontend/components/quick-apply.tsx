"use client";

import { useState } from "react";

export function QuickApplyButton({ jobId }: { jobId: string }) {
  const [applied, setApplied] = useState(false);
  const [loading, setLoading] = useState(false);

  async function apply() {
    setLoading(true);
    try {
      const res = await fetch(
        `http://localhost:8000/api/v1/applications?user_id=00000000-0000-0000-0000-000000000001`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ job_id: jobId }),
        }
      );
      if (res.ok) {
        setApplied(true);
      }
    } catch {}
    setLoading(false);
  }

  if (applied) {
    return <span className="text-xs text-green-600 font-medium">✓ Applied</span>;
  }

  return (
    <button
      onClick={apply}
      disabled={loading}
      className="px-3 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 transition-colors"
    >
      {loading ? "..." : "Quick Apply"}
    </button>
  );
}
