import { Card, StatCard } from "@/components/ui";
import { RunScrapersButton } from "@/components/run-scrapers";
import { ScraperStatusPanel } from "@/components/scraper-status";
import { StartupFinder } from "@/components/startup-finder";
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {data?.stats?.last_scrape
              ? `Last scrape ${new Date(data.stats.last_scrape).toLocaleString()}`
              : "No data yet"}
          </p>
        </div>
        <RunScrapersButton />
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Jobs" value={data?.stats?.total_jobs ?? 0} color="indigo" />
        <StatCard label="Active" value={data?.stats?.active_jobs ?? 0} color="emerald" />
        <StatCard label="Applied" value={data?.stats?.applications_submitted ?? 0} color="violet" />
        <StatCard label="Interviews" value={data?.stats?.interviews_scheduled ?? 0} color="amber" />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <Card>
            <h3 className="text-sm font-medium mb-4">Jobs by Source</h3>
            {data?.jobs_by_source?.length ? (
              <div className="space-y-3">
                {data.jobs_by_source.map((s: { source: string; count: number }) => {
                  const max = Math.max(...data.jobs_by_source.map((x: { count: number }) => x.count), 1);
                  const pct = (s.count / max) * 100;
                  return (
                    <div key={s.source} className="flex items-center gap-3">
                      <span className="w-24 text-xs text-muted-foreground capitalize truncate">{s.source}</span>
                      <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                        <div className="h-full bg-primary rounded-full transition-all duration-700" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-xs font-medium tabular-nums w-8 text-right">{s.count}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-4 text-center">No data yet</p>
            )}
          </Card>

          <Card>
            <h3 className="text-sm font-medium mb-4">Top Technologies</h3>
            {data?.top_technologies?.length ? (
              <div className="space-y-3">
                {data.top_technologies.slice(0, 8).map((s: { source: string; count: number }) => {
                  const max = Math.max(...data.top_technologies.slice(0, 8).map((x: { count: number }) => x.count), 1);
                  const pct = (s.count / max) * 100;
                  return (
                    <div key={s.source} className="flex items-center gap-3">
                      <span className="w-24 text-xs text-muted-foreground truncate">{s.source}</span>
                      <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full transition-all duration-700" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-xs font-medium tabular-nums w-8 text-right">{s.count}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-4 text-center">No data yet</p>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          {data?.jobs_by_location?.length ? (
            <Card>
              <h3 className="text-sm font-medium mb-4">Locations</h3>
              <LocationCards data={data.jobs_by_location} />
            </Card>
          ) : null}

          <Card>
            <h3 className="text-sm font-medium mb-4">Scrapers</h3>
            <ScraperStatusPanel />
          </Card>

          <Card>
            <h3 className="text-sm font-medium mb-4">Pakistan Startups</h3>
            <StartupFinder />
          </Card>

          <Card>
            <h3 className="text-sm font-medium mb-3">Quick Links</h3>
            <div className="space-y-1">
              {[
                { href: "/jobs", label: "Browse all jobs" },
                { href: "/jobs?q=backend", label: "Backend jobs" },
                { href: "/jobs?q=frontend", label: "Frontend jobs" },
                { href: "/resume", label: "Upload resume" },
                { href: "/companies", label: "Companies" },
              ].map((link) => (
                <a key={link.href} href={link.href} className="block text-xs text-muted-foreground hover:text-foreground py-1.5 px-2 -mx-2 rounded hover:bg-secondary/50 transition-colors">
                  {link.label}
                </a>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
