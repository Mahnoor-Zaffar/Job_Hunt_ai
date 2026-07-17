import type { ReactNode } from "react";

export function Card({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border bg-card text-card-foreground shadow-sm ${className}`}>
      {title && (
        <div className="px-5 py-3 border-b">
          <h3 className="font-semibold text-sm">{title}</h3>
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}

export function StatCard({
  label,
  value,
  icon,
  color = "blue",
}: {
  label: string;
  value: number;
  icon?: string;
  color?: "blue" | "purple" | "green" | "amber" | "red";
}) {
  const gradients: Record<string, string> = {
    blue: "from-blue-500/10 to-blue-600/5 border-blue-200 dark:border-blue-800",
    purple: "from-purple-500/10 to-purple-600/5 border-purple-200 dark:border-purple-800",
    green: "from-emerald-500/10 to-emerald-600/5 border-emerald-200 dark:border-emerald-800",
    amber: "from-amber-500/10 to-amber-600/5 border-amber-200 dark:border-amber-800",
    red: "from-red-500/10 to-red-600/5 border-red-200 dark:border-red-800",
  };
  const dots: Record<string, string> = {
    blue: "bg-blue-500",
    purple: "bg-purple-500",
    green: "bg-emerald-500",
    amber: "bg-amber-500",
    red: "bg-red-500",
  };

  return (
    <div className={`rounded-xl border bg-gradient-to-br ${gradients[color]} p-5`}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
        <span className={`w-2 h-2 rounded-full ${dots[color]}`} />
      </div>
      <p className="text-3xl font-bold tracking-tight">{value.toLocaleString()}</p>
      {icon && <p className="text-lg mt-1">{icon}</p>}
    </div>
  );
}

export function ActionCard({
  title,
  href,
  icon,
  primary = false,
}: {
  title: string;
  href: string;
  icon: string;
  primary?: boolean;
}) {
  return (
    <a
      href={href}
      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
        primary
          ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
          : "bg-muted hover:bg-muted/70"
      }`}
    >
      <span className="text-lg">{icon}</span>
      <span className="text-sm font-medium">{title}</span>
    </a>
  );
}
