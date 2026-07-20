"use client";

import { useState } from "react";

interface EmailResult {
  email: string;
  priority: number;
  priority_label: string;
  source: string;
}

interface GeneratedEmail {
  subject: string;
  body: string;
}

export function EmailHRButton({ jobId }: { jobId: string }) {
  const [loading, setLoading] = useState(false);
  const [emails, setEmails] = useState<EmailResult[] | null>(null);
  const [generated, setGenerated] = useState<GeneratedEmail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleClick() {
    setLoading(true); setError(null); setEmails(null); setGenerated(null); setCopied(false);
    try {
      const res = await fetch("http://localhost:8000/api/v1/career/email-hr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, candidate_name: "[Your Name]", candidate_email: "[Your Email]", candidate_phone: "[Your Phone]" }),
      });
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setEmails(data.emails_found || []);
      setGenerated(data.generated_email);
    } catch (e) { setError("Failed to find emails"); }
    setLoading(false);
  }

  async function copyToClipboard() {
    if (!generated) return;
    const text = `Subject: ${generated.subject}\n\n${generated.body}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        Searching for HR contacts...
      </div>
    );
  }

  if (emails && generated) {
    return (
      <div className="space-y-3 text-xs">
        <div>
          <h4 className="font-semibold mb-1">Found emails:</h4>
          {emails.map((e, i) => (
            <div key={i} className="flex items-center gap-2 text-muted-foreground">
              <span className={`w-1.5 h-1.5 rounded-full ${e.priority <= 2 ? "bg-emerald-500" : e.priority === 3 ? "bg-amber-500" : "bg-gray-400"}`} />
              <span>{e.email}</span>
              <span className="text-[10px] bg-secondary px-1 rounded">{e.priority_label}</span>
            </div>
          ))}
        </div>

        <div className="border-t pt-3">
          <h4 className="font-semibold mb-1">Generated Email:</h4>
          <p className="font-medium text-muted-foreground">{generated.subject}</p>
          <pre className="text-muted-foreground whitespace-pre-wrap mt-1 leading-relaxed">{generated.body}</pre>
          <div className="flex gap-2 mt-2">
            <button onClick={copyToClipboard} className="px-3 py-1 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
              {copied ? "✓ Copied" : "📋 Copy to Clipboard"}
            </button>
            <button onClick={() => { setEmails(null); setGenerated(null); }} className="px-3 py-1 text-xs border rounded-md hover:bg-secondary transition-colors">
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <button onClick={handleClick} className="px-3 py-1.5 text-xs border rounded-md hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground">
        📧 Email HR
      </button>
      {error && <p className="text-xs text-destructive mt-1">{error}</p>}
    </div>
  );
}
