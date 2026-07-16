import { Card } from "@/components/ui";

const PER_PAGE = 20;

const QUICK_FILTERS = [
  "Backend",
  "Frontend",
  "Full Stack",
  "Python",
  "JavaScript",
  "React",
  "Node.js",
  "DevOps",
  "Data Engineer",
  "AI/ML",
  "Mobile",
  "QA",
];

const SOFTWARE_KEYWORDS = [
  "software", "engineer", "developer", "full stack", "fullstack",
  "backend", "back-end", "frontend", "front-end", "web", "python",
  "javascript", "typescript", "react", "node", "java", "devops",
  "cloud", "data engineer", "data scientist", "ai", "ml", "machine learning",
  "mobile", "android", "ios", "flutter", "go", "rust", "php",
  "ruby", "c#", ".net", "angular", "vue", "django", "fastapi",
  "spring", "kubernetes", "docker", "aws", "azure", "gcp",
  "qa", "quality", "test", "sdet", "security", "cybersecurity",
  "architect", "tech lead", "staff engineer", "principal",
  "blockchain", "embedded", "firmware", "game dev", "unity",
  "database", "dba", "sql", "postgresql", "mongodb",
  "site reliability", "sre", "platform engineer",
];

async function getJobs(page: number, query: string, showAll: boolean = false) {
  const params = new URLSearchParams({
    status: "active",
    per_page: String(PER_PAGE),
    page: String(page),
  });
  if (query) {
    params.set("title", query);
  } else if (!showAll) {
    params.append("keywords", "engineer");
    params.append("keywords", "developer");
    params.append("keywords", "software");
    params.append("keywords", "programmer");
  }

  try {
    const res = await fetch(
      `http://localhost:8000/api/v1/jobs?${params.toString()}`,
      { next: { revalidate: 30 } },
    );
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function JobsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; q?: string; all?: string }>;
}) {
  const params = await searchParams;
  const page = Math.max(1, parseInt(params.page || "1", 10) || 1);
  const query = params.q || "";
  const showAll = params.all === "1";
  const data = await getJobs(page, query, showAll);

  const currentFilter = query;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Jobs</h1>
        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total} total &middot; Page {data.page} of {data.pages}
          </span>
        )}
      </div>

      {/* Search */}
      <form className="flex gap-2 mb-4">
        <input
          type="text"
          name="q"
          defaultValue={query}
          placeholder="Filter by title (e.g. Backend, Python, React)..."
          className="flex-1 px-3 py-2 text-sm border rounded bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
        <button
          type="submit"
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
        >
          Search
        </button>
        {query && (
          <a
            href="/jobs"
            className="px-3 py-2 text-sm border rounded text-muted-foreground hover:bg-muted transition-colors"
          >
            Clear
          </a>
        )}
      </form>

      {/* Quick filters */}
      <div className="flex gap-1.5 mb-6 flex-wrap">
        <a
          href="/jobs?all=1"
          className={`px-2.5 py-1 text-xs rounded transition-colors ${
            !query ? "bg-primary text-primary-foreground" : "bg-muted hover:bg-muted/70 text-muted-foreground"
          }`}
        >
          Software Jobs
        </a>
        {QUICK_FILTERS.map((f) => (
          <a
            key={f}
            href={`/jobs?q=${encodeURIComponent(f)}`}
            className={`px-2.5 py-1 text-xs rounded transition-colors ${
              currentFilter === f
                ? "bg-primary text-primary-foreground"
                : "bg-muted hover:bg-muted/70 text-muted-foreground"
            }`}
          >
            {f}
          </a>
        ))}
      </div>

      {!data ? (
        <Card>
          <p className="text-sm text-muted-foreground py-8 text-center">
            Backend API is not available.
          </p>
        </Card>
      ) : data.items.length === 0 ? (
        <Card>
          <p className="text-sm text-muted-foreground py-8 text-center">
            No jobs found{query ? ` for "${query}"` : ""}. Try a different filter or run the scrapers.
          </p>
        </Card>
      ) : (
        <>
          <div className="space-y-3">
            {data.items.map((job: Record<string, unknown>) => (
              <Card key={String(job.id)}>
                <div className="flex justify-between items-start">
                  <div className="min-w-0 flex-1">
                    <a href={`/jobs/${String(job.id)}`} className="hover:text-primary transition-colors">
                      <h3 className="font-semibold truncate">{String(job.title)}</h3>
                    </a>
                    <p className="text-sm text-muted-foreground">
                      {String(job.company)} — {String(job.location)}
                    </p>
                    <div className="flex gap-2 mt-1 items-center text-xs text-muted-foreground">
                      <span className="capitalize bg-muted px-1.5 py-0.5 rounded">
                        {String(job.source)}
                      </span>
                      {job.remote_type && job.remote_type !== "onsite" && (
                        <span className="capitalize">{String(job.remote_type)}</span>
                      )}
                    </div>
                    {(job.skills as string[])?.length > 0 && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {(job.skills as string[]).slice(0, 8).map((s: string) => (
                          <span key={s} className="text-xs bg-muted px-2 py-0.5 rounded">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2 text-sm text-muted-foreground shrink-0 ml-4">
                    {job.salary_min ? (
                      <span className="text-primary font-medium whitespace-nowrap">
                        ${String(job.salary_min)}–${String(job.salary_max)}
                      </span>
                    ) : null}
                    <a
                      href={`/jobs/${String(job.id)}`}
                      className="text-xs text-primary hover:underline font-medium"
                    >
                      View Details →
                    </a>
                    {job.apply_url ? (
                      <a
                        href={String(job.apply_url)}
                        target="_blank"
                        rel="noopener"
                        className="text-xs text-muted-foreground hover:underline"
                      >
                        Apply →
                      </a>
                    ) : null}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              {page > 1 && (
                <a
                  href={`/jobs?page=${page - 1}${query ? `&q=${encodeURIComponent(query)}` : ""}`}
                  className="px-3 py-1.5 text-sm border rounded hover:bg-muted transition-colors"
                >
                  ← Previous
                </a>
              )}
              {Array.from({ length: data.pages }, (_, i) => i + 1)
                .filter((p) => p === 1 || p === data.pages || Math.abs(p - page) <= 2)
                .map((p, i, arr) => (
                  <span key={p}>
                    {i > 0 && arr[i - 1] !== p - 1 && (
                      <span className="px-1 text-muted-foreground">…</span>
                    )}
                    <a
                      href={`/jobs?page=${p}${query ? `&q=${encodeURIComponent(query)}` : ""}`}
                      className={`px-3 py-1.5 text-sm border rounded transition-colors ${
                        p === page
                          ? "bg-primary text-primary-foreground border-primary"
                          : "hover:bg-muted"
                      }`}
                    >
                      {p}
                    </a>
                  </span>
                ))}
              {page < data.pages && (
                <a
                  href={`/jobs?page=${page + 1}${query ? `&q=${encodeURIComponent(query)}` : ""}`}
                  className="px-3 py-1.5 text-sm border rounded hover:bg-muted transition-colors"
                >
                  Next →
                </a>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
