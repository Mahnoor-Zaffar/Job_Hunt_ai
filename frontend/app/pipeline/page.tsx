"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui";

const STAGE_LABELS: Record<string, { label: string; color: string }> = {
  discovered: { label: "Discovered", color: "text-gray-500 bg-gray-100 dark:bg-gray-800 dark:text-gray-400" },
  recommended: { label: "Recommended", color: "text-blue-600 bg-blue-50 dark:bg-blue-950 dark:text-blue-400" },
  resume_ready: { label: "Resume Ready", color: "text-violet-600 bg-violet-50 dark:bg-violet-950 dark:text-violet-400" },
  outreach_ready: { label: "Outreach Ready", color: "text-purple-600 bg-purple-50 dark:bg-purple-950 dark:text-purple-400" },
  queued: { label: "Queued", color: "text-indigo-600 bg-indigo-50 dark:bg-indigo-950 dark:text-indigo-400" },
  draft: { label: "Draft", color: "text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-400" },
  submitted: { label: "Submitted", color: "text-cyan-600 bg-cyan-50 dark:bg-cyan-950 dark:text-cyan-400" },
  under_review: { label: "Under Review", color: "text-amber-600 bg-amber-50 dark:bg-amber-950 dark:text-amber-400" },
  interview: { label: "Interview", color: "text-emerald-600 bg-emerald-50 dark:bg-emerald-950 dark:text-emerald-400" },
  offer: { label: "Offer", color: "text-green-600 bg-green-50 dark:bg-green-950 dark:text-green-400" },
  rejected: { label: "Rejected", color: "text-rose-600 bg-rose-50 dark:bg-rose-950 dark:text-rose-400" },
  withdrawn: { label: "Withdrawn", color: "text-gray-400 bg-gray-50 dark:bg-gray-900 dark:text-gray-500" },
};

const PIPELINE_DISPLAY = [
  "discovered", "recommended", "resume_ready", "outreach_ready",
  "queued", "draft", "submitted", "under_review", "interview", "offer",
];

const USER_ID = "00000000-0000-0000-0000-000000000001";

interface StageInfo {
  stage: string;
  count: number;
}

interface PipelineJob {
  app_id: string;
  job_id: string;
  stage: string;
  match_score: number | null;
  applied_at: string | null;
  interview_date: string | null;
  follow_up_at: string | null;
  notes: string | null;
  job: { title?: string; company?: string; location?: string };
}

export default function PipelinePage() {
  const [stages, setStages] = useState<StageInfo[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [jobs, setJobs] = useState<PipelineJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setSelectedStage(params.get("stage"));
  }, []);

  const fetchOverview = useCallback(async () => {
    const res = await fetch(`http://localhost:8000/api/v1/pipeline?user_id=${USER_ID}`);
    if (res.ok) {
      const data = await res.json();
      setStages(data.stages ?? []);
      setTotal(data.total ?? 0);
    }
  }, []);

  const fetchJobs = useCallback(async (stage: string | null) => {
    setLoading(true);
    let url = `http://localhost:8000/api/v1/pipeline/jobs?user_id=${USER_ID}`;
    if (stage) url += `&stage=${stage}`;
    const res = await fetch(url);
    if (res.ok) {
      setJobs(await res.json());
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchOverview(); }, [fetchOverview]);
  useEffect(() => { fetchJobs(selectedStage); }, [selectedStage, fetchJobs]);

  const stageMap: Record<string, number> = {};
  stages.forEach((s) => { stageMap[s.stage] = s.count; });

  const handleAdvance = async (appId: string, autoSubmit = false) => {
    setActionLoading(appId);
    const job = jobs.find((j) => j.app_id === appId);
    if (!job) return;
    const url = `http://localhost:8000/api/v1/pipeline/jobs/${job.job_id}/advance?user_id=${USER_ID}&auto_submit=${autoSubmit}`;
    await fetch(url, { method: "POST" });
    await fetchJobs(selectedStage);
    await fetchOverview();
    setActionLoading(null);
  };

  const handleGenerateOutreach = async (jobId: string) => {
    setActionLoading(jobId);
    await fetch(`http://localhost:8000/api/v1/outreach/generate?job_id=${jobId}&user_id=${USER_ID}`, {
      method: "POST",
    });
    setActionLoading(null);
    window.open("/outreach", "_blank");
  };

  const handleAutoApply = async (appId: string) => {
    setActionLoading(appId);
    await fetch(`http://localhost:8000/api/v1/applications/${appId}/auto-apply?user_id=${USER_ID}`, {
      method: "POST",
    });
    setActionLoading(null);
  };

  const canAdvance = (stage: string) => {
    return !["offer", "rejected", "withdrawn"].includes(stage);
  };

  const stageActions = (app: PipelineJob) => {
    const stage = app.stage;
    const isLast = stage === "offer" || stage === "rejected" || stage === "withdrawn";
    return (
      <div className="flex flex-wrap gap-2 mt-3">
        {canAdvance(stage) && (
          <button
            className="inline-flex items-center justify-center rounded-md text-xs font-medium ring-offset-background transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground px-3 py-1.5 disabled:opacity-50"
            disabled={actionLoading === app.app_id}
            onClick={() => handleAdvance(app.app_id, stage === "queued")}
          >
            {actionLoading === app.app_id ? "..." : "Advance →"}
          </button>
        )}
        {isLast && (
          <span className="text-xs text-muted-foreground italic">Terminal stage</span>
        )}
        {stage === "submitted" && (
          <button
            className="inline-flex items-center justify-center rounded-md text-xs font-medium ring-offset-background transition-colors border border-input bg-secondary hover:bg-secondary/80 px-3 py-1.5 disabled:opacity-50"
            disabled={actionLoading === app.job_id}
            onClick={() => handleAutoApply(app.app_id)}
          >
            Auto Apply
          </button>
        )}
        {stage === "outreach_ready" && (
          <button
            className="inline-flex items-center justify-center rounded-md text-xs font-medium ring-offset-background transition-colors border border-input bg-purple-100 hover:bg-purple-200 text-purple-700 px-3 py-1.5 disabled:opacity-50"
            disabled={actionLoading === app.job_id}
            onClick={() => handleGenerateOutreach(app.job_id)}
          >
            Generate Outreach
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Career Pipeline</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {total} jobs in pipeline
        </p>
      </div>

      <div className="grid grid-cols-5 gap-3">
        {PIPELINE_DISPLAY.slice(0, 5).map((stage) => {
          const info = STAGE_LABELS[stage] || { label: stage, color: "bg-secondary text-muted-foreground" };
          const count = stageMap[stage] || 0;
          return (
            <button key={stage} onClick={() => setSelectedStage(stage)}
              className="text-left"
            >
              <div className={`rounded-lg border bg-card p-4 text-center hover:bg-secondary/30 transition-colors ${count > 0 ? "border-l-2" : "opacity-60"} ${selectedStage === stage ? "ring-2 ring-primary" : ""}`}>
                <p className={`text-xs font-medium mb-1 ${STAGE_LABELS[stage]?.color?.split(" ")[0] || "text-muted-foreground"}`}>{info.label}</p>
                <p className="text-2xl font-semibold tracking-tight">{count}</p>
              </div>
            </button>
          );
        })}
      </div>
      <div className="grid grid-cols-5 gap-3">
        {PIPELINE_DISPLAY.slice(5).map((stage) => {
          const info = STAGE_LABELS[stage] || { label: stage, color: "bg-secondary text-muted-foreground" };
          const count = stageMap[stage] || 0;
          return (
            <button key={stage} onClick={() => setSelectedStage(stage)}
              className="text-left"
            >
              <div className={`rounded-lg border bg-card p-4 text-center hover:bg-secondary/30 transition-colors ${count > 0 ? "border-l-2" : "opacity-60"} ${selectedStage === stage ? "ring-2 ring-primary" : ""}`}>
                <p className={`text-xs font-medium mb-1 ${STAGE_LABELS[stage]?.color?.split(" ")[0] || "text-muted-foreground"}`}>{info.label}</p>
                <p className="text-2xl font-semibold tracking-tight">{count}</p>
              </div>
            </button>
          );
        })}
        <button onClick={() => setSelectedStage("rejected")}
          className="text-left"
        >
          <div className={`rounded-lg border bg-card p-4 text-center hover:bg-secondary/30 transition-colors ${stageMap.rejected > 0 ? "border-l-2 border-l-rose-500" : "opacity-60"} ${selectedStage === "rejected" ? "ring-2 ring-primary" : ""}`}>
            <p className="text-xs font-medium text-rose-500 mb-1">Rejected</p>
            <p className="text-2xl font-semibold tracking-tight">{stageMap.rejected || 0}</p>
          </div>
        </button>
        <button onClick={() => setSelectedStage("withdrawn")}
          className="text-left"
        >
          <div className={`rounded-lg border bg-card p-4 text-center hover:bg-secondary/30 transition-colors ${stageMap.withdrawn > 0 ? "border-l-2" : "opacity-60"} ${selectedStage === "withdrawn" ? "ring-2 ring-primary" : ""}`}>
            <p className="text-xs font-medium text-muted-foreground mb-1">Withdrawn</p>
            <p className="text-2xl font-semibold tracking-tight">{stageMap.withdrawn || 0}</p>
          </div>
        </button>
      </div>

      {selectedStage && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-medium">
              {STAGE_LABELS[selectedStage]?.label || selectedStage}
            </h2>
            <button onClick={() => setSelectedStage(null)} className="text-xs text-muted-foreground hover:text-foreground">
              Clear filter
            </button>
          </div>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading jobs...</p>
          ) : jobs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No jobs in this stage.</p>
          ) : (
            <div className="space-y-3">
              {jobs.map((app) => (
                <Card key={app.app_id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{app.job.title || "Unknown"}</p>
                      <p className="text-sm text-muted-foreground">
                        {app.job.company || ""}{app.job.company && app.job.location ? " · " : ""}{app.job.location || ""}
                      </p>
                    </div>
                    {app.match_score != null && (
                      <span className="inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium">{Math.round(app.match_score)}</span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STAGE_LABELS[app.stage]?.color || ""}`}>
                      {STAGE_LABELS[app.stage]?.label || app.stage}
                    </span>
                    {app.applied_at && <span className="text-xs text-muted-foreground">Applied {new Date(app.applied_at).toLocaleDateString()}</span>}
                    {app.follow_up_at && <span className="text-xs text-amber-600">Follow-up {new Date(app.follow_up_at).toLocaleDateString()}</span>}
                    {app.interview_date && <span className="text-xs text-emerald-600">Interview {new Date(app.interview_date).toLocaleDateString()}</span>}
                  </div>
                  {stageActions(app)}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
