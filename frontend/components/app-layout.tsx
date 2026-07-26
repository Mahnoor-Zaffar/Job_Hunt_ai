"use client";

import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "◧" },
  { href: "/jobs", label: "All Jobs", icon: "⊞" },
  { href: "/pipeline", label: "Pipeline", icon: "⊣" },
  { href: "/remote-jobs", label: "Remote Jobs", icon: "◎" },
  { href: "/startups", label: "Startups", icon: "⟐" },
  { href: "/it-companies", label: "IT Companies", icon: "⊞" },
  { href: "/companies", label: "Companies", icon: "⊡" },
  { href: "/alerts", label: "Alerts", icon: "⏢" },
  { href: "/applications", label: "Applications", icon: "⊟" },
  { href: "/resume", label: "Resume", icon: "⊠" },
  { href: "/classify", label: "Classifier", icon: "◎" },
  { href: "/settings", label: "Settings", icon: "⊡" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.notifications.list(true, 1, 1);
        setUnreadCount(data.unread_count);
      } catch {
        // ignore
      }
    }
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="fixed inset-y-0 left-0 z-40 w-56 flex flex-col border-r bg-sidebar">
      <div className="flex items-center gap-2 h-14 px-4 border-b">
        <span className="w-6 h-6 rounded-md bg-primary flex items-center justify-center text-[10px] text-primary-foreground font-bold">
          JH
        </span>
        <span className="font-semibold text-sm tracking-tight">Job Hunting</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-auto">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const isAlerts = item.href === "/alerts";
          return (
            <a
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-all duration-150 ${
                active
                  ? "bg-secondary text-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
              }`}
            >
              <span className="text-base w-5 text-center">{item.icon}</span>
              <span className="flex-1">{item.label}</span>
              {isAlerts && unreadCount > 0 && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-primary text-primary-foreground">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </a>
          );
        })}
      </nav>

      <div className="border-t p-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="w-5 h-5 rounded-full bg-secondary flex items-center justify-center text-[10px]">D</span>
          Dev User
        </div>
        <ThemeToggle />
      </div>
    </aside>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className="pl-56">
        <div className="max-w-7xl mx-auto px-8 py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
