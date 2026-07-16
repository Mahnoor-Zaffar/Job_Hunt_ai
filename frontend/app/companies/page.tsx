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
            No companies yet. Companies are automatically created when jobs are scraped.
            Run the scrapers to populate companies.
          </p>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {data.items.map((c: Record<string, unknown>) => (
            <Card key={String(c.id)}>
              <h3 className="font-semibold">{String(c.name)}</h3>
              <div className="flex gap-2 mt-2 text-xs text-muted-foreground">
                {c.industry && <span className="bg-muted px-2 py-0.5 rounded">{String(c.industry)}</span>}
                {c.size && <span className="bg-muted px-2 py-0.5 rounded">{String(c.size)}</span>}
                {c.is_active ? (
                  <span className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 px-2 py-0.5 rounded">Active</span>
                ) : (
                  <span className="bg-muted px-2 py-0.5 rounded">Inactive</span>
                )}
              </div>
              {c.website && (
                <a href={String(c.website)} target="_blank" rel="noopener" className="text-xs text-primary hover:underline mt-2 inline-block">
                  {String(c.website)}
                </a>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
