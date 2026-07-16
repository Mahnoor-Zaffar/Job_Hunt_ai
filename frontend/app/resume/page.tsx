"use client";

import { useState } from "react";
import { Card } from "@/components/ui";

export default function ResumePage() {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !name.trim()) {
      setError("Please provide a name and select a file.");
      return;
    }
    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const text = await file.text();
      // Send to backend resume creation API
      const userId = "00000000-0000-0000-0000-000000000001";
      const res = await fetch(
        `http://localhost:8000/api/v1/resumes?user_id=${userId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name,
            file_path: `/uploads/${file.name}`,
            file_type: file.name.split(".").pop() || "txt",
            parsed_text: text.slice(0, 5000),
          }),
        }
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }

      const data = await res.json();
      setResult(`Resume uploaded! ID: ${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    }
    setUploading(false);
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Resume Manager</h1>

      <div className="max-w-xl">
        <Card title="Upload Resume">
          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <label className="text-sm font-medium block mb-1">Resume Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Software Engineer Resume"
                className="w-full px-3 py-2 text-sm border rounded bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <div>
              <label className="text-sm font-medium block mb-1">File (PDF, DOCX, TXT)</label>
              <input
                type="file"
                accept=".pdf,.docx,.doc,.txt"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-sm file:mr-3 file:py-1.5 file:px-3 file:text-xs file:border file:rounded file:bg-muted hover:file:bg-muted/70"
              />
              {file && (
                <p className="text-xs text-muted-foreground mt-1">
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 dark:bg-red-950 px-3 py-2 rounded">{error}</p>
            )}
            {result && (
              <p className="text-sm text-green-600 bg-green-50 dark:bg-green-950 px-3 py-2 rounded">{result}</p>
            )}

            <button
              type="submit"
              disabled={uploading}
              className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {uploading ? "Uploading..." : "Upload Resume"}
            </button>
          </form>
        </Card>

        <Card title="Supported Formats" className="mt-4">
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>✅ PDF (.pdf) — Max 10MB</li>
            <li>✅ Word (.docx, .doc) — Max 10MB</li>
            <li>✅ Plain Text (.txt) — Max 10MB</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
