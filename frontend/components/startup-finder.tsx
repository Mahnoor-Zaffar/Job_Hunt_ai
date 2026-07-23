"use client";

import { useState } from "react";

interface Company {
  name: string; website: string; city: string; tier: string;
  hiring: boolean; remote: boolean; scanned: boolean;
  roles_found: string[]; requirements: string;
  emails: { email: string; priority: number; label: string }[];
  email_keywords: { subject_kw?: string[]; body_kw?: string[]; suggested_subject?: string };
  industry: string; size: string; linkedin: string;
}

const INDUSTRY_COLORS: Record<string, string> = {
  "Fintech": "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  "E-commerce": "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  "AI/ML": "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  "SaaS": "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300",
  "B2B SaaS": "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300",
  "Software Services": "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300",
  "Logistics": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  "EdTech": "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
};

const EMAIL_TEMPLATE = `Hi [Hiring Manager],

I'm a full-stack / backend developer based in Pakistan with experience in Python, JavaScript, React, Node.js, Docker, and cloud infrastructure. I'm reaching out because I'm interested in remote opportunities and your company caught my attention.

I've been following the tech ecosystem in Pakistan and believe my skills in building scalable applications would be a strong fit for your team.

I've attached my resume for your review. I'd love to schedule a brief call to discuss how I can contribute.

Best regards,
[Your Name]
[Your Email]
[Your Phone]`;

export function StartupFinder() {
  const [loading, setLoading] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [filter, setFilter] = useState<"all" | "tier1" | "tier2">("all");
  const [cityFilter, setCityFilter] = useState<string>("all");
  const [industryFilter, setIndustryFilter] = useState<string>("all");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [showEmailBody, setShowEmailBody] = useState(false);
  const [showTemplate, setShowTemplate] = useState(false);

  async function run() {
    setLoading(true); setCompanies([]); setStats(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/career/startup-emails", { method: "POST" });
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setCompanies(data.companies || []);
      setStats(data.stats || {});
    } catch { setStats({ error: "1" }); }
    setLoading(false);
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
    navigator.clipboard.writeText(EMAIL_TEMPLATE);
    setShowTemplate(false);
  }

  function exportCSV() {
    const rows = [["Company", "City", "Industry", "Size", "HR Email", "LinkedIn"]];
    filtered.forEach((c) => rows.push([c.name, c.city, c.industry, c.size, c.emails[0]?.email || "", c.linkedin]));
    const csv = rows.map((r) => r.map((v) => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "pakistan_startups.csv"; a.click();
  }

  const filtered = (() => {
    let f = companies;
    if (filter === "tier1") f = f.filter((c) => c.tier === "Tier 1");
    if (filter === "tier2") f = f.filter((c) => c.tier === "Tier 2");
    if (cityFilter !== "all") f = f.filter((c) => c.city === cityFilter);
    if (industryFilter !== "all") f = f.filter((c) => c.industry === industryFilter);
    return f;
  })();

  const cities = [...new Set(companies.map((c) => c.city))].filter(Boolean);
  const industries = [...new Set(companies.map((c) => c.industry))].filter(Boolean);
  const hasEmails = companies.filter((c) => c.emails.length > 0).length;

  return (
    <div className="space-y-4">
      <button
        onClick={run}
        disabled={loading}
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {loading ? (
          <><span className="w-3.5 h-3.5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" /> Scanning...</>
        ) : (
          <>🔍 Find Pakistan Startups</>
        )}
      </button>

      {loading && <p className="text-xs text-muted-foreground">Searching Google + scanning company websites + finding HR emails — takes 1-2 minutes</p>}

      {stats && companies.length > 0 && (
        <>
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => setFilter("all")} className={`text-xs px-2.5 py-1 rounded-md transition-colors font-medium ${filter === "all" ? "bg-primary text-primary-foreground" : "bg-secondary"}`}>
              All ({companies.length})
            </button>
            <button onClick={() => setFilter("tier1")} className={`text-xs px-2.5 py-1 rounded-md transition-colors font-medium ${filter === "tier1" ? "bg-emerald-100 text-emerald-700" : "bg-secondary"}`}>
              🟢 Hiring ({stats.tier1_hiring_remote || 0})
            </button>
            <button onClick={() => setFilter("tier2")} className={`text-xs px-2.5 py-1 rounded-md transition-colors font-medium ${filter === "tier2" ? "bg-amber-100 text-amber-700" : "bg-secondary"}`}>
              🟡 Potential ({stats.tier2_hiring_onsite || 0})
            </button>

            <span className="border-r mx-1" />

            <select value={cityFilter} onChange={(e) => setCityFilter(e.target.value)} className="text-xs bg-secondary px-2.5 py-1 rounded-md border-0">
              <option value="all">All Cities</option>
              {cities.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>

            <select value={industryFilter} onChange={(e) => setIndustryFilter(e.target.value)} className="text-xs bg-secondary px-2.5 py-1 rounded-md border-0">
              <option value="all">All Industries</option>
              {industries.map((i) => <option key={i} value={i}>{i}</option>)}
            </select>

            <button onClick={copyAllEmails} className="text-xs px-2.5 py-1 rounded-md bg-secondary hover:bg-secondary/70 transition-colors">
              {copiedAll ? "✓ Copied" : `📋 Copy All (${hasEmails})`}
            </button>

            <button onClick={exportCSV} className="text-xs px-2.5 py-1 rounded-md bg-secondary hover:bg-secondary/70 transition-colors">
              📥 CSV
            </button>

            <button onClick={() => setShowEmailBody(!showEmailBody)} className="text-xs px-2.5 py-1 rounded-md bg-secondary hover:bg-secondary/70 transition-colors">
              📧 Email Template
            </button>
          </div>

          {showEmailBody && (
            <div className="rounded-lg border bg-card p-4 space-y-2">
              <h4 className="text-sm font-medium">Email Template (copy + personalize)</h4>
              <pre className="text-xs text-muted-foreground bg-secondary p-3 rounded-md whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">{EMAIL_TEMPLATE}</pre>
              <button onClick={copyEmailTemplate} className="text-xs px-3 py-1 bg-primary text-primary-foreground rounded-md">📋 Copy Template</button>
            </div>
          )}

          <p className="text-xs text-muted-foreground">
            Showing {filtered.length} of {companies.length} companies · {hasEmails} have HR emails
          </p>

          <div className="rounded-lg border overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b bg-secondary/50">
                  <th className="text-left px-3 py-2 font-medium">Company</th>
                  <th className="text-left px-3 py-2 font-medium">City</th>
                  <th className="text-left px-3 py-2 font-medium">Industry</th>
                  <th className="text-left px-2 py-2 font-medium">Size</th>
                  <th className="text-left px-3 py-2 font-medium">HR Email</th>
                  <th className="text-right px-3 py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c, i) => (
                  <tr key={i} className="border-b last:border-0 hover:bg-secondary/30 transition-colors">
                    <td className="px-3 py-2">
                      <span className="font-medium">{c.name}</span>
                      {c.scanned ? (
                        <span className="ml-1 text-[10px] bg-blue-100 text-blue-700 px-1 rounded">✓ scanned</span>
                      ) : (
                        <span className="ml-1 text-[10px] bg-muted text-muted-foreground px-1 rounded">not scanned</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{c.city}</td>
                    <td className="px-3 py-2">
                      {c.industry ? (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${INDUSTRY_COLORS[c.industry] || "bg-secondary"}`}>{c.industry}</span>
                      ) : "—"}
                    </td>
                    <td className="px-2 py-2 text-muted-foreground">{c.size || "—"}</td>
                    <td className="px-3 py-2">
                      <span className="text-muted-foreground">{c.emails[0]?.email || "—"}</span>
                      <span className="ml-1 text-[10px] text-muted-foreground">{c.emails[0]?.label}</span>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {c.emails[0] && (
                          <button onClick={() => copyEmail(c.emails[0].email, i)} className="text-primary hover:underline text-[10px] px-1">
                            {copiedIdx === i ? "✓" : "📋"}
                          </button>
                        )}
                        {c.linkedin && (
                          <a href={c.linkedin} target="_blank" rel="noopener" className="text-[10px] text-muted-foreground hover:text-foreground px-1">in</a>
                        )}
                        {c.website && (
                          <a href={c.website} target="_blank" rel="noopener" className="text-[10px] text-muted-foreground hover:text-foreground px-1">🌐</a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
