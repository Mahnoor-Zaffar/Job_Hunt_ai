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

async function getPipeline() {
  try {
    const res = await fetch("http://localhost:8000/api/v1/pipeline?user_id=00000000-0000-0000-0000-000000000001", { next: { revalidate: 15 } });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

export default async function PipelinePage() {
  const data = await getPipeline();
  const stageMap: Record<string, number> = {};
  data?.stages?.forEach((s: { stage: string; count: number }) => { stageMap[s.stage] = s.count; });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Career Pipeline</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {data ? `${data.total} jobs in pipeline` : "Loading..."}
        </p>
      </div>

      <div className="grid grid-cols-5 gap-3">
        {PIPELINE_DISPLAY.slice(0, 5).map((stage) => {
          const info = STAGE_LABELS[stage] || { label: stage, color: "bg-secondary text-muted-foreground" };
          const count = stageMap[stage] || 0;
          return (
            <a key={stage} href={`/pipeline?stage=${stage}`}>
              <div className={`rounded-lg border bg-card p-4 text-center hover:bg-secondary/30 transition-colors ${count > 0 ? "border-l-2" : "opacity-60"}`}>
                <p className={`text-xs font-medium mb-1 ${STAGE_LABELS[stage]?.color.split(" ")[0] || "text-muted-foreground"}`}>{info.label}</p>
                <p className="text-2xl font-semibold tracking-tight">{count}</p>
              </div>
            </a>
          );
        })}
      </div>
      <div className="grid grid-cols-5 gap-3">
        {PIPELINE_DISPLAY.slice(5).map((stage) => {
          const info = STAGE_LABELS[stage] || { label: stage, color: "bg-secondary text-muted-foreground" };
          const count = stageMap[stage] || 0;
          return (
            <a key={stage} href={`/pipeline?stage=${stage}`}>
              <div className={`rounded-lg border bg-card p-4 text-center hover:bg-secondary/30 transition-colors ${count > 0 ? "border-l-2" : "opacity-60"}`}>
                <p className={`text-xs font-medium mb-1 ${STAGE_LABELS[stage]?.color.split(" ")[0] || "text-muted-foreground"}`}>{info.label}</p>
                <p className="text-2xl font-semibold tracking-tight">{count}</p>
              </div>
            </a>
          );
        })}
        <a href="/pipeline?stage=rejected">
          <div className={`rounded-lg border bg-card p-4 text-center hover:bg-secondary/30 transition-colors ${(stageMap.rejected || 0) > 0 ? "border-l-2 border-l-rose-500" : "opacity-60"}`}>
            <p className="text-xs font-medium text-rose-500 mb-1">Rejected</p>
            <p className="text-2xl font-semibold tracking-tight">{stageMap.rejected || 0}</p>
          </div>
        </a>
        <a href="/pipeline?stage=withdrawn">
          <div className={`rounded-lg border bg-card p-4 text-center hover:bg-secondary/30 transition-colors ${(stageMap.withdrawn || 0) > 0 ? "border-l-2" : "opacity-60"}`}>
            <p className="text-xs font-medium text-muted-foreground mb-1">Withdrawn</p>
            <p className="text-2xl font-semibold tracking-tight">{stageMap.withdrawn || 0}</p>
          </div>
        </a>
      </div>
    </div>
  );
}
