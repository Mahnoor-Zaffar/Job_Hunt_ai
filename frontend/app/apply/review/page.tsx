"use client";

import { useCallback, useEffect, useState } from "react";

const USER_ID = "00000000-0000-0000-0000-000000000001";

interface ReviewItem {
  app_id: string;
  job_id: string | null;
  job_title: string;
  company: string;
  apply_url: string | null;
  cover_letter: string | null;
  matched_repo: string | null;
  before_screenshot: string | null;
  status: string;
  created_at: string;
}

export default function ApplyReviewPage() {
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`http://localhost:8000/api/v1/apply/review?user_id=${USER_ID}`);
    if (res.ok) setQueue(await res.json());
    setLoading(false);
  }, []);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  const handleSubmit = async (appId: string) => {
    setActionLoading(appId);
    const res = await fetch(`http://localhost:8000/api/v1/apply/submit?user_id=${USER_ID}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ app_id: appId }),
    });
    if (res.ok) {
      const d = await res.json();
      setResult(`Submitted ${d.company} — ${d.job_title}`);
      setQueue((q) => q.filter((i) => i.app_id !== appId));
    } else {
      setResult("Submit failed");
    }
    setActionLoading(null);
  };

  const handleSkip = async (appId: string) => {
    setActionLoading(appId);
    await fetch(`http://localhost:8000/api/v1/apply/skip?user_id=${USER_ID}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ app_id: appId }),
    });
    setQueue((q) => q.filter((i) => i.app_id !== appId));
    setActionLoading(null);
  };

  const handleSchedule = async () => {
    setLoading(true);
    const res = await fetch(`http://localhost:8000/api/v1/apply/schedule?user_id=${USER_ID}&count=5`, {
      method: "POST",
    });
    if (res.ok) {
      const d = await res.json();
      setResult(`Scheduled ${d.prepared} new applications for review`);
    }
    await fetchQueue();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Review Queue</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {queue.length} applications ready for review
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSchedule}
            disabled={loading}
            className="h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {loading ? "Loading..." : "Prepare 5 More"}
          </button>
        </div>
      </div>

      {result && (
        <div className="rounded-lg border bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 p-3 text-sm text-emerald-700 dark:text-emerald-300">
          {result}
          <button onClick={() => setResult(null)} className="ml-2 underline text-xs">Dismiss</button>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-muted-foreground py-8 text-center">Loading review queue...</p>
      ) : queue.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-lg text-muted-foreground mb-2">No applications to review</p>
          <button onClick={handleSchedule} className="text-sm text-primary hover:underline">
            Prepare applications from top remote jobs
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {queue.map((item) => (
            <div key={item.app_id} className="rounded-lg border bg-card overflow-hidden">
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium">{item.job_title}</p>
                    <p className="text-sm text-muted-foreground">
                      {item.company}
                      {item.apply_url && (
                        <a href={item.apply_url} target="_blank" rel="noreferrer"
                          className="ml-2 text-xs text-primary hover:underline">
                          View job →
                        </a>
                      )}
                    </p>
                    {item.matched_repo && (
                      <span className="inline-block mt-1 text-[10px] bg-secondary px-1.5 py-0.5 rounded">
                        Matched project: {item.matched_repo}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2 shrink-0 ml-4">
                    <button
                      onClick={() => handleSkip(item.app_id)}
                      disabled={actionLoading === item.app_id}
                      className="h-8 px-3 text-xs font-medium rounded-md border border-input hover:bg-secondary transition-colors disabled:opacity-50"
                    >
                      Skip
                    </button>
                    <button
                      onClick={() => handleSubmit(item.app_id)}
                      disabled={actionLoading === item.app_id}
                      className="h-8 px-3 text-xs font-medium rounded-md bg-emerald-600 text-white hover:bg-emerald-700 transition-colors disabled:opacity-50"
                    >
                      {actionLoading === item.app_id ? "..." : "Submit"}
                    </button>
                  </div>
                </div>

                <button
                  onClick={() => setSelected(selected === item.app_id ? null : item.app_id)}
                  className="mt-2 text-xs text-muted-foreground hover:text-foreground"
                >
                  {selected === item.app_id ? "Hide cover letter ↑" : "Preview cover letter ↓"}
                </button>

                {selected === item.app_id && item.cover_letter && (
                  <pre className="mt-3 p-3 rounded-md bg-secondary/50 text-xs leading-relaxed whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                    {item.cover_letter}
                  </pre>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
