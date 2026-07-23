"use client";

import { useEffect, useState } from "react";

interface Company {
  name: string; website: string; city: string; tier: string;
  hiring: boolean; remote: boolean; scanned: boolean;
  industry: string; size: string; linkedin: string; category: string;
  emails: {
    email: string; priority: number; label: string;
    confidence?: number; confidence_label?: string; detail?: string; source?: string;
  }[];
  email_keywords: { suggested_subject?: string };
  hiring_roles?: string[];
}

type PipelineStatus = "not_contacted" | "contacted" | "replied" | "interviewing" | "no_response";

interface PipelineEntry {
  status: PipelineStatus;
  contacted_at: string | null;
  notes: string;
}

const PIPELINE_LABELS: Record<PipelineStatus, string> = {
  not_contacted: "Not Contacted",
  contacted: "Contacted",
  replied: "Replied",
  interviewing: "Interviewing",
  no_response: "No Response",
};

const PIPELINE_COLORS: Record<PipelineStatus, string> = {
  not_contacted: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  contacted: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  replied: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  interviewing: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  no_response: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
};

const PIPELINE_ICONS: Record<PipelineStatus, string> = {
  not_contacted: "📌",
  contacted: "✉️",
  replied: "📬",
  interviewing: "🎯",
  no_response: "❌",
};

const INDUSTRY_COLORS: Record<string, string> = {
  "Software Development": "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300",
  "IT Services": "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300",
  "BPO": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  "Software": "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300",
  "BPO/Software": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  "Fintech": "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  "QA/Software": "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
};

const IT_EMAIL_TEMPLATE = `Hi [Hiring Manager/Team],

I'm a full-stack / backend developer based in Pakistan with experience in Python, JavaScript, React, Node.js, Docker, and cloud infrastructure.

I understand that [Company] works on [services — staff augmentation / product development / digital transformation]. Finding developers who can deliver quality code and communicate effectively across timezones is a real challenge. I bring strong technical skills, professional communication, and the ability to integrate quickly into existing workflows.

I've attached my resume for your review. I'd love to schedule a brief call to discuss how I can contribute to your team and your clients.

Best regards,
[Your Name]
[Your Email]
[Your Phone]`;

const STORAGE_KEY = "it_company_pipeline";

function loadPipeline(): Record<string, PipelineEntry> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function savePipeline(p: Record<string, PipelineEntry>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
}

function hasAgo(days: number, dateStr: string | null): boolean {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  return (Date.now() - d.getTime()) > days * 86400000;
}

function normalizeCompany(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]/g, "");
}

const ROLE_PATTERNS: { label: string; regex: RegExp }[] = [
  { label: "Frontend", regex: /front(\s|-)?end|frontend/i },
  { label: "Backend", regex: /back(\s|-)?end|backend/i },
  { label: "Full Stack", regex: /full\s*stack|fullstack/i },
  { label: "Web Developer", regex: /web\s*developer|web\s*engineer/i },
];

export function ItCompaniesFinder() {
  const [loading, setLoading] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [verifyTaskId, setVerifyTaskId] = useState<string | null>(null);
  const [verifyProgress, setVerifyProgress] = useState<{current: number; total: number} | null>(null);
  const [cityFilter, setCityFilter] = useState<string>("all");
  const [industryFilter, setIndustryFilter] = useState<string>("all");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [showEmailBody, setShowEmailBody] = useState(false);
  const [pipeline, setPipeline] = useState<Record<string, PipelineEntry>>({});
  const [personalizing, setPersonalizing] = useState<number | null>(null);
  const [personalizedEmails, setPersonalizedEmails] = useState<Record<string, {subject: string; body: string}>>({});
  const [jobCounts, setJobCounts] = useState<Record<string, number>>({});
  const [companyRoles, setCompanyRoles] = useState<Record<string, string[]>>({});
  const [modal, setModal] = useState<{company: Company; idx: number} | null>(null);
  const [copyEmailText, setCopyEmailText] = useState<number | null>(null);

  useEffect(() => {
    setPipeline(loadPipeline());
  }, []);

  // Fetch jobs for hiring detection
  useEffect(() => {
    if (companies.length === 0) return;
    fetch("http://localhost:8000/api/v1/jobs?per_page=500&status=active")
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (!data || !data.jobs) return;
        const counts: Record<string, number> = {};
        const roles: Record<string, string[]> = {};
        for (const job of data.jobs) {
          const key = normalizeCompany(job.company || "");
          if (key) {
            counts[key] = (counts[key] || 0) + 1;
            for (const rp of ROLE_PATTERNS) {
              if (rp.regex.test(job.title || "")) {
                if (!roles[key]) roles[key] = [];
                if (!roles[key].includes(rp.label)) roles[key].push(rp.label);
              }
            }
          }
        }
        setJobCounts(counts);
        setCompanyRoles(roles);
      })
      .catch(() => {});
  }, [companies]);

  async function run() {
    setLoading(true); setCompanies([]); setStats(null);
    setVerifyTaskId(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/career/it-companies", { method: "POST" });
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setCompanies(data.companies || []);
      setStats(data.stats || null);
    } catch (e: unknown) {
      alert("Error loading IT companies: " + (e instanceof Error ? e.message : String(e)));
    } finally {
      setLoading(false);
    }
  }

  async function startVerify() {
    setVerifyTaskId("pending");
    try {
      const res = await fetch("http://localhost:8000/api/v1/career/it-companies/verify", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ companies }),
      });
      if (!res.ok) throw new Error("Verify failed");
      const data = await res.json();
      setVerifyTaskId(data.task_id);
      setVerifyProgress({ current: 0, total: data.total });
    } catch {
      setVerifyTaskId(null);
      alert("Failed to start verification");
    }
  }

  // Poll verify progress
  useEffect(() => {
    if (!verifyTaskId || verifyTaskId === "pending") return;
    const id = setInterval(async () => {
      try {
        const r = await fetch(`http://localhost:8000/api/v1/career/it-companies/verify/${verifyTaskId}`);
        if (!r.ok) { clearInterval(id); setVerifyTaskId(null); return; }
        const data = await r.json();
        setVerifyProgress({ current: data.progress, total: data.total });
        if (data.status === "completed" || data.status === "error") {
          setCompanies(data.companies || []);
          setVerifyProgress(null);
          setVerifyTaskId(null);
        }
      } catch { clearInterval(id); setVerifyTaskId(null); }
    }, 3000);
    return () => clearInterval(id);
  }, [verifyTaskId]);

  function updatePipeline(name: string, status: PipelineStatus) {
    const next = { ...pipeline };
    const existing = next[name];
    if (status === "contacted" && (!existing || existing.status !== "contacted")) {
      next[name] = { status, contacted_at: new Date().toISOString(), notes: existing?.notes || "" };
    } else {
      next[name] = { status, contacted_at: existing?.contacted_at || null, notes: existing?.notes || "" };
    }
    setPipeline(next);
    savePipeline(next);
  }

  function copyEmail(email: string, idx: number) {
    navigator.clipboard.writeText(email);
    setCopiedIdx(idx); setTimeout(() => setCopiedIdx(null), 1500);
  }

  function copyAllEmails() {
    const all = filtered.map((c) => c.emails[0]?.email).filter(Boolean).join(", ");
    navigator.clipboard.writeText(all);
    setCopiedAll(true); setTimeout(() => setCopiedAll(false), 1500);
  }

  function copyEmailTemplate() {
    navigator.clipboard.writeText(IT_EMAIL_TEMPLATE);
  }

  function copyPersonalizedText(text: string, idx: number) {
    navigator.clipboard.writeText(text);
    setCopyEmailText(idx); setTimeout(() => setCopyEmailText(null), 1500);
  }

  async function personalizeEmail(c: Company, idx: number) {
    if (personalizedEmails[c.name]) {
      setModal({ company: c, idx });
      return;
    }
    setPersonalizing(idx);
    try {
      const r = await fetch("http://localhost:8000/api/v1/career/it-company-email/personalize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: c.name,
          industry: c.industry,
          city: c.city,
          size: c.size,
          role: roleFilter !== "all" ? roleFilter : "Full-Stack Developer",
          remote: "Remote",
          company_tier: c.industry,
        }),
      });
      if (!r.ok) throw new Error("AI personalization failed");
      const d = await r.json();
      setPersonalizedEmails((prev) => ({ ...prev, [c.name]: { subject: d.subject, body: d.body } }));
      setModal({ company: c, idx });
    } catch {
      setPersonalizedEmails((prev) => ({
        ...prev,
        [c.name]: { subject: "Error", body: "Could not generate. Check your API key." },
      }));
      setModal({ company: c, idx });
    }
    setPersonalizing(null);
  }

  const cities = [...new Set(companies.map((c) => c.city))].filter(Boolean).sort();
  const industries = [...new Set(companies.map((c) => c.industry))].filter(Boolean).sort();
  const hasEmails = companies.filter((c) => c.emails.length > 0).length;

  const pipelineStats = (() => {
    const counts: Record<string, number> = {};
    for (const s of Object.values(PIPELINE_LABELS)) counts[s] = 0;
    for (const c of companies) {
      const entry = pipeline[c.name];
      const label = entry ? PIPELINE_LABELS[entry.status] : "Not Contacted";
      counts[label] = (counts[label] || 0) + 1;
    }
    return counts;
  })();

  let filtered = [...companies];
  if (cityFilter !== "all") filtered = filtered.filter((c) => c.city === cityFilter);
  if (industryFilter !== "all") filtered = filtered.filter((c) => c.industry === industryFilter);
  if (roleFilter !== "all") {
    filtered = filtered.filter((c) => {
      const roles = companyRoles[normalizeCompany(c.name)] || [];
      return roles.includes(roleFilter);
    });
  }
  if (statusFilter !== "all") {
    filtered = filtered.filter((c) => (pipeline[c.name]?.status || "not_contacted") === statusFilter);
  }

  filtered.sort((a, b) => {
    const aRoles = (companyRoles[normalizeCompany(a.name)] || []).length;
    const bRoles = (companyRoles[normalizeCompany(b.name)] || []).length;
    if (aRoles !== bRoles) return bRoles - aRoles;
    return a.name.localeCompare(b.name);
  });

  return (
    <div className="space-y-4">
      <button
        onClick={run}
        disabled={loading}
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {loading ? (
          <><span className="w-3.5 h-3.5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" /> Loading...</>
        ) : (
          <>Load IT Companies</>
        )}
      </button>

      {loading && <p className="text-xs text-muted-foreground">Loading companies and guessing HR emails...</p>}
      {verifyProgress && <p className="text-xs text-amber-600 dark:text-amber-400">Verifying emails in background: {verifyProgress.current}/{verifyProgress.total} companies checked</p>}

      {stats && companies.length > 0 && (
        <>
          {/* Pipeline stats bar */}
          {Object.entries(pipelineStats).filter(([_, v]) => v > 0).length > 0 && (
            <div className="flex gap-3 flex-wrap text-xs">
              {Object.entries(PIPELINE_LABELS).map(([key, label]) => {
                const count = pipelineStats[label] || 0;
                if (count === 0) return null;
                return (
                  <span key={key} className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${PIPELINE_COLORS[key as PipelineStatus]}`}>
                    {PIPELINE_ICONS[key as PipelineStatus]} {label}: {count}
                  </span>
                );
              })}
            </div>
          )}

          <div className="flex gap-2 flex-wrap">
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="text-xs bg-secondary px-2.5 py-1 rounded-md border-0">
              <option value="all">All Statuses</option>
              {(Object.entries(PIPELINE_LABELS) as [PipelineStatus, string][]).map(([key, label]) => (
                <option key={key} value={key}>{PIPELINE_ICONS[key]} {label}</option>
              ))}
            </select>

            <select value={cityFilter} onChange={(e) => setCityFilter(e.target.value)} className="text-xs bg-secondary px-2.5 py-1 rounded-md border-0">
              <option value="all">All Cities</option>
              {cities.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>

            <select value={industryFilter} onChange={(e) => setIndustryFilter(e.target.value)} className="text-xs bg-secondary px-2.5 py-1 rounded-md border-0">
              <option value="all">All Industries</option>
              {industries.map((i) => <option key={i} value={i}>{i}</option>)}
            </select>

            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="text-xs bg-secondary px-2.5 py-1 rounded-md border-0">
              <option value="all">All Roles</option>
              <option value="Frontend">Frontend</option>
              <option value="Backend">Backend</option>
              <option value="Full Stack">Full Stack</option>
              <option value="Web Developer">Web Developer</option>
            </select>

            <button onClick={copyAllEmails} className="text-xs px-2.5 py-1 rounded-md bg-secondary hover:bg-secondary/70 transition-colors">
              {copiedAll ? "✓ Copied" : `Copy All (${hasEmails})`}
            </button>

            <button onClick={() => setShowEmailBody(!showEmailBody)} className="text-xs px-2.5 py-1 rounded-md bg-secondary hover:bg-secondary/70 transition-colors">
              Email Template
            </button>
          </div>

          {showEmailBody && (
            <div className="rounded-lg border bg-card p-4 space-y-2">
              <h4 className="text-sm font-medium">Email Template (copy + personalize)</h4>
              <pre className="text-xs text-muted-foreground bg-secondary p-3 rounded-md whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">{IT_EMAIL_TEMPLATE}</pre>
              <button onClick={copyEmailTemplate} className="text-xs px-3 py-1 bg-primary text-primary-foreground rounded-md">Copy Template</button>
            </div>
          )}

          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Showing {filtered.length} of {companies.length} companies · {hasEmails} have HR emails
              {verifyProgress ? (
                <> · <span className="text-amber-600 dark:text-amber-400">Verifying: {verifyProgress.current}/{verifyProgress.total}</span></>
              ) : stats?.verified ? (
                <> · <span className="text-emerald-600 dark:text-emerald-400">✓ {stats.verified} verified</span></>
              ) : ""}
            </p>
            {companies.length > 0 && !verifyTaskId && (
              <button onClick={startVerify}
                className="text-xs px-2.5 py-1 rounded-md bg-secondary hover:bg-secondary/70 transition-colors">
                Verify Emails
              </button>
            )}
          </div>

          <div className="rounded-lg border overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b bg-secondary/50">
                  <th className="text-left px-3 py-2 font-medium">Company</th>
                  <th className="text-left px-3 py-2 font-medium">City</th>
                  <th className="text-left px-3 py-2 font-medium">Industry</th>
                  <th className="text-left px-2 py-2 font-medium">Size</th>
                  <th className="text-left px-2 py-2 font-medium">Roles</th>
                  <th className="text-left px-3 py-2 font-medium">HR Email</th>
                  <th className="text-left px-2 py-2 font-medium">Pipeline</th>
                  <th className="text-right px-3 py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c, i) => {
                  const entry = pipeline[c.name];
                  const status: PipelineStatus = entry?.status || "not_contacted";
                  const needsFollowUp = status === "contacted" && hasAgo(7, entry?.contacted_at || null);
                  const roles = companyRoles[normalizeCompany(c.name)] || [];

                  return (
                    <tr key={i} className={`border-b last:border-0 hover:bg-secondary/30 transition-colors ${needsFollowUp ? "bg-orange-50 dark:bg-orange-950/20" : ""}`}>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-1">
                          <span className="font-medium">{c.name}</span>
                          {needsFollowUp && (
                            <span className="text-[10px] bg-orange-200 text-orange-800 dark:bg-orange-800 dark:text-orange-200 px-1.5 py-0.5 rounded-full font-medium">
                              Follow up!
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">{c.city}</td>
                      <td className="px-3 py-2">
                        {c.industry ? (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${INDUSTRY_COLORS[c.industry] || "bg-secondary"}`}>{c.industry}</span>
                        ) : "—"}
                      </td>
                      <td className="px-2 py-2 text-muted-foreground">{c.size || "—"}</td>
                      <td className="px-2 py-2">
                        {roles.length > 0 ? (
                          <div className="flex gap-1 flex-wrap">
                            {roles.map((role) => (
                              <span key={role} className="text-[10px] bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 px-1.5 py-0.5 rounded-full font-medium">
                                {role}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {c.emails[0] ? (
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => copyEmail(c.emails[0].email, i)}
                              className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                            >
                              {c.emails[0].email}
                              {copiedIdx === i && <span className="ml-1 text-green-600">✓</span>}
                            </button>
                            {!!c.emails[0].confidence_label && (
                              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                                c.emails[0].confidence_label === "verified" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300" :
                                c.emails[0].confidence_label === "confirmed" ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300" :
                                c.emails[0].confidence_label === "live" ? "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300" :
                                c.emails[0].confidence_label === "probable" ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300" :
                                c.emails[0].confidence_label === "invalid" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300" :
                                "bg-secondary"
                              }`}>
                                {c.emails[0].confidence_label === "verified" ? "✓" :
                                 c.emails[0].confidence_label === "confirmed" ? "⟡" :
                                 c.emails[0].confidence_label === "live" ? "⟡" :
                                 c.emails[0].confidence_label === "probable" ? "?" :
                                 c.emails[0].confidence_label === "invalid" ? "✕" : ""}
                                {" "}{c.emails[0].confidence_label}
                              </span>
                            )}
                          </div>
                        ) : "—"}
                      </td>
                      <td className="px-2 py-2">
                        <select
                          value={status}
                          onChange={(e) => updatePipeline(c.name, e.target.value as PipelineStatus)}
                          className={`text-[10px] px-1 py-0.5 rounded border-0 font-medium cursor-pointer ${PIPELINE_COLORS[status]}`}
                        >
                          {(Object.entries(PIPELINE_LABELS) as [PipelineStatus, string][]).map(([key, label]) => (
                            <option key={key} value={key}>{PIPELINE_ICONS[key]} {label}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => personalizeEmail(c, i)}
                            disabled={personalizing === i}
                            className="text-[11px] px-2 py-1 rounded bg-primary/10 text-primary hover:bg-primary/20 transition-colors font-medium disabled:opacity-50"
                          >
                            {personalizing === i ? (
                              <span className="w-3 h-3 border border-primary border-t-transparent rounded-full animate-spin inline-block" />
                            ) : "AI Email"}
                          </button>
                          {c.linkedin && (
                            <a href={c.linkedin} target="_blank" rel="noopener" className="text-[11px] text-muted-foreground hover:text-foreground px-1">in</a>
                          )}
                          {c.website && (
                            <a href={c.website} target="_blank" rel="noopener" className="text-[11px] text-muted-foreground hover:text-foreground px-1">site</a>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Modal overlay */}
          {modal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setModal(null)}>
              <div
                className="bg-background rounded-xl border shadow-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto mx-4"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between px-6 py-4 border-b">
                  <h2 className="text-sm font-semibold">AI Email — {modal.company.name}</h2>
                  <button onClick={() => setModal(null)} className="text-muted-foreground hover:text-foreground text-sm px-2 py-1 rounded hover:bg-secondary transition-colors">✕</button>
                </div>
                <div className="px-6 py-5">
                  {(() => {
                    const email = personalizedEmails[modal.company.name];
                    if (!email) return <p className="text-sm text-muted-foreground">Generating email...</p>;
                    return (
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-sm font-semibold text-foreground mb-1">Subject</h4>
                          <p className="text-sm text-muted-foreground bg-secondary p-3 rounded-md">{email.subject}</p>
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-foreground mb-1">Body</h4>
                          <pre className="text-sm text-muted-foreground bg-secondary p-4 rounded-md whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto">{email.body}</pre>
                        </div>
                        <button
                          onClick={() => copyPersonalizedText(`Subject: ${email.subject}\n\n${email.body}`, modal.idx)}
                          className="text-sm px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                        >
                          {copyEmailText === modal.idx ? "✓ Copied" : "Copy Email"}
                        </button>
                      </div>
                    );
                  })()}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
