import { Card } from "@/components/ui";
import { QuickApplyButton } from "@/components/quick-apply";

const PER_PAGE = 20;

const QUICK_FILTERS = ["Backend", "Frontend", "Full Stack", "Python", "React", "DevOps", "AI/ML"];

async function getJobs(page: number, query: string, showAll: boolean) {
  const params = new URLSearchParams({ status: "active", per_page: String(PER_PAGE), page: String(page) });
  if (query) { params.set("title", query); }
  else if (!showAll) {
    params.append("keywords", "engineer"); params.append("keywords", "developer");
    params.append("keywords", "software"); params.append("keywords", "programmer");
  }
  try {
    const res = await fetch(`http://localhost:8000/api/v1/jobs?${params.toString()}`, { next: { revalidate: 30 } });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

export default async function JobsPage({ searchParams }: { searchParams: Promise<{ page?: string; q?: string; all?: string }> }) {
  const params = await searchParams;
  const page = Math.max(1, parseInt(params.page || "1", 10) || 1);
  const query = params.q || "";
  const showAll = params.all === "1";
  const data = await getJobs(page, query, showAll);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {data ? `${data.total} jobs found` : "Loading..."}
        </p>
      </div>

      <form className="flex gap-2">
        <input type="text" name="q" defaultValue={query} placeholder="Filter by title..." className="flex-1 h-9 px-3 text-sm rounded-md border bg-transparent focus:outline-none focus:ring-2 focus:ring-ring" />
        <button type="submit" className="h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">Search</button>
        {query && <a href="/jobs" className="h-9 px-3 text-sm flex items-center rounded-md border text-muted-foreground hover:bg-secondary transition-colors">Clear</a>}
      </form>

      <div className="flex gap-1.5 flex-wrap">
        <a href="/jobs?all=1" className={`px-2.5 py-1 text-xs rounded-md transition-colors ${!query ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}>Software Jobs</a>
        {QUICK_FILTERS.map(f => (
          <a key={f} href={`/jobs?q=${encodeURIComponent(f)}`} className={`px-2.5 py-1 text-xs rounded-md transition-colors ${query === f ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}>{f}</a>
        ))}
      </div>

      {!data ? (
        <Card><p className="text-sm text-muted-foreground py-8 text-center">Backend unavailable.</p></Card>
      ) : data.items.length === 0 ? (
        <Card><p className="text-sm text-muted-foreground py-8 text-center">No jobs found{query ? ` for "${query}"` : ""}.</p></Card>
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
                  <QuickApplyButton jobId={String(job.id)} />
                </div>
              </div>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="flex justify-center gap-1">
              {page > 1 && <a href={`/jobs?page=${page - 1}${query ? `&q=${query}` : ""}`} className="h-8 px-3 text-xs flex items-center rounded-md border hover:bg-secondary transition-colors">← Prev</a>}
              {Array.from({ length: data.pages }, (_, i) => i + 1).filter(p => p === 1 || p === data.pages || Math.abs(p - page) <= 2).map((p, i, arr) => (
                <span key={p}>
                  {i > 0 && arr[i - 1] !== p - 1 && <span className="px-1 text-muted-foreground text-xs">…</span>}
                  <a href={`/jobs?page=${p}${query ? `&q=${query}` : ""}`} className={`h-8 w-8 text-xs flex items-center justify-center rounded-md transition-colors ${p === page ? "bg-primary text-primary-foreground" : "border hover:bg-secondary"}`}>{p}</a>
                </span>
              ))}
              {page < data.pages && <a href={`/jobs?page=${page + 1}${query ? `&q=${query}` : ""}`} className="h-8 px-3 text-xs flex items-center rounded-md border hover:bg-secondary transition-colors">Next →</a>}
            </div>
          )}
        </>
      )}
    </div>
  );
}
