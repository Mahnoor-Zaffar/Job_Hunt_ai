import { BarChart, StatPill } from "@/components/charts";
import { Card, StatCard } from "@/components/ui";
import { RunScrapersButton } from "@/components/run-scrapers";
import { ScraperStatusPanel } from "@/components/scraper-status";
import { LocationCards } from "@/components/location-cards";

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
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {data?.stats?.last_scrape
              ? `Last scrape: ${new Date(data.stats.last_scrape).toLocaleString()}`
              : "No scrapes yet"}
          </p>
        </div>
        <RunScrapersButton />
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Jobs" value={data?.stats?.total_jobs ?? 0} color="blue" />
        <StatCard label="Active Jobs" value={data?.stats?.active_jobs ?? 0} color="green" />
        <StatCard label="Submitted" value={data?.stats?.applications_submitted ?? 0} color="purple" />
        <StatCard label="Interviews" value={data?.stats?.interviews_scheduled ?? 0} color="amber" />
      </div>

      {/* Source breakdown quick pills */}
      {data?.jobs_by_source?.length ? (
        <div className="flex gap-2 flex-wrap">
          {data.jobs_by_source.map((s: { source: string; count: number }, i: number) => (
            <StatPill
              key={s.source}
              label={s.source}
              count={s.count}
              color={["blue", "purple", "green", "amber", "red"][i % 5]}
            />
          ))}
        </div>
      ) : null}

      {/* Charts Row 1 */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card title="Jobs by Source">
          {data?.jobs_by_source?.length ? (
            <BarChart data={data.jobs_by_source.map((s: { source: string; count: number }) => ({ label: s.source, value: s.count }))} />
          ) : (
            <p className="text-sm text-muted-foreground py-4 text-center">No data yet</p>
          )}
        </Card>

        <Card title="Top Technologies">
          {data?.top_technologies?.length ? (
            <BarChart data={data.top_technologies.slice(0, 8).map((s: { source: string; count: number }) => ({ label: s.source, value: s.count }))} />
          ) : (
            <p className="text-sm text-muted-foreground py-4 text-center">No data yet</p>
          )}
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid md:grid-cols-2 gap-6">
        {data?.jobs_by_location?.length ? (
          <Card title="Jobs by Location">
            <LocationCards data={data.jobs_by_location} />
          </Card>
        ) : null}

        {data?.applications_by_status?.length ? (
          <Card title="Applications by Status">
            <BarChart data={data.applications_by_status.map((s: { source: string; count: number }) => ({ label: s.source || "none", value: s.count }))} />
          </Card>
        ) : null}
      </div>

      {/* Scraper Status */}
      <Card title="Scraper Status">
        <ScraperStatusPanel />
      </Card>

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <ActionCard icon="🔍" title="Browse Jobs" href="/jobs" primary />
          <ActionCard icon="👨‍💻" title="Backend Jobs" href="/jobs?q=backend" />
          <ActionCard icon="🎨" title="Frontend Jobs" href="/jobs?q=frontend" />
          <ActionCard icon="🤖" title="AI Jobs" href="/jobs?q=ai" />
          <ActionCard icon="📄" title="Upload Resume" href="/resume" />
          <ActionCard icon="🏢" title="Companies" href="/companies" />
          <ActionCard icon="📊" title="API Docs" href="http://localhost:8000/docs" />
          <ActionCard icon="🧪" title="AI Evaluation" href="http://localhost:8000/api/v1/ai/evaluate" />
        </div>
      </div>
    </div>
  );
}

function ActionCard({ icon, title, href, primary = false }: { icon: string; title: string; href: string; primary?: boolean }) {
  return (
    <a
      href={href}
      target={href.startsWith("http") ? "_blank" : undefined}
      rel={href.startsWith("http") ? "noopener" : undefined}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
        primary
          ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
          : "bg-muted hover:bg-muted/70 border border-transparent hover:border-border"
      }`}
    >
      <span className="text-lg">{icon}</span>
      <span className="text-sm font-medium">{title}</span>
    </a>
  );
}
