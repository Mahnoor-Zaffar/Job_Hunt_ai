import { Card, StatCard } from "@/components/ui";
import { RunScrapersButton } from "@/components/run-scrapers";
import { ScraperStatusPanel } from "@/components/scraper-status";
import { LocationCards } from "@/components/location-cards";
import { RecentAlerts } from "@/components/recent-alerts";

async function getStats() {
  try {
    const res = await fetch("http://localhost:8000/api/v1/analytics/dashboard", { next: { revalidate: 30 } });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

async function getRecDashboard() {
  try {
    const res = await fetch("http://localhost:8000/api/v1/recommendations/dashboard?user_id=00000000-0000-0000-0000-000000000001", { next: { revalidate: 30 } });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

export default async function DashboardPage() {
  const [data, recDataRaw] = await Promise.all([getStats(), getRecDashboard()]);
  const recData = recDataRaw as {
    apply_today_count: number;
    best_matches: any[];
    pipeline_stage_counts: Record<string, number>;
    follow_ups_due: number;
    interviews_scheduled: number;
    offers_received: number;
    missing_skills: string[];
    needs_profile?: boolean;
  } | null;

  const pipelineTotal = recData?.pipeline_stage_counts
    ? Object.values(recData.pipeline_stage_counts).reduce((a: number, b: number) => a + b, 0)
    : 0;

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

      <div className="grid grid-cols-6 gap-4">
        <a href="/jobs?sort=best" className="block">
          <div className="rounded-lg border bg-card p-4 border-l-2 border-l-emerald-500 hover:bg-secondary/30 transition-colors">
            <p className="text-xs font-medium text-muted-foreground mb-1">🔥 Apply Today</p>
            <p className="text-2xl font-semibold tracking-tight">{recData?.apply_today_count ?? 0}</p>
          </div>
        </a>
        <a href="/pipeline" className="block">
          <div className="rounded-lg border bg-card p-4 border-l-2 border-l-blue-500 hover:bg-secondary/30 transition-colors">
            <p className="text-xs font-medium text-muted-foreground mb-1">📄 Pipeline</p>
            <p className="text-2xl font-semibold tracking-tight">{pipelineTotal}</p>
          </div>
        </a>
        <a href="/pipeline?stage=interview" className="block">
          <div className="rounded-lg border bg-card p-4 border-l-2 border-l-amber-500 hover:bg-secondary/30 transition-colors">
            <p className="text-xs font-medium text-muted-foreground mb-1">💼 Interviews</p>
            <p className="text-2xl font-semibold tracking-tight">{recData?.interviews_scheduled ?? data?.stats?.interviews_scheduled ?? 0}</p>
          </div>
        </a>
        <a href="/applications" className="block">
          <div className="rounded-lg border bg-card p-4 border-l-2 border-l-violet-500 hover:bg-secondary/30 transition-colors">
            <p className="text-xs font-medium text-muted-foreground mb-1">📋 Applications</p>
            <p className="text-2xl font-semibold tracking-tight">{data?.stats?.applications_submitted ?? 0}</p>
          </div>
        </a>
        <a href="/pipeline?stage=offer" className="block">
          <div className="rounded-lg border bg-card p-4 border-l-2 border-l-emerald-500 hover:bg-secondary/30 transition-colors">
            <p className="text-xs font-medium text-muted-foreground mb-1">🎉 Offers</p>
            <p className="text-2xl font-semibold tracking-tight">{recData?.offers_received ?? data?.stats?.offers_received ?? 0}</p>
          </div>
        </a>
        {recData?.needs_profile && (
          <a href="/settings" className="block">
            <div className="rounded-lg border bg-card p-4 border-l-2 border-l-rose-500 hover:bg-secondary/30 transition-colors animate-pulse">
              <p className="text-xs font-medium text-muted-foreground mb-1">⚠️ Setup Needed</p>
              <p className="text-sm font-semibold tracking-tight">Create Profile</p>
            </div>
          </a>
        )}
      </div>

      {recData?.missing_skills && recData.missing_skills.length > 0 && (
        <Card title="📄 Skills to Learn">
          <div className="flex gap-2 flex-wrap">
            {recData.missing_skills.map((s: string) => (
              <span key={s} className="text-xs bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded">
                {s}
              </span>
            ))}
          </div>
        </Card>
      )}

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
          <Card title="📅 Follow Ups">
            {recData?.follow_ups_due ? (
              <p className="text-sm font-medium text-amber-600">{recData.follow_ups_due} follow-up{recData.follow_ups_due > 1 ? "s" : ""} due</p>
            ) : (
              <p className="text-xs text-muted-foreground">No follow-ups due</p>
            )}
          </Card>

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

          <RecentAlerts />

          <Card>
            <h3 className="text-sm font-medium mb-3">Quick Links</h3>
            <div className="space-y-1">
              {[
                { href: "/jobs?sort=best", label: "Best match jobs" },
                { href: "/jobs", label: "Browse all jobs" },
                { href: "/remote-jobs", label: "Remote jobs" },
                { href: "/pipeline", label: "Career pipeline" },
                { href: "/applications", label: "Applications" },
                { href: "/settings", label: "Career profile" },
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
