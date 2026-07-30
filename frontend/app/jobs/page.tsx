import { Card } from "@/components/ui";
import { AutoApplyButton } from "@/components/auto-apply";

const PER_PAGE = 20;
const QUICK_FILTERS = ["Backend", "Frontend", "Full Stack", "Python", "React", "DevOps", "AI/ML"];

const LABEL_COLORS: Record<string, string> = {
  "Excellent Match": "text-emerald-600 bg-emerald-50 dark:bg-emerald-950 dark:text-emerald-400",
  "Strong Match": "text-blue-600 bg-blue-50 dark:bg-blue-950 dark:text-blue-400",
  "Worth Applying": "text-amber-600 bg-amber-50 dark:bg-amber-950 dark:text-amber-400",
  "Stretch Role": "text-orange-600 bg-orange-50 dark:bg-orange-950 dark:text-orange-400",
  Ignore: "text-gray-500 bg-gray-100 dark:bg-gray-800 dark:text-gray-400",
};

const ACTION_COLORS: Record<string, string> = {
  "Apply Immediately": "bg-emerald-600 hover:bg-emerald-700 text-white",
  "Tailor Resume": "bg-blue-600 hover:bg-blue-700 text-white",
  "Learn Skills First": "bg-amber-600 hover:bg-amber-700 text-white",
  Skip: "bg-gray-300 dark:bg-gray-700 text-muted-foreground cursor-default",
};

async function getJobs(page: number, query: string, showAll: boolean, sort: string, remoteOnly: boolean) {
  const base = "http://localhost:8000/api/v1";
  const USER_ID = "00000000-0000-0000-0000-000000000001";

  if (sort === "best") {
    const params = new URLSearchParams({ user_id: USER_ID, limit: String(PER_PAGE), offset: String((page - 1) * PER_PAGE) });
    if (remoteOnly) params.set("remote_only", "true");
    try {
      const res = await fetch(`${base}/recommendations/ranked?${params.toString()}`, { next: { revalidate: 30 } });
      if (!res.ok) return null;
      const data = await res.json();
      return { items: data, total: data.length, page, per_page: PER_PAGE, pages: Math.ceil(data.length / PER_PAGE) || 1, sort: "best" };
    } catch { return null; }
  }

  const params = new URLSearchParams({ status: "active", per_page: String(PER_PAGE), page: String(page) });
  if (query) { params.set("title", query); }
  else if (!showAll) {
    params.append("keywords", "engineer"); params.append("keywords", "developer");
    params.append("keywords", "software"); params.append("keywords", "programmer");
  }
  if (remoteOnly) params.set("is_remote", "true");
  try {
    const res = await fetch(`${base}/jobs?${params.toString()}`, { next: { revalidate: 30 } });
    if (!res.ok) return null;
    const data = await res.json();
    return { ...data, sort: "latest" };
  } catch { return null; }
}

export default async function JobsPage({ searchParams }: { searchParams: Promise<{ page?: string; q?: string; all?: string; sort?: string; remote?: string }> }) {
  const params = await searchParams;
  const page = Math.max(1, parseInt(params.page || "1", 10) || 1);
  const query = params.q || "";
  const showAll = params.all === "1";
  const sort = params.sort || "best";
  const remoteOnly = params.remote === "1";
  const data = await getJobs(page, query, showAll, sort, remoteOnly);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {data ? `${data.total} jobs found` : "Loading..."}
          </p>
        </div>
      </div>

      <form className="flex gap-2">
        <input type="text" name="q" defaultValue={query} placeholder="Filter by title..." className="flex-1 h-9 px-3 text-sm rounded-md border bg-transparent focus:outline-none focus:ring-2 focus:ring-ring" />
        <button type="submit" className="h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">Search</button>
        {query && <a href="/jobs?sort=best" className="h-9 px-3 text-sm flex items-center rounded-md border text-muted-foreground hover:bg-secondary transition-colors">Clear</a>}
      </form>

      <div className="flex gap-1.5 flex-wrap items-center">
        <a href="/jobs?sort=best" className={`px-2.5 py-1 text-xs rounded-md transition-colors ${sort === "best" ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}>
          Best Match
        </a>
        <a href="/jobs?sort=latest" className={`px-2.5 py-1 text-xs rounded-md transition-colors ${sort === "latest" ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}>
          Latest
        </a>
        <span className="w-px h-4 bg-border mx-1" />
        <a href="/jobs?all=1&sort=latest" className={`px-2.5 py-1 text-xs rounded-md transition-colors ${!query && sort !== "best" && !showAll && !remoteOnly ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}>
          All Jobs
        </a>
        <a href="/jobs?remote=1&sort=latest" className={`px-2.5 py-1 text-xs rounded-md transition-colors ${remoteOnly ? "bg-emerald-600 text-white" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}>
          Remote Only
        </a>
        {QUICK_FILTERS.map(f => (
          <a key={f} href={`/jobs?q=${encodeURIComponent(f)}&sort=latest`} className={`px-2.5 py-1 text-xs rounded-md transition-colors ${query === f ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}>{f}</a>
        ))}
      </div>

      {!data ? (
        <Card><p className="text-sm text-muted-foreground py-8 text-center">Backend unavailable.</p></Card>
      ) : data.items.length === 0 ? (
        <Card><p className="text-sm text-muted-foreground py-8 text-center">No jobs found{query ? ` for "${query}"` : ""}.</p></Card>
      ) : sort === "best" ? (
        <div className="space-y-3">
          {data.items.map((job: Record<string, unknown>, idx: number) => {
            const factors = (job.factors as Record<string, { score: number; max: number }>) || {};
            const totalScore = Object.values(factors).reduce((s: number, f: any) => s + (f.score || 0), 0);
            const maxScore = Object.values(factors).reduce((s: number, f: any) => s + (f.max || 0), 0);
            const pct = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;
            const label = String(job.label || "Unknown");
            const action = String(job.recommended_action || "Skip");
            const why = (job.why as { strengths?: string[]; weaknesses?: string[]; missing_skills?: string[]; recommendations?: string[] }) || {};
            const j = job.job as Record<string, unknown> || {};
            const strengths = why.strengths || [];
            const weaknesses = why.weaknesses || [];
            const missingSkills = why.missing_skills || [];

            return (
              <div key={String(j.id || idx)} className="rounded-lg border bg-card p-4 hover:bg-secondary/20 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-muted-foreground">#{idx + 1}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium uppercase ${LABEL_COLORS[label] || LABEL_COLORS.Ignore}`}>
                        {label}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${ACTION_COLORS[action] || ACTION_COLORS.Skip}`}>
                        {action}
                      </span>
                      <span className="text-[10px] text-muted-foreground">Score: {pct}%</span>
                    </div>
                     <a href={`/jobs/${String(j.id)}`} className="text-sm font-medium hover:text-primary transition-colors block truncate">
                      {String(j.title || "")}
                    </a>
                    <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                      <span>{String(j.company || "")}</span>
                      <span>·</span>
                      <span>{String(j.location || "")}</span>
                      {(j.is_remote as boolean) && (
                        <><span>·</span><span className="text-emerald-600 dark:text-emerald-400 font-medium">Remote</span></>
                      )}
                      {(j.salary_min as number) ? <span>· ${String(j.salary_min)}</span> : null}
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <AutoApplyButton jobId={String(j.id || "")} />
                  </div>
                </div>

                {(strengths.length > 0 || weaknesses.length > 0) && (
                  <div className="mt-3 pl-2 border-l-2 border-border space-y-1">
                    {strengths.slice(0, 3).map((s, i) => (
                      <p key={i} className="text-[11px] text-emerald-600 dark:text-emerald-400">✓ {s}</p>
                    ))}
                    {weaknesses.slice(0, 2).map((w, i) => (
                      <p key={i} className="text-[11px] text-amber-600 dark:text-amber-400">✗ {w}</p>
                    ))}
                  </div>
                )}

                {missingSkills.length > 0 && (
                  <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                    <span className="text-[10px] text-muted-foreground">Missing:</span>
                    {missingSkills.map((s) => (
                      <span key={s} className="text-[10px] bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400 px-1.5 py-0.5 rounded">{s}</span>
                    ))}
                  </div>
                )}

                <div className="mt-2 flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] capitalize bg-secondary px-1.5 py-0.5 rounded text-muted-foreground">{String(j.source || "")}</span>
                  {(j.skills as string[])?.slice(0, 4).map((s: string) => (
                    <span key={s} className="text-[10px] bg-secondary px-1.5 py-0.5 rounded">{s}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <>
          <div className="rounded-lg border">
            {data.items.map((job: Record<string, unknown>) => (
              <div key={String(job.id)} className="flex items-center gap-4 px-5 py-3 border-b last:border-0 hover:bg-secondary/30 transition-colors">
                <div className="flex-1 min-w-0">
                  <a href={`/jobs/${String(job.id)}`} className="text-sm font-medium hover:text-primary transition-colors truncate block">
                    {String(job.title)}
                  </a>
                   <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                     <span>{String(job.company)}</span>
                     <span>·</span>
                     <span>{String(job.location)}</span>
                     {(job.is_remote as boolean) && (
                       <><span>·</span><span className="text-emerald-600 dark:text-emerald-400 font-medium">Remote</span></>
                     )}
                  </div>
                  {(job.skills as string[])?.length > 0 && (
                    <div className="flex gap-1 mt-1.5 flex-wrap">
                      {(job.skills as string[]).slice(0, 4).map((s: string) => (
                        <span key={s} className="text-[10px] bg-secondary px-1.5 py-0.5 rounded">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[10px] capitalize bg-secondary px-1.5 py-0.5 rounded text-muted-foreground">{String(job.source)}</span>
                  {job.salary_min ? <span className="text-xs font-medium whitespace-nowrap">${String(job.salary_min)}</span> : null}
                  <AutoApplyButton jobId={String(job.id)} />
                </div>
              </div>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="flex justify-center gap-1">
              {page > 1 && <a href={`/jobs?page=${page - 1}${query ? `&q=${query}` : ""}&sort=${sort}`} className="h-8 px-3 text-xs flex items-center rounded-md border hover:bg-secondary transition-colors">← Prev</a>}
              {Array.from({ length: data.pages }, (_, i) => i + 1).filter(p => p === 1 || p === data.pages || Math.abs(p - page) <= 2).map((p, i, arr) => (
                <span key={p}>
                  {i > 0 && arr[i - 1] !== p - 1 && <span className="px-1 text-muted-foreground text-xs">…</span>}
                  <a href={`/jobs?page=${p}${query ? `&q=${query}` : ""}&sort=${sort}`} className={`h-8 w-8 text-xs flex items-center justify-center rounded-md transition-colors ${p === page ? "bg-primary text-primary-foreground" : "border hover:bg-secondary"}`}>{p}</a>
                </span>
              ))}
              {page < data.pages && <a href={`/jobs?page=${page + 1}${query ? `&q=${query}` : ""}&sort=${sort}`} className="h-8 px-3 text-xs flex items-center rounded-md border hover:bg-secondary transition-colors">Next →</a>}
            </div>
          )}
        </>
      )}
    </div>
  );
}
