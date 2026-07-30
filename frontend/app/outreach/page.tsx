"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
import { api } from "@/lib/api";

interface OutreachItem {
  id: string;
  job_id: string;
  recipient_email: string;
  recipient_name: string | null;
  subject: string;
  body: string;
  status: string;
  sent_at: string | null;
  created_at: string;
}

export default function OutreachPage() {
  const [items, setItems] = useState<OutreachItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState<string | null>(null);

  async function load() {
    try {
      const data = await api.outreach.list();
      setItems(data);
    } catch { /* ignore */ }
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  async function handleSend(id: string) {
    setSending(id);
    try {
      await api.outreach.send(id);
      await load();
    } catch { /* ignore */ }
    setSending(null);
  }

  if (loading) return <div className="text-sm text-muted-foreground">Loading...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Email Outreach</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Generate and send cold emails to hiring teams
        </p>
      </div>

      {items.length === 0 ? (
        <Card>
          <p className="text-sm text-muted-foreground">
            No outreach emails yet. Go to a job in the Pipeline and generate an email.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <Card key={item.id}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-medium text-sm">{item.subject}</p>
                  <p className="text-xs text-muted-foreground">
                    To: {item.recipient_email} {item.recipient_name ? `(${item.recipient_name})` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    item.status === "sent" ? "bg-emerald-50 text-emerald-600" :
                    item.status === "failed" ? "bg-rose-50 text-rose-600" :
                    "bg-gray-100 text-gray-600"
                  }`}>
                    {item.status}
                  </span>
                  {item.status === "draft" && (
                    <button
                      onClick={() => handleSend(item.id)}
                      disabled={sending === item.id}
                      className="text-xs px-3 py-1 rounded bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
                    >
                      {sending === item.id ? "Sending..." : "Send"}
                    </button>
                  )}
                </div>
              </div>
              <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-sans bg-muted/30 rounded p-3 max-h-48 overflow-auto">
                {item.body.slice(0, 600)}
                {item.body.length > 600 ? "..." : ""}
              </pre>
              {item.sent_at && (
                <p className="text-xs text-muted-foreground mt-2">Sent: {new Date(item.sent_at).toLocaleString()}</p>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
