import { Card } from "@/components/ui";

async function getApplications() {
  try {
    const res = await fetch(
      "http://localhost:8000/api/v1/applications?user_id=00000000-0000-0000-0000-000000000001&per_page=20",
      { next: { revalidate: 30 } }
    );
    if (!res.ok) return { items: [] };
    return await res.json();
  } catch { return { items: [] }; }
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
  submitted: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  under_review: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  interview: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  offer: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  rejected: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
  withdrawn: "bg-gray-100 text-gray-500",
};

export default async function ApplicationsPage() {
  const data = await getApplications();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Applications</h1>

      {data.items.length === 0 ? (
        <Card>
          <p className="text-sm text-muted-foreground py-8 text-center">
            No applications yet. Browse jobs and click "Quick Apply" to start tracking.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {data.items.map((app: Record<string, unknown>) => (
            <Card key={String(app.id)}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">
                    <a href={`/jobs/${String(app.job_id)}`} className="hover:text-primary transition-colors">
                      Application #{String(app.id).slice(0, 8)}
                    </a>
                  </h3>
                  <div className="flex gap-2 mt-1 items-center">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wider ${STATUS_COLORS[String(app.status)] || STATUS_COLORS.draft}`}
                    >
                      {String(app.status).replace("_", " ")}
                    </span>
                    {app.applied_at && (
                      <span className="text-xs text-muted-foreground">
                        Applied: {new Date(String(app.applied_at)).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  {app.notes && (
                    <p className="text-xs text-muted-foreground mt-1">{String(app.notes)}</p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {app.match_score ? (
                    <span className="text-xs font-medium">
                      {(Number(app.match_score) * 100).toFixed(0)}% match
                    </span>
                  ) : null}
                  <a href={`/jobs/${String(app.job_id)}`} className="text-xs text-primary hover:underline">
                    View Job →
                  </a>
                  <div className="flex flex-col gap-1">
                    <a
                      href={`http://localhost:8000/api/v1/applications/${String(app.id)}/status?status=submitted`}
                      target="_blank"
                      className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded hover:bg-blue-200"
                    >
                      Mark Submitted
                    </a>
                    <a
                      href={`http://localhost:8000/api/v1/applications/${String(app.id)}/status?status=interview`}
                      target="_blank"
                      className="text-[10px] bg-amber-100 text-amber-700 px-2 py-0.5 rounded hover:bg-amber-200"
                    >
                      Mark Interview
                    </a>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
