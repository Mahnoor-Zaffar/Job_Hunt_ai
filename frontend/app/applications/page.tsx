import { Card } from "@/components/ui";

async function getApplications() {
  try {
    const res = await fetch("http://localhost:8000/api/v1/applications?user_id=00000000-0000-0000-0000-000000000001&per_page=20", { next: { revalidate: 30 } });
    if (!res.ok) return { items: [] };
    return await res.json();
  } catch { return { items: [] }; }
}

const STATUS_COLORS: Record<string, string> = {
  draft: "text-muted-foreground bg-secondary",
  submitted: "text-blue-600 bg-blue-50 dark:bg-blue-950 dark:text-blue-400",
  under_review: "text-violet-600 bg-violet-50 dark:bg-violet-950 dark:text-violet-400",
  interview: "text-amber-600 bg-amber-50 dark:bg-amber-950 dark:text-amber-400",
  offer: "text-emerald-600 bg-emerald-50 dark:bg-emerald-950 dark:text-emerald-400",
  rejected: "text-rose-600 bg-rose-50 dark:bg-rose-950 dark:text-rose-400",
};

export default async function ApplicationsPage() {
  const data = await getApplications();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Applications</h1>
        <p className="text-sm text-muted-foreground mt-1">Track your job applications through the pipeline</p>
      </div>

      {data.items.length === 0 ? (
        <Card>
          <div className="py-12 text-center">
            <p className="text-sm text-muted-foreground">No applications yet</p>
            <p className="text-xs text-muted-foreground mt-1">Browse jobs and click "Quick Apply" to start tracking</p>
          </div>
        </Card>
      ) : (
        <div className="rounded-lg border">
          {data.items.map((app: Record<string, unknown>) => (
            <div key={String(app.id)} className="flex items-center gap-4 px-5 py-3 border-b last:border-0 hover:bg-secondary/30 transition-colors">
              <div className="flex-1 min-w-0">
                <a href={`/jobs/${String(app.job_id)}`} className="text-sm font-medium hover:text-primary transition-colors">
                  Application #{String(app.id).slice(0, 8)}
                </a>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                  {!!app.applied_at && <span>{new Date(String(app.applied_at)).toLocaleDateString()}</span>}
                  {!!app.notes && <span>· {String(app.notes).slice(0, 60)}</span>}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase ${STATUS_COLORS[String(app.status)] || STATUS_COLORS.draft}`}>
                  {String(app.status).replace("_", " ")}
                </span>
                {!!app.match_score ? (
                  <span className="text-xs font-medium">{(Number(app.match_score) * 100).toFixed(0)}%</span>
                ) : null}
                <a href={`/jobs/${String(app.job_id)}`} className="text-xs text-muted-foreground hover:text-foreground transition-colors">View →</a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
