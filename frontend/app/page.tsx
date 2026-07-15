import { Card, StatCard } from "@/components/ui";

async function getStats() {
  try {
    const res = await fetch("http://localhost:8000/api/v1/analytics/dashboard", {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const data = await getStats();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Jobs" value={data?.stats?.total_jobs ?? 0} />
        <StatCard label="Active Jobs" value={data?.stats?.active_jobs ?? 0} />
        <StatCard label="Applications" value={data?.stats?.applications_submitted ?? 0} />
        <StatCard label="Interviews" value={data?.stats?.interviews_scheduled ?? 0} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card title="Jobs by Source">
          {data?.jobs_by_source?.length ? (
            <ul className="space-y-2">
              {data.jobs_by_source.map(
                (s: { source: string; count: number }, i: number) => (
                  <li key={i} className="flex justify-between text-sm">
                    <span className="text-muted-foreground capitalize">
                      {s.source}
                    </span>
                    <span className="font-medium">{s.count}</span>
                  </li>
                ),
              )}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              {data ? "No data yet" : "Backend unavailable — start the API server"}
            </p>
          )}
        </Card>

        <Card title="Applications by Status">
          {data?.applications_by_status?.length ? (
            <ul className="space-y-2">
              {data.applications_by_status.map(
                (s: { source: string; count: number }, i: number) => (
                  <li key={i} className="flex justify-between text-sm">
                    <span className="text-muted-foreground capitalize">
                      {s.source}
                    </span>
                    <span className="font-medium">{s.count}</span>
                  </li>
                ),
              )}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              {data ? "No data yet" : "Backend unavailable — start the API server"}
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
