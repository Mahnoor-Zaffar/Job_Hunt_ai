"use client";

import { useState } from "react";

export default function ResumePage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [parsed, setParsed] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true); setError(null); setParsed(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("http://localhost:8000/api/v1/resumes/parse", { method: "POST", body: formData });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || "Parse failed"); }
      const data = await res.json();
      setParsed(data);
      localStorage.setItem("parsedResume", JSON.stringify(data));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    }
    setUploading(false);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Resume</h1>
        <p className="text-sm text-muted-foreground mt-1">Upload your resume to extract skills, experience, and education</p>
      </div>

      {!parsed ? (
        <div className="max-w-lg">
          <div className="rounded-lg border bg-card p-6">
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Resume file</label>
                <p className="text-xs text-muted-foreground mb-2">PDF, DOCX, or TXT (max 10MB)</p>
                <input type="file" accept=".pdf,.docx,.doc,.txt" onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full text-sm file:mr-4 file:py-2 file:px-4 file:text-xs file:font-medium file:border-0 file:rounded-md file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 file:transition-colors" />
                {file && <p className="text-xs text-muted-foreground mt-2">{file.name} ({(file.size / 1024).toFixed(0)} KB)</p>}
              </div>
              {error && <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">{error}</p>}
              <button type="submit" disabled={!file || uploading}
                className="h-9 px-4 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 transition-colors">
                {uploading ? "Uploading..." : "Upload & Parse"}
              </button>
            </form>
          </div>

          <div className="mt-4 rounded-lg border bg-card p-5">
            <h3 className="text-sm font-medium mb-2">Supported formats</h3>
            <div className="space-y-1 text-xs text-muted-foreground">
              <p>PDF (.pdf) — extracts text from all pages</p>
              <p>Word (.docx, .doc) — extracts paragraphs</p>
              <p>Plain Text (.txt) — reads directly</p>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <button onClick={() => { setParsed(null); setFile(null); }} className="text-xs text-muted-foreground hover:text-foreground transition-colors mb-4">
            ← Upload another
          </button>

          <div className="grid grid-cols-2 gap-6">
            <div className="rounded-lg border bg-card p-5 space-y-4">
              <h3 className="text-sm font-medium">Personal Info</h3>
              <div className="space-y-2 text-sm">
                {!!parsed.full_name && <p><span className="text-muted-foreground">Name</span> <span className="font-medium ml-2">{String(parsed.full_name)}</span></p>}
                {!!parsed.email && <p><span className="text-muted-foreground">Email</span> <span className="font-medium ml-2">{String(parsed.email)}</span></p>}
                {!!parsed.phone && <p><span className="text-muted-foreground">Phone</span> <span className="font-medium ml-2">{String(parsed.phone)}</span></p>}
                {!!parsed.location && <p><span className="text-muted-foreground">Location</span> <span className="font-medium ml-2">{String(parsed.location)}</span></p>}
                {!!parsed.total_experience_years && <p><span className="text-muted-foreground">Experience</span> <span className="font-medium ml-2">{String(parsed.total_experience_years)} years</span></p>}
              </div>
            </div>

            <div className="rounded-lg border bg-card p-5 space-y-4">
              <h3 className="text-sm font-medium">Skills</h3>
              <div className="flex gap-1.5 flex-wrap">
                {(parsed.skills as string[])?.map((s) => (
                  <span key={s} className="text-xs bg-secondary px-2 py-1 rounded-md">{s}</span>
                ))}
              </div>
            </div>

            {(parsed.experience as Array<Record<string, unknown>>)?.length > 0 && (
              <div className="rounded-lg border bg-card p-5 space-y-3 col-span-2">
                <h3 className="text-sm font-medium">Experience</h3>
                {(parsed.experience as Array<Record<string, unknown>>).map((e, i) => (
                  <div key={i} className="flex justify-between text-sm border-b last:border-0 pb-2 last:pb-0">
                    <div>
                      <p className="font-medium">{String(e.title)}</p>
                      <p className="text-xs text-muted-foreground">{String(e.company)}</p>
                    </div>
                    <span className="text-xs text-muted-foreground">{String(e.start_date)} — {String(e.end_date)}</span>
                  </div>
                ))}
              </div>
            )}

            {(parsed.education as Array<Record<string, unknown>>)?.length > 0 && (
              <div className="rounded-lg border bg-card p-5 space-y-3 col-span-2">
                <h3 className="text-sm font-medium">Education</h3>
                {(parsed.education as Array<Record<string, unknown>>).map((e, i) => (
                  <div key={i} className="flex justify-between text-sm border-b last:border-0 pb-2 last:pb-0">
                    <div>
                      <p className="font-medium">{String(e.degree)}{e.field ? ` in ${String(e.field)}` : ""}</p>
                      <p className="text-xs text-muted-foreground">{String(e.school)}</p>
                    </div>
                    <span className="text-xs text-muted-foreground">{String(e.year)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
