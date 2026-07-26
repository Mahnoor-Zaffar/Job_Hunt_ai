"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
import { api, NotificationPreferences } from "@/lib/api";

const DEFAULT_PREFS: NotificationPreferences = {
  telegram_enabled: true,
  email_enabled: false,
  notify_on_match: true,
  notify_on_new_jobs: true,
  min_match_score: 0.6,
  alert_skills: "JavaScript, Python, AI/ML, DevOps, Docker, TypeScript, Node.js, Express.js",
  alert_min_score: 0.3,
  alert_email: "",
  digest_enabled: false,
};

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<NotificationPreferences>(DEFAULT_PREFS);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  useEffect(() => {
    api.notifications.getPreferences()
      .then((data) => {
        setPrefs({ ...DEFAULT_PREFS, ...data });
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  async function save() {
    setSaved(false);
    await api.notifications.updatePreferences(prefs);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  async function syncCompanies() {
    setSyncResult("Syncing...");
    try {
      const itResult = await api.companies.syncItCompanies();
      setSyncResult(itResult.message);
    } catch (e: any) {
      setSyncResult("Error: " + e.message);
    }
  }

  async function refreshEmailVerification() {
    try {
      const status = await api.companies.emailVerificationStatus();
      setSyncResult(`Verified: ${status.verified} / ${status.total} companies`);
    } catch (e: any) {
      setSyncResult("Error: " + e.message);
    }
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Settings</h1>
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <button
          onClick={save}
          className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
        >
          {saved ? "✓ Saved" : "Save Changes"}
        </button>
      </div>

      <div className="space-y-6 max-w-xl">
        <Card title="Skills & Alerts">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium block mb-1">Your Skills (comma-separated)</label>
              <p className="text-xs text-muted-foreground mb-2">
                Jobs matching these skills at watched companies will trigger alerts.
              </p>
              <input
                type="text"
                value={prefs.alert_skills}
                onChange={(e) => setPrefs({ ...prefs, alert_skills: e.target.value })}
                className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Python, JavaScript, React, Node.js, Docker..."
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">
                Minimum Match Score: {prefs.alert_min_score}
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={prefs.alert_min_score}
                onChange={(e) => setPrefs({ ...prefs, alert_min_score: parseFloat(e.target.value) })}
                className="w-full"
              />
              <div className="flex justify-between text-[10px] text-muted-foreground mt-0.5">
                <span>Loose (0.1)</span>
                <span>Strict (1.0)</span>
              </div>
            </div>
          </div>
        </Card>

        <Card title="Notifications">
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <span className="text-sm">Telegram notifications</span>
              <input
                type="checkbox"
                checked={prefs.telegram_enabled}
                onChange={(e) => setPrefs({ ...prefs, telegram_enabled: e.target.checked })}
                className="w-4 h-4 rounded"
              />
            </label>
            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm">Email notifications</span>
                <p className="text-xs text-muted-foreground">Requires SMTP configuration</p>
              </div>
              <input
                type="checkbox"
                checked={prefs.email_enabled}
                onChange={(e) => setPrefs({ ...prefs, email_enabled: e.target.checked })}
                className="w-4 h-4 rounded"
              />
            </label>
            <div>
              <label className="text-sm font-medium block mb-1">Email address for alerts</label>
              <input
                type="email"
                value={prefs.alert_email}
                onChange={(e) => setPrefs({ ...prefs, alert_email: e.target.value })}
                className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="you@example.com"
              />
            </div>
            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm">Daily email digest</span>
                <p className="text-xs text-muted-foreground">Bundle all alerts into one daily email</p>
              </div>
              <input
                type="checkbox"
                checked={prefs.digest_enabled}
                onChange={(e) => setPrefs({ ...prefs, digest_enabled: e.target.checked })}
                className="w-4 h-4 rounded"
              />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Notify on job match</span>
              <input
                type="checkbox"
                checked={prefs.notify_on_match}
                onChange={(e) => setPrefs({ ...prefs, notify_on_match: e.target.checked })}
                className="w-4 h-4 rounded"
              />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Notify on new jobs</span>
              <input
                type="checkbox"
                checked={prefs.notify_on_new_jobs}
                onChange={(e) => setPrefs({ ...prefs, notify_on_new_jobs: e.target.checked })}
                className="w-4 h-4 rounded"
              />
            </label>
          </div>
        </Card>

        <Card title="Company Sync">
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              Import curated company lists into the database for email verification and job alerts.
            </p>
            <div className="flex gap-2">
              <button
                onClick={syncCompanies}
                className="px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
              >
                Sync IT Companies & Startups
              </button>
              <button
                onClick={refreshEmailVerification}
                className="px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
              >
                Check Verification Status
              </button>
            </div>
            {syncResult && (
              <p className="text-xs text-muted-foreground">{syncResult}</p>
            )}
          </div>
        </Card>

        <Card title="Location Preferences">
          <p className="text-xs text-muted-foreground mb-3">
            Jobs from these locations will be shown by default.
          </p>
          <div className="space-y-3">
            {[
              { key: "islamabad", label: "Islamabad" },
              { key: "rawalpindi", label: "Rawalpindi" },
              { key: "lahore", label: "Lahore" },
              { key: "remote", label: "Remote (Worldwide)" },
            ].map((loc) => (
              <label key={loc.key} className="flex items-center justify-between">
                <span className="text-sm">{loc.label}</span>
                <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
              </label>
            ))}
          </div>
        </Card>

        <Card title="Scraper Settings">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium block mb-1">Scrape Interval (minutes)</label>
              <input
                type="number"
                className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
                defaultValue={30}
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Max Concurrent Scrapers</label>
              <input
                type="number"
                className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
                defaultValue={3}
              />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
