"use client";

import { useState } from "react";

interface ClassifyResult {
  accepted: boolean;
  category: string | null;
  confidence: string;
  matched_title: string | null;
  matched_technologies: string[];
  reason: string;
}

export default function ClassifyPage() {
  const [title, setTitle] = useState("");
  const [skills, setSkills] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<ClassifyResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleClassify() {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/jobs/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          skills: skills ? skills.split(",").map((s) => s.trim()) : [],
          description: description || null,
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch {
      setResult({
        accepted: false,
        category: null,
        confidence: "low",
        matched_title: null,
        matched_technologies: [],
        reason: "API call failed",
      });
    } finally {
      setLoading(false);
    }
  }

  const examples = [
    { title: "Backend Engineer", skills: "python,fastapi,postgresql", desc: "Building REST APIs with FastAPI and PostgreSQL." },
    { title: "LLM Engineer", skills: "python,langchain,rag,gpt", desc: "Building RAG systems with LangChain and OpenAI." },
    { title: "Software Engineer", skills: "java,j2ee", desc: "Maintaining enterprise Java applications." },
    { title: "Sales Representative", skills: "", desc: "Selling our product to enterprise customers." },
    { title: "Senior Frontend Developer", skills: "react,typescript,tailwind", desc: "Building UI components with React and TypeScript." },
    { title: "Blockchain Developer", skills: "solidity,web3", desc: "Developing smart contracts on Ethereum." },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Job Classifier</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Test the rule-based classification engine. Enter a job and see how it gets classified.
        </p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {examples.map((ex) => (
          <button
            key={ex.title}
            onClick={() => { setTitle(ex.title); setSkills(ex.skills); setDescription(ex.desc); }}
            className="px-2.5 py-1 text-xs rounded-md bg-secondary text-muted-foreground hover:bg-secondary/70 transition-colors"
          >
            {ex.title}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Job Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Backend Engineer"
              className="w-full h-9 px-3 text-sm rounded-md border bg-transparent focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Skills (comma-separated)</label>
            <input
              type="text"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="e.g. python, fastapi, postgresql"
              className="w-full h-9 px-3 text-sm rounded-md border bg-transparent focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Job description..."
              rows={4}
              className="w-full px-3 py-2 text-sm rounded-md border bg-transparent focus:outline-none focus:ring-2 focus:ring-ring resize-none"
            />
          </div>
          <button
            onClick={handleClassify}
            disabled={loading || !title}
            className="h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {loading ? "Classifying..." : "Classify"}
          </button>
        </div>

        <div>
          {result && (
            <div className={`rounded-lg border p-4 ${result.accepted ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20" : "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20"}`}>
              <div className="flex items-center gap-3 mb-3">
                <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${result.accepted ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"}`}>
                  {result.accepted ? "ACCEPTED" : "REJECTED"}
                </span>
                <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${
                  result.confidence === "high" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" :
                  result.confidence === "medium" ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300" :
                  "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
                }`}>
                  {result.confidence.toUpperCase()}
                </span>
              </div>

              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-muted-foreground text-xs">Category:</span>
                  <span className="ml-2 font-medium">{result.category || "N/A"}</span>
                </div>
                {result.matched_title && (
                  <div>
                    <span className="text-muted-foreground text-xs">Matched Title:</span>
                    <span className="ml-2">{result.matched_title}</span>
                  </div>
                )}
                {result.matched_technologies.length > 0 && (
                  <div>
                    <span className="text-muted-foreground text-xs">Matched Tech:</span>
                    <div className="flex gap-1 flex-wrap mt-1">
                      {result.matched_technologies.map((t) => (
                        <span key={t} className="text-[10px] bg-secondary px-1.5 py-0.5 rounded">{t}</span>
                      ))}
                    </div>
                  </div>
                )}
                <div className="pt-2 border-t mt-2">
                  <span className="text-muted-foreground text-xs block mb-1">Reason:</span>
                  <p className="text-xs">{result.reason}</p>
                </div>
              </div>
            </div>
          )}

          {!result && (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <p className="text-sm text-muted-foreground">Enter a job title and click Classify to see the result.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
