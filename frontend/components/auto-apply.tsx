"use client";

import { useState, useEffect, useCallback } from "react";

const USER_ID = "00000000-0000-0000-0000-000000000001";

interface AutoApplyStatus {
  status: string; // pending, running, success, failed, not_found
  step?: string | null;
  message?: string | null;
  error?: string | null;
  filled_fields?: number | null;
}

export function AutoApplyButton({ jobId }: { jobId: string }) {
  const [state, setState] = useState<"idle" | "creating" | "polling" | "success" | "error">("idle");
  const [status, setStatus] = useState<AutoApplyStatus | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const pollStatus = useCallback(async (appId: string) => {
    try {
      const res = await fetch(
        `http://localhost:8000/api/v1/applications/${appId}/auto-apply/status`
      );
      if (!res.ok) return;
      const data: AutoApplyStatus = await res.json();
      setStatus(data);

      if (data.status === "success") {
        setState("success");
        return;
      }
      if (data.status === "failed" || data.status === "not_found") {
        setState("error");
        return;
      }
      setTimeout(() => pollStatus(appId), 2000);
    } catch {
      setState("error");
    }
  }, []);

  async function handleClick() {
    if (state !== "idle") return;

    setState("creating");
    setModalOpen(true);

    try {
      // Step 1: create application
      const appRes = await fetch(
        `http://localhost:8000/api/v1/applications?user_id=${USER_ID}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ job_id: jobId }),
        }
      );
      if (!appRes.ok) { setState("error"); return; }
      const app = await appRes.json();

      // Step 2: start auto-apply
      const aaRes = await fetch(
        `http://localhost:8000/api/v1/applications/${app.id}/auto-apply?user_id=${USER_ID}`,
        { method: "POST" }
      );
      if (!aaRes.ok) { setState("error"); return; }

      setState("polling");
      pollStatus(app.id);
    } catch {
      setState("error");
    }
  }

  function reset() {
    setState("idle");
    setStatus(null);
    setModalOpen(false);
  }

  const steps = [
    { key: "initializing", label: "Preparing" },
    { key: "fetching", label: "Loading job details" },
    { key: "launching", label: "Launching browser" },
    { key: "running", label: "Filling application form" },
    { key: "saving", label: "Saving result" },
  ];

  const currentStep = status?.step || "";

  return (
    <>
      <button
        onClick={handleClick}
        disabled={state === "creating" || state === "polling" || state === "success"}
        className={`px-3 py-1 text-xs rounded font-medium transition-colors ${
          state === "success"
            ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
            : state === "error"
            ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
            : "bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        }`}
      >
        {state === "success" ? "✓ Applied" : state === "error" ? "Failed" : state === "creating" ? "..." : "Auto Apply"}
      </button>

      {modalOpen && (state === "creating" || state === "polling") && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={reset}>
          <div className="bg-background rounded-xl border shadow-xl w-full max-w-md mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-sm font-semibold mb-4">Auto-Applying...</h3>
            <div className="space-y-3">
              {steps.map((s) => {
                const isActive = currentStep.startsWith(s.key);
                const isDone = !isActive && state !== "polling";
                return (
                  <div key={s.key} className="flex items-center gap-3 text-sm">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium ${
                      isActive ? "bg-primary text-primary-foreground animate-pulse" : isDone ? "bg-green-100 text-green-700" : "bg-secondary text-muted-foreground"
                    }`}>
                      {isActive ? "..." : isDone ? "✓" : "○"}
                    </span>
                    <span className={isActive ? "text-foreground font-medium" : "text-muted-foreground"}>{s.label}</span>
                  </div>
                );
              })}
            </div>
            {status?.filled_fields != null && (
              <p className="mt-3 text-xs text-muted-foreground">Fields filled: {status.filled_fields}</p>
            )}
            <button onClick={reset} className="mt-4 text-xs text-muted-foreground hover:text-foreground">Close</button>
          </div>
        </div>
      )}

      {modalOpen && (state === "error" || state === "success") && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={reset}>
          <div className="bg-background rounded-xl border shadow-xl w-full max-w-md mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className={`text-sm font-semibold mb-2 ${state === "success" ? "text-green-600" : "text-red-600"}`}>
              {state === "success" ? "Application Submitted!" : "Auto-Apply Failed"}
            </h3>
            <p className="text-sm text-muted-foreground">
              {state === "success"
                ? status?.message || "Your application was submitted successfully."
                : status?.error || status?.message || "Could not complete auto-apply."}
            </p>
            <button onClick={reset} className="mt-4 px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
              Done
            </button>
          </div>
        </div>
      )}
    </>
  );
}
