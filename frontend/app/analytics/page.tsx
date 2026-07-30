"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
import { api, type DashboardStats } from "@/lib/api";

export default function AnalyticsPage() {
  const [data, setData] = useState<DashboardStats | null>(null);

  useEffect(() => {
    api.analytics.dashboard().then(setData).catch(() => {});
  }, []);

  if (!data) return <div className="text-sm text-muted-foreground">Loading analytics...</div>;

  const s = data.stats;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">Pipeline performance and job market overview</p>
      </div>

      <div className="grid grid-cols-5 gap-3">
        <div className="rounded-lg border bg-card p-4 text-center">
          <p className="text-xs font-medium text-muted-foreground mb-1">Active Jobs</p>
          <p className="text-2xl font-semibold">{s.active_jobs}</p>
        </div>
        <div className="rounded-lg border bg-card p-4 text-center">
          <p className="text-xs font-medium text-muted-foreground mb-1">Applied</p>
          <p className="text-2xl font-semibold">{s.applications_submitted}</p>
        </div>
        <div className="rounded-lg border bg-card p-4 text-center">
          <p className="text-xs font-medium text-muted-foreground mb-1">Interviews</p>
          <p className="text-2xl font-semibold">{s.interviews_scheduled}</p>
        </div>
        <div className="rounded-lg border bg-card p-4 text-center">
          <p className="text-xs font-medium text-muted-foreground mb-1">Offers</p>
          <p className="text-2xl font-semibold">{s.offers_received}</p>
        </div>
        <div className="rounded-lg border bg-card p-4 text-center">
          <p className="text-xs font-medium text-muted-foreground mb-1">Total Jobs</p>
          <p className="text-2xl font-semibold">{s.total_jobs}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card title="Top Technologies">
          <div className="space-y-2">
            {(data.top_technologies || []).slice(0, 10).map((t) => (
              <div key={t.name} className="flex items-center justify-between text-sm">
                <span>{t.name}</span>
                <span className="text-muted-foreground">{t.count}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Jobs by Source">
          <div className="space-y-2">
            {data.jobs_by_source.map((s) => (
              <div key={s.source} className="flex items-center justify-between text-sm">
                <span>{s.source}</span>
                <span className="text-muted-foreground">{s.count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="Pipeline Breakdown">
        {data.applications_by_status.length === 0 ? (
          <p className="text-sm text-muted-foreground">No applications in pipeline yet.</p>
        ) : (
          <div className="space-y-2">
            {data.applications_by_status.map((a) => (
              <div key={a.status} className="flex items-center justify-between text-sm">
                <span className="capitalize">{a.status.replace(/_/g, " ")}</span>
                <span className="text-muted-foreground">{a.count}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
