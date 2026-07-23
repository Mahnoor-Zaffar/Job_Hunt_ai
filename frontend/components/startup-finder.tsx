"use client";

import { useState } from "react";

interface Company {
  name: string; website: string; city: string; tier: string;
  hiring: boolean; remote: boolean;
  roles_found: string[]; requirements: string;
  emails: { email: string; priority: number; label: string }[];
  email_keywords: { subject_kw?: string[]; body_kw?: string[]; suggested_subject?: string };
}

export function StartupFinder() {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [filter, setFilter] = useState<"all" | "tier1" | "tier2">("all");
  const [cityFilter, setCityFilter] = useState<string>("all");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  async function run() {
    setLoading(true); setCompanies([]); setStats(null); setProgress("Searching 30+ queries across Google...");
    try {
      const res = await fetch("http://localhost:8000/api/v1/career/startup-emails", { method: "POST" });
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setCompanies(data.companies || []);
      setStats(data.stats || {});
    } catch { setStats({ error: "1" }); }
    setLoading(false); setProgress("");
  }

  function copyEmail(email: string, idx: number) {
    navigator.clipboard.writeText(email);
    setCopiedIdx(idx); setTimeout(() => setCopiedIdx(null), 1500);
  }

  function copyAll() {
    const all = filtered.map((c) => c.emails.map((e) => e.email).join(", ")).join(", ");
    navigator.clipboard.writeText(all);
    setCopiedAll(true); setTimeout(() => setCopiedAll(false), 1500);
  }

  const tier1 = companies.filter((c) => c.tier === "Tier 1");
  const tier2 = companies.filter((c) => c.tier === "Tier 2");
  const hasEmail = companies.filter((c) => c.emails.length > 0);

  const filtered = filter === "tier1" ? tier1 : filter === "tier2" ? tier2 : companies;
  const cityFiltered = cityFilter === "all" ? filtered : filtered.filter((c) => c.city === cityFilter);
  const cities = [...new Set(companies.map((c) => c.city))].filter(Boolean);

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

      {loading && companies.length === 0 && <p className="text-xs text-muted-foreground">This takes 2-5 minutes — searching 30+ queries, scanning company websites, finding HR emails</p>}

      {stats && (
        <div className="flex gap-3 flex-wrap">
          <span className="text-xs bg-secondary px-2 py-1 rounded-md">{stats.total_companies} companies found</span>
          <button onClick={() => setFilter("tier1")} className={`text-xs px-2 py-1 rounded-md transition-colors ${filter === "tier1" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300" : "bg-secondary"}`}>
            🟢 {stats.tier1_hiring_remote} Hiring + Remote
          </button>
          <button onClick={() => setFilter("tier2")} className={`text-xs px-2 py-1 rounded-md transition-colors ${filter === "tier2" ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300" : "bg-secondary"}`}>
            🟡 {stats.tier2_hiring_onsite} Hiring
          </button>
          <button onClick={() => setFilter("all")} className={`text-xs px-2 py-1 rounded-md transition-colors ${filter === "all" ? "bg-primary text-primary-foreground" : "bg-secondary"}`}>
            All
          </button>
          {cities.length > 0 && (
            <select value={cityFilter} onChange={(e) => setCityFilter(e.target.value)} className="text-xs bg-secondary px-2 py-1 rounded-md border-0">
              <option value="all">All Cities</option>
              {cities.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          )}
          {hasEmail.length > 0 && (
            <button onClick={copyAll} className="text-xs px-2 py-1 rounded-md bg-primary text-primary-foreground transition-colors">
              {copiedAll ? "✓ Copied All" : `📋 Copy All (${hasEmail.length})`}
            </button>
          )}
        </div>
      )}

      {cityFiltered.length > 0 && (
        <div className="rounded-lg border overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b bg-secondary/50">
                <th className="text-left px-3 py-2 font-medium">Company</th>
                <th className="text-left px-3 py-2 font-medium">City</th>
                <th className="text-left px-3 py-2 font-medium">Roles</th>
                <th className="text-left px-3 py-2 font-medium">Remote</th>
                <th className="text-left px-3 py-2 font-medium">HR Email</th>
                <th className="text-left px-3 py-2 font-medium">Subject</th>
                <th className="text-right px-3 py-2 font-medium">Copy</th>
              </tr>
            </thead>
            <tbody>
              {cityFiltered.map((c, i) => (
                <tr key={i} className="border-b last:border-0 hover:bg-secondary/30 transition-colors">
                  <td className="px-3 py-2">
                    <span className="font-medium">{c.name}</span>
                    {c.tier === "Tier 1" && <span className="ml-1 text-[10px] bg-emerald-100 text-emerald-700 px-1 rounded">T1</span>}
                    {c.tier === "Tier 2" && <span className="ml-1 text-[10px] bg-amber-100 text-amber-700 px-1 rounded">T2</span>}
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{c.city}</td>
                  <td className="px-3 py-2">
                    {c.roles_found.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {c.roles_found.slice(0, 3).map((r, j) => <span key={j} className="text-[10px] bg-secondary px-1 rounded">{r}</span>)}
                      </div>
                    ) : <span className="text-muted-foreground">—</span>}
                  </td>
                  <td className="px-3 py-2">{c.remote ? "✅" : "—"}</td>
                  <td className="px-3 py-2">{c.emails[0]?.email || "—"}</td>
                  <td className="px-3 py-2 text-[10px] text-muted-foreground max-w-[150px] truncate">{c.email_keywords?.suggested_subject || "—"}</td>
                  <td className="px-3 py-2 text-right">
                    {c.emails[0] && (
                      <button onClick={() => copyEmail(c.emails[0].email, i)} className="text-primary hover:underline text-[10px]">
                        {copiedIdx === i ? "✓ Copied" : "📋"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
