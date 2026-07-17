"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui";

export default function SettingsPage() {
  const [prefs, setPrefs] = useState({
    telegram_enabled: true,
    email_enabled: false,
    notify_on_match: true,
    notify_on_new_jobs: true,
    min_match_score: 0.6,
  });
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/notifications/preferences?user_id=00000000-0000-0000-0000-000000000001")
      .then((r) => r.json())
      .then((data) => {
        if (data.telegram_enabled !== undefined) setPrefs(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  async function save() {
    setSaved(false);
    await fetch(
      "http://localhost:8000/api/v1/notifications/preferences?user_id=00000000-0000-0000-0000-000000000001",
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prefs),
      }
    );
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
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
