"use client";

import { useEffect, useState } from "react";
import { AutoApplyButton } from "@/components/auto-apply";

const PER_PAGE = 30;

const SOURCE_LABELS: Record<string, string> = {
  remoteok: "Remote OK",
  weworkremotely: "We Work Remotely",
  remotive: "Remotive",
  wellfound: "Wellfound",
  remote_co: "Remote.co",
  built_in: "Built In",
  hn_hiring: "HN Hiring",
};

const SOURCE_COLORS: Record<string, string> = {
  remoteok: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  weworkremotely: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  remotive: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  wellfound: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  remote_co: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300",
  built_in: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
  hn_hiring: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

const QUICK_FILTERS = ["Backend", "Frontend", "Full Stack", "Python", "React", "DevOps", "AI/ML"];

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  source: string;
  salary_min: number | null;
  skills: string[] | null;
  apply_url: string | null;
}

interface JobsResponse {
  items: Job[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export default function RemoteJobsPage() {
  const [data, setData] = useState<JobsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [sourceFilter, setSourceFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  function load() {
    setLoading(true);
    const params = new URLSearchParams({
      is_remote: "true",
      status: "active",
      per_page: String(PER_PAGE),
      page: String(page),
    });
    if (query) params.set("title", query);
    if (sourceFilter !== "all") params.set("source", sourceFilter);

    fetch(`http://localhost:8000/api/v1/jobs?${params.toString()}`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setData(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [page, sourceFilter]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    load();
  }

  const sources = data?.items
    ? [...new Set(data.items.map((j) => j.source))].sort()
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Remote Jobs</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {data ? `${data.total} remote jobs` : "Loading..."}
          </p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter by title..."
          className="flex-1 h-9 px-3 text-sm rounded-md border bg-transparent focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <button type="submit" className="h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
          Search
        </button>
        {query && (
          <button onClick={() => { setQuery(""); setPage(1); }} className="h-9 px-3 text-sm rounded-md border text-muted-foreground hover:bg-secondary transition-colors">
            Clear
          </button>
        )}
      </form>

      <div className="flex gap-1.5 flex-wrap">
        <button
          onClick={() => { setSourceFilter("all"); setPage(1); }}
          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${sourceFilter === "all" ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}
        >
          All Sources
        </button>
        {sources.map((s) => (
          <button
            key={s}
            onClick={() => { setSourceFilter(s); setPage(1); }}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors ${sourceFilter === s ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}
          >
            {SOURCE_LABELS[s] || s}
          </button>
        ))}
      </div>

      <div className="flex gap-1.5 flex-wrap">
        {QUICK_FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => { setQuery(f); setPage(1); }}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors ${query === f ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}
          >
            {f}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-16">
          <p className="text-sm text-muted-foreground">Loading remote jobs...</p>
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-lg text-muted-foreground mb-2">No remote jobs found</p>
          <p className="text-sm text-muted-foreground/60">
            {query ? `Try a different search term.` : "Run scrapers from the Dashboard to discover remote jobs."}
          </p>
        </div>
      ) : (
        <>
          <div className="rounded-lg border">
            {data.items.map((job) => (
              <div key={job.id} className="flex items-center gap-4 px-5 py-3 border-b last:border-0 hover:bg-secondary/30 transition-colors">
                <div className="flex-1 min-w-0">
                  <a href={`/jobs/${job.id}`} className="text-sm font-medium hover:text-primary transition-colors truncate block">
                    {job.title}
                  </a>
                  <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                    <span>{job.company}</span>
                    <span>·</span>
                    <span>{job.location}</span>
                  </div>
                  {job.skills && job.skills.length > 0 && (
                    <div className="flex gap-1 mt-1.5 flex-wrap">
                      {job.skills.slice(0, 4).map((s) => (
                        <span key={s} className="text-[10px] bg-secondary px-1.5 py-0.5 rounded">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${SOURCE_COLORS[job.source] || "bg-secondary text-muted-foreground"}`}>
                    {SOURCE_LABELS[job.source] || job.source}
                  </span>
                  {job.salary_min ? <span className="text-xs font-medium whitespace-nowrap">${job.salary_min}</span> : null}
                  <AutoApplyButton jobId={job.id} />
                </div>
              </div>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="flex justify-center gap-1">
              {page > 1 && (
                <button onClick={() => setPage(page - 1)} className="h-8 px-3 text-xs flex items-center rounded-md border hover:bg-secondary transition-colors">
                  ← Prev
                </button>
              )}
              {Array.from({ length: data.pages }, (_, i) => i + 1)
                .filter((p) => p === 1 || p === data.pages || Math.abs(p - page) <= 2)
                .map((p, i, arr) => (
                  <span key={p}>
                    {i > 0 && arr[i - 1] !== p - 1 && <span className="px-1 text-muted-foreground text-xs">…</span>}
                    <button
                      onClick={() => setPage(p)}
                      className={`h-8 w-8 text-xs flex items-center justify-center rounded-md transition-colors ${p === page ? "bg-primary text-primary-foreground" : "border hover:bg-secondary"}`}
                    >
                      {p}
                    </button>
                  </span>
                ))}
              {page < data.pages && (
                <button onClick={() => setPage(page + 1)} className="h-8 px-3 text-xs flex items-center rounded-md border hover:bg-secondary transition-colors">
                  Next →
                </button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
