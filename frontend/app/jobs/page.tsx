import { Card } from "@/components/ui";

async function getJobs() {
  try {
    return await (
      await fetch("http://localhost:8000/api/v1/jobs?status=active&per_page=20")
    ).json();
  } catch {
    return { items: [], total: 0 };
  }
}

export default async function JobsPage() {
  const data = await getJobs();

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Jobs</h1>
        <span className="text-sm text-muted-foreground">{data.total} total</span>
      </div>
      <div className="space-y-3">
        {data.items.map((job: Record<string, unknown>) => (
          <Card key={String(job.id)}>
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold">{String(job.title)}</h3>
                <p className="text-sm text-muted-foreground">
                  {String(job.company)} — {String(job.location)}
                </p>
                {(job.skills as string[])?.length > 0 && (
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {(job.skills as string[]).slice(0, 6).map((s: string) => (
                      <span key={s} className="text-xs bg-muted px-2 py-0.5 rounded">
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end gap-2 text-sm text-muted-foreground">
                <span className="capitalize">{String(job.source)}</span>
                {job.salary_min && (
                  <span className="text-primary font-medium">
                    ${String(job.salary_min)}–${String(job.salary_max)}
                  </span>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
