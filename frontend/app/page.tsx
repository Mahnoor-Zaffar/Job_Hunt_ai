import { BarChart } from "@/components/charts";
import { Card, StatCard } from "@/components/ui";
import { RunScrapersButton } from "@/components/run-scrapers";

async function getStats() {
  try {
    const res = await fetch("http://localhost:8000/api/v1/analytics/dashboard", { next: { revalidate: 30 } });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

export default async function DashboardPage() {
  const data = await getStats();

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <RunScrapersButton />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Jobs" value={data?.stats?.total_jobs ?? 0} />
        <StatCard label="Active Jobs" value={data?.stats?.active_jobs ?? 0} />
        <StatCard label="Applications" value={data?.stats?.applications_submitted ?? 0} />
        <StatCard label="Interviews" value={data?.stats?.interviews_scheduled ?? 0} />
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <Card title="Jobs by Source">
          {data?.jobs_by_source?.length ? (
            <BarChart data={data.jobs_by_source.map((s: { source: string; count: number }) => ({ label: s.source, value: s.count }))} />
          ) : (
            <p className="text-sm text-muted-foreground">Backend unavailable — start the API server</p>
          )}
        </Card>

        <Card title="Applications by Status">
          {data?.applications_by_status?.length ? (
            <BarChart data={data.applications_by_status.map((s: { source: string; count: number }) => ({ label: s.source || "none", value: s.count }))} />
          ) : (
            <p className="text-sm text-muted-foreground">No applications yet</p>
          )}
        </Card>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {data?.jobs_by_location?.length ? (
          <Card title="Jobs by Location">
            <BarChart data={data.jobs_by_location.map((s: { source: string; count: number }) => ({ label: s.source, value: s.count }))} />
          </Card>
        ) : null}

        {data?.top_technologies?.length ? (
          <Card title="Top Technologies">
            <BarChart data={data.top_technologies.slice(0, 8).map((s: { source: string; count: number }) => ({ label: s.source, value: s.count }))} />
          </Card>
        ) : null}
      </div>

      <Card title="Quick Actions">
        <div className="flex gap-3 flex-wrap">
          <a href="/jobs" className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors">
            Browse All Jobs
          </a>
          <a href="/jobs?q=backend" className="px-4 py-2 text-sm border rounded hover:bg-muted transition-colors">
            Backend Jobs
          </a>
          <a href="/jobs?q=frontend" className="px-4 py-2 text-sm border rounded hover:bg-muted transition-colors">
            Frontend Jobs
          </a>
          <a href="http://localhost:8000/docs" target="_blank" className="px-4 py-2 text-sm border rounded hover:bg-muted transition-colors">
            API Docs
          </a>
          <a href="http://localhost:8000/api/v1/ai/evaluate" target="_blank" className="px-4 py-2 text-sm border rounded hover:bg-muted transition-colors">
            AI Evaluation
          </a>
        </div>
      </Card>
    </div>
  );
}
