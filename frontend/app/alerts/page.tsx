"use client";

import { useEffect, useState } from "react";
import { api, NotificationItem } from "@/lib/api";

const TYPE_COLORS: Record<string, string> = {
  job_match: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  company_hiring: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  scraper: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  default: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

function getScore(message: string): number | null {
  const m = message.match(/Match score:\s*(\d+)%/);
  return m ? parseInt(m[1]) : null;
}

export default function AlertsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const data = await api.notifications.list();
      setNotifications(data.items);
      setUnreadCount(data.unread_count);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  async function markRead(id: string) {
    await api.notifications.markRead(id);
    load();
  }

  async function markAllRead() {
    await api.notifications.markAllRead();
    load();
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Alerts</h1>
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Alerts</h1>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-primary text-primary-foreground">
              {unreadCount} unread
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
          >
            Mark all read
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-lg text-muted-foreground mb-2">No alerts yet</p>
          <p className="text-sm text-muted-foreground/60">
            Job alerts will appear here when new jobs match your skills at watched companies.
            Set up your preferences in Settings.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => {
            const score = getScore(n.message);
            const typeColor = TYPE_COLORS[n.type] || TYPE_COLORS.default;
            return (
              <div
                key={n.id}
                className={`flex items-start gap-4 p-4 rounded-lg border transition-colors ${
                  n.is_read
                    ? "bg-background border-border"
                    : "bg-secondary/20 border-primary/30"
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 text-[10px] font-medium rounded-full ${typeColor}`}>
                      {n.type}
                    </span>
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-primary" />
                    )}
                    {score !== null && (
                      <span className={`px-2 py-0.5 text-[10px] font-medium rounded-full ${
                        score >= 70
                          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                          : score >= 40
                          ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                          : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                      }`}>
                        {score}% match
                      </span>
                    )}
                  </div>
                  <p className="font-medium text-sm">{n.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{n.message}</p>
                  <p className="text-[10px] text-muted-foreground/50 mt-1">
                    {n.created_at ? new Date(n.created_at).toLocaleString() : ""}
                  </p>
                </div>
                {!n.is_read && (
                  <button
                    onClick={() => markRead(n.id)}
                    className="px-2 py-1 text-[10px] font-medium text-muted-foreground hover:text-foreground rounded border border-border hover:bg-secondary/50 transition-colors shrink-0"
                  >
                    Dismiss
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
