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
    <div className={`rounded-lg border bg-card text-card-foreground p-4 ${className}`}>
      {title && <h3 className="font-semibold text-sm mb-3">{title}</h3>}
      {children}
    </div>
  );
}

export function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-2xl font-bold text-primary">{value.toLocaleString()}</p>
    </Card>
  );
}
