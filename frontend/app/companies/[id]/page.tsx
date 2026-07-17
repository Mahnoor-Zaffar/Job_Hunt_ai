import { Card } from "@/components/ui";
import { BarChart } from "@/components/charts";

async function getCompany(id: string) {
  try {
    const res = await fetch(`http://localhost:8000/api/v1/companies/${id}`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

async function getCompanyJobs(name: string) {
  try {
    const res = await fetch(`http://localhost:8000/api/v1/jobs?company=${encodeURIComponent(name)}&per_page=20`, { next: { revalidate: 60 } });
    if (!res.ok) return { items: [], total: 0 };
    return await res.json();
  } catch { return { items: [], total: 0 } };
}

export default async function CompanyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const company = await getCompany(id);
  if (!company) {
    return (
      <div>
        <a href="/companies" className="text-sm text-primary hover:underline mb-4 inline-block">← Back to Companies</a>
        <Card><p className="text-sm text-muted-foreground py-8 text-center">Company not found.</p></Card>
      </div>
    );
  }

  const jobs = await getCompanyJobs(company.name);

  return (
    <div>
      <a href="/companies" className="text-sm text-primary hover:underline mb-4 inline-block">← Back to Companies</a>

      <div className="mb-6">
        <h1 className="text-2xl font-bold">{company.name}</h1>
        <div className="flex gap-2 mt-2 flex-wrap text-sm">
          {company.industry && <span className="bg-muted px-2 py-1 rounded text-xs">{company.industry}</span>}
          {company.size && <span className="bg-muted px-2 py-1 rounded text-xs">{company.size}</span>}
          {company.headquarters && <span className="bg-muted px-2 py-1 rounded text-xs">{company.headquarters}</span>}
          {company.website && (
            <a href={company.website} target="_blank" rel="noopener" className="text-primary hover:underline text-xs">
              {company.website}
            </a>
          )}
        </div>
        {company.description && (
          <p className="text-sm text-muted-foreground mt-3">{company.description}</p>
        )}
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <Card title={`Open Jobs (${jobs.total})`}>
            {jobs.items.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">No open jobs found.</p>
            ) : (
              <div className="space-y-2">
                {jobs.items.map((job: Record<string, unknown>) => (
                  <a
                    key={String(job.id)}
                    href={`/jobs/${String(job.id)}`}
                    className="block p-3 rounded-lg border hover:border-primary/30 transition-colors"
                  >
                    <h4 className="font-medium text-sm">{String(job.title)}</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      {String(job.location)} · {String(job.source)}
                    </p>
                    {(job.skills as string[])?.length > 0 && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {(job.skills as string[]).slice(0, 5).map((s: string) => (
                          <span key={s} className="text-[10px] bg-muted px-1.5 py-0.5 rounded">{s}</span>
                        ))}
                      </div>
                    )}
                  </a>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <h3 className="font-semibold text-sm mb-3">Quick Actions</h3>
            <div className="space-y-2">
              <a
                href={`http://localhost:8000/api/v1/career/research/company/${encodeURIComponent(company.name)}`}
                target="_blank"
                className="block px-3 py-2 text-xs border rounded hover:bg-muted transition-colors"
              >
                🔬 AI Company Research
              </a>
              <a
                href={`http://localhost:8000/api/v1/career/contacts/${encodeURIComponent(company.name)}`}
                target="_blank"
                className="block px-3 py-2 text-xs border rounded hover:bg-muted transition-colors"
              >
                👥 Find Contacts
              </a>
              <a
                href={`/jobs?company=${encodeURIComponent(company.name)}`}
                className="block px-3 py-2 text-xs border rounded hover:bg-muted transition-colors"
              >
                🔍 All {company.name} Jobs
              </a>
            </div>
          </Card>

          {company.description && (
            <Card title="About">
              <p className="text-xs text-muted-foreground leading-relaxed">{String(company.description).slice(0, 500)}</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
