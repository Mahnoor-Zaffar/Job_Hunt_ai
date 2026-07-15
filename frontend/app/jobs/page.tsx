import { Card } from "@/components/ui";

const PER_PAGE = 20;

async function getJobs(page: number) {
  try {
    const res = await fetch(
      `http://localhost:8000/api/v1/jobs?status=active&per_page=${PER_PAGE}&page=${page}`,
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
  searchParams: Promise<{ page?: string }>;
}) {
  const params = await searchParams;
  const page = Math.max(1, parseInt(params.page || "1", 10) || 1);
  const data = await getJobs(page);

  if (!data) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Jobs</h1>
        <Card>
          <p className="text-sm text-muted-foreground py-8 text-center">
            Backend API is not available.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Jobs</h1>
        <span className="text-sm text-muted-foreground">
          {data.total} total &middot; Page {data.page} of {data.pages}
        </span>
      </div>
      <div className="space-y-3">
        {data.items.map((job: Record<string, unknown>) => (
          <Card key={String(job.id)}>
            <div className="flex justify-between items-start">
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold truncate">{String(job.title)}</h3>
                <p className="text-sm text-muted-foreground">
                  {String(job.company)} — {String(job.location)}
                  {job.city ? ` (${String(job.city)})` : ""}
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
                    {(job.skills as string[])
                      .slice(0, 8)
                      .map((s: string) => (
                        <span
                          key={s}
                          className="text-xs bg-muted px-2 py-0.5 rounded"
                        >
                          {s}
                        </span>
                      ))}
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end gap-1 text-sm text-muted-foreground shrink-0 ml-4">
                {job.salary_min ? (
                  <span className="text-primary font-medium whitespace-nowrap">
                    ${String(job.salary_min)}–${String(job.salary_max)}
                  </span>
                ) : null}
                {job.apply_url ? (
                  <a
                    href={String(job.apply_url)}
                    target="_blank"
                    rel="noopener"
                    className="text-xs text-primary hover:underline"
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
              href={`/jobs?page=${page - 1}`}
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
                  href={`/jobs?page=${p}`}
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
              href={`/jobs?page=${page + 1}`}
              className="px-3 py-1.5 text-sm border rounded hover:bg-muted transition-colors"
            >
              Next →
            </a>
          )}
        </div>
      )}
    </div>
  );
}
