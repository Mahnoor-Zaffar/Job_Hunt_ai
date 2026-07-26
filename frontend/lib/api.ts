const BASE_URL = "http://localhost:8000/api/v1";
const USER_ID = "00000000-0000-0000-0000-000000000001";

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

export interface NotificationItem {
  id: string;
  user_id: string | null;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  read_at: string | null;
  job_id: string | null;
  sent_via: string | null;
  created_at: string | null;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  unread_count: number;
}

export interface NotificationPreferences {
  telegram_enabled: boolean;
  email_enabled: boolean;
  notify_on_match: boolean;
  notify_on_new_jobs: boolean;
  min_match_score: number;
  alert_skills: string;
  alert_min_score: number;
  alert_email: string;
  digest_enabled: boolean;
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
  notifications: {
    list: (unreadOnly = false, page = 1, perPage = 50) => {
      const qs = new URLSearchParams({
        user_id: USER_ID,
        unread_only: String(unreadOnly),
        page: String(page),
        per_page: String(perPage),
      }).toString();
      return fetchJSON<NotificationListResponse>(`/notifications?${qs}`);
    },
    markRead: (id: string) =>
      fetchJSON<NotificationItem>(`/notifications/${id}/read`, { method: "PATCH" }),
    markAllRead: () =>
      fetchJSON<{ marked_read: number }>(
        `/notifications/read-all?user_id=${USER_ID}`,
        { method: "POST" },
      ),
    getPreferences: () =>
      fetchJSON<NotificationPreferences>(
        `/notifications/preferences?user_id=${USER_ID}`,
      ),
    updatePreferences: (prefs: NotificationPreferences) =>
      fetchJSON<NotificationPreferences>(
        `/notifications/preferences?user_id=${USER_ID}`,
        { method: "PUT", body: JSON.stringify(prefs) },
      ),
  },
  companies: {
    syncItCompanies: () =>
      fetchJSON<{ synced: number; message: string }>("/companies/sync-it-companies", { method: "POST" }),
    syncStartups: () =>
      fetchJSON<{ synced: number; message: string }>("/companies/sync-startups", { method: "POST" }),
    emailVerificationStatus: () =>
      fetchJSON<{ total: number; verified: number; unverified: number }>(
        "/companies/email-verification-status",
      ),
    toggleWatch: (companyName: string, watch: boolean) =>
      fetchJSON<{ watched: boolean; company_name: string }>(
        "/companies/watchlist/toggle",
        {
          method: "POST",
          body: JSON.stringify({ company_name: companyName, watch }),
        },
      ),
    getWatchlist: () =>
      fetchJSON<{ items: { company_name: string }[]; total: number }>(
        `/companies/watchlist?user_id=${USER_ID}`,
      ),
  },
  career: {
    itCompanies: (verify = false) =>
      fetchJSON<{ companies: any[]; stats: any }>(
        `/career/it-companies?verify=${verify}`,
        { method: "POST" },
      ),
  },
};
