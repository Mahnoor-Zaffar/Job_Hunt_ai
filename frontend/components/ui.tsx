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
    <div className={`rounded-lg border bg-card p-5 ${className}`}>
      {title && <h3 className="font-medium text-sm mb-3">{title}</h3>}
      {children}
    </div>
  );
}

export function StatCard({
  label,
  value,
  color = "indigo",
}: {
  label: string;
  value: number;
  color?: "indigo" | "violet" | "emerald" | "amber" | "rose";
}) {
  const dots: Record<string, string> = {
    indigo: "bg-indigo-500",
    violet: "bg-violet-500",
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
    rose: "bg-rose-500",
  };
  const borders: Record<string, string> = {
    indigo: "border-l-indigo-500",
    violet: "border-l-violet-500",
    emerald: "border-l-emerald-500",
    amber: "border-l-amber-500",
    rose: "border-l-rose-500",
  };

  return (
    <div className={`rounded-lg border bg-card p-5 border-l-2 ${borders[color]}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        <span className={`w-1.5 h-1.5 rounded-full ${dots[color]}`} />
      </div>
      <p className="text-2xl font-semibold tracking-tight">{value.toLocaleString()}</p>
    </div>
  );
}
