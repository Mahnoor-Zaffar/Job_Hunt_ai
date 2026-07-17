import { Card } from "@/components/ui";

async function getCompanies() {
  try {
    const res = await fetch("http://localhost:8000/api/v1/companies?per_page=50", { next: { revalidate: 60 } });
    if (!res.ok) return { items: [] };
    return await res.json();
  } catch { return { items: [] }; }
}

export default async function CompaniesPage() {
  const data = await getCompanies();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Companies</h1>

      {data.items.length === 0 ? (
        <Card>
          <p className="text-sm text-muted-foreground py-8 text-center">
            No companies yet. Run the scrapers to discover companies.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {data.items.map((c: Record<string, unknown>) => (
            <Card key={String(c.id)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <a
                      href={`/companies/${encodeURIComponent(String(c.id))}`}
                      className="font-semibold hover:text-primary transition-colors"
                    >
                      {String(c.name)}
                    </a>
                    {c.is_active ? (
                      <span className="text-[10px] bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 px-1.5 py-0.5 rounded-full font-medium">
                        Active
                      </span>
                    ) : null}
                  </div>
                  <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                    {c.industry ? <span className="bg-muted px-2 py-0.5 rounded">{String(c.industry)}</span> : null}
                    {c.size ? <span className="bg-muted px-2 py-0.5 rounded">{String(c.size)}</span> : null}
                  </div>
                  {c.website ? (
                    <a href={String(c.website)} target="_blank" rel="noopener" className="text-xs text-primary hover:underline mt-1 inline-block">
                      {String(c.website)}
                    </a>
                  ) : null}
                </div>
                <div className="flex items-center gap-3">
                  {Number(c.job_count) > 0 ? (
                    <a
                      href={`/jobs?company=${encodeURIComponent(String(c.name))}`}
                      className="flex flex-col items-center px-4 py-2 rounded-lg bg-muted hover:bg-muted/70 transition-colors"
                    >
                      <span className="text-xl font-bold">{String(c.job_count)}</span>
                      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Jobs</span>
                    </a>
                  ) : null}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
