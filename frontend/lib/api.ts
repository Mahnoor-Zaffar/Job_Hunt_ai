const BASE_URL = "/api/v1";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  city: string | null;
  country: string | null;
  is_remote: boolean;
  description: string | null;
  requirements: string | null;
  url: string;
  apply_url: string | null;
  source: string;
  source_id: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  employment_type: string | null;
  experience_level: string | null;
  skills: string[] | null;
  posted_at: string | null;
  status: string;
  created_at: string | null;
}

export interface ScraperInfo {
  source: string;
  display_name: string;
  locations: string[];
  interval_minutes: number;
  is_registered: boolean;
}

export interface DashboardStats {
  stats: {
    total_jobs: number;
    active_jobs: number;
    applications_submitted: number;
    interviews_scheduled: number;
    offers_received: number;
    companies_tracked: number;
    last_scrape: string | null;
  };
  jobs_by_source: { source: string; count: number }[];
  applications_by_status: { source: string; count: number }[];
}

export const api = {
  jobs: {
    search: (params: Record<string, string>) => {
      const qs = new URLSearchParams(params).toString();
      return fetchJSON<{ items: Job[]; total: number }>(`/jobs?${qs}`);
    },
  },
  scrapers: {
    list: () => fetchJSON<{ scrapers: ScraperInfo[]; total: number }>("/scrapers"),
    run: (source?: string) =>
      fetchJSON<{ total_jobs: number; succeeded: number; failed: number }>(
        "/scrapers/run",
        { method: "POST", body: JSON.stringify({ source }) },
      ),
  },
  analytics: {
    dashboard: () => fetchJSON<DashboardStats>("/analytics/dashboard"),
  },
};
