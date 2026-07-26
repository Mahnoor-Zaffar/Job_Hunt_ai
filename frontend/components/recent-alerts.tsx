"use client";

import { useEffect, useState } from "react";
import { api, NotificationItem } from "@/lib/api";
import { Card } from "@/components/ui";

export function RecentAlerts() {
  const [alerts, setAlerts] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.notifications.list(false, 1, 5);
        setAlerts(data.items);
      } catch { /* ignore */ }
      setLoading(false);
    }
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Card>
        <h3 className="text-sm font-medium mb-3">Recent Alerts</h3>
        <p className="text-xs text-muted-foreground">Loading...</p>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">Recent Alerts</h3>
        {alerts.length > 0 && (
          <a href="/alerts" className="text-[10px] text-primary hover:underline">View all</a>
        )}
      </div>
      {alerts.length === 0 ? (
        <p className="text-xs text-muted-foreground">No alerts yet</p>
      ) : (
        <div className="space-y-2">
          {alerts.map((a) => (
            <div key={a.id} className={`p-2 rounded-md text-xs ${a.is_read ? "" : "bg-secondary/50"}`}>
              <p className={`font-medium truncate ${a.is_read ? "text-muted-foreground" : "text-foreground"}`}>
                {a.title}
              </p>
              <p className="text-[10px] text-muted-foreground mt-0.5 truncate">
                {a.created_at ? new Date(a.created_at).toLocaleDateString() : ""}
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
