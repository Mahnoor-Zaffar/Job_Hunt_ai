"use client";

import { useState } from "react";

export function AiAssistantPanel({ jobId }: { jobId: string }) {
  const [loading, setLoading] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function fetchAi(action: string, url: string) {
    setLoading(action);
    setError(null);
    setResults(null);
    try {
      const res = await fetch(url);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Request failed");
      }
      const data = await res.json();
      setResults({ action, data });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
    setLoading(null);
  }

  const isBusy = loading !== null;

  async function generateCV(jobId: string) {
    setLoading("cv");
    setError(null);
    setResults(null);

    // Load saved resume data from localStorage
    let resumeData: Record<string, unknown> = {};
    try {
      const saved = localStorage.getItem("parsedResume");
      if (saved) resumeData = JSON.parse(saved);
    } catch {}

    if (!resumeData.full_name && !resumeData.skills) {
      setError("Upload a resume first! Go to the Resume page, upload your CV, then come back.");
      setLoading(null);
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/api/v1/career/generate-cv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: String(resumeData.full_name || "Your Name"),
          email: String(resumeData.email || "you@example.com"),
          phone: String(resumeData.phone || ""),
          location: String(resumeData.location || ""),
          summary: String(resumeData.summary || "Experienced software engineer."),
          skills: (resumeData.skills as string[]) || [],
          experience: (resumeData.experience as Array<Record<string, unknown>>) || [],
          education: (resumeData.education as Array<Record<string, unknown>>) || [],
          certifications: (resumeData.certifications as string[]) || [],
          job_id: jobId,
        }),
      });
      if (!res.ok) throw new Error("Failed to generate CV");
      const data = await res.json();
      window.open(`http://localhost:8000${data.download_url}`, "_blank");
      setResults({ action: "cv", data: { message: "CV downloaded with your resume data!" } });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
    setLoading(null);
  }

  return (
    <div>
      <div className="flex gap-2 flex-wrap mb-4">
        <button
          disabled={isBusy}
          onClick={() => fetchAi("summary", `http://localhost:8000/api/v1/career/insights/job/${jobId}`)}
          className="px-3 py-1.5 text-xs border rounded hover:bg-muted transition-colors disabled:opacity-50"
        >
          🤖 AI Summary
        </button>
        <button
          disabled={isBusy}
          onClick={() => fetchAi("interview", `http://localhost:8000/api/v1/career/interview/prep/${jobId}`)}
          className="px-3 py-1.5 text-xs border rounded hover:bg-muted transition-colors disabled:opacity-50"
        >
          🎯 Interview Prep
        </button>
        <button
          disabled={isBusy}
          onClick={() => fetchAi("optimise", `http://localhost:8000/api/v1/career/resume/optimise?resume_text=Software+engineer+with+experience+in...&job_id=${jobId}`)}
          className="px-3 py-1.5 text-xs border rounded hover:bg-muted transition-colors disabled:opacity-50"
        >
          📝 Optimise Resume
        </button>
        <button
          disabled={isBusy}
          onClick={() => generateCV(jobId)}
          className="px-3 py-1.5 text-xs border rounded hover:bg-muted transition-colors disabled:opacity-50"
        >
          {loading === "cv" ? "⏳ Generating..." : "📄 Generate CV"}
        </button>
      </div>

      {loading && (
        <div className="mb-4 p-3 bg-muted/50 rounded border text-sm flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-muted-foreground">
            {loading === "summary" && "Generating job summary..."}
            {loading === "interview" && "Preparing interview questions (4 sections in parallel)..."}
            {loading === "optimise" && "Optimizing your resume..."}
          </span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950 border border-red-200 rounded text-sm text-red-700 mb-4">
          {error}
        </div>
      )}

      {results && (
        <div className="p-4 bg-muted/50 rounded border text-sm space-y-3 mb-4">
          {results.action === "summary" && (
            <div>
              <h4 className="font-semibold mb-2">AI Summary</h4>
              <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                {(results.data as { summary?: string[] }).summary?.map((s: string, i: number) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {results.action === "interview" && (
            <div>
              <h4 className="font-semibold mb-2">Interview Preparation</h4>
              {(["technical", "behavioral", "company_specific", "questions_to_ask"] as const).map((section) => {
                const items = (results.data as Record<string, Array<Record<string, string>>>)[section];
                if (!items?.length) return null;
                return (
                  <div key={section} className="mb-3">
                    <h5 className="text-xs font-medium uppercase text-muted-foreground mb-1">
                      {section.replace("_", " ")}
                    </h5>
                    {items.map((q: Record<string, string>, i: number) => (
                      <div key={i} className="ml-2 mb-2">
                        <p className="font-medium">Q: {q.question}</p>
                        {q.expected_answer && (
                          <p className="text-muted-foreground text-xs ml-2">A: {q.expected_answer}</p>
                        )}
                        {q.suggested_approach && (
                          <p className="text-muted-foreground text-xs ml-2">Approach: {q.suggested_approach}</p>
                        )}
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          )}

          {results.action === "optimise" && (
            <div>
              <h4 className="font-semibold mb-2">Optimised Resume</h4>
              <pre className="text-muted-foreground whitespace-pre-wrap text-xs leading-relaxed">
                {String((results.data as Record<string, string>).rewritten || (results.data as Record<string, string>).optimised_text || JSON.stringify(results.data, null, 2))}
              </pre>
            </div>
          )}

          <button
            onClick={() => { setResults(null); setError(null); }}
            className="text-xs text-muted-foreground hover:underline"
          >
            ✕ Clear
          </button>
        </div>
      )}
    </div>
  );
}
