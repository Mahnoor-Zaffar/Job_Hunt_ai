export function BarChart({ data }: { data: { label: string; value: number }[] }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  const colors = ["#3b82f6", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#6366f1"];

  return (
    <div className="space-y-3">
      {data.map((item, i) => {
        const pct = Math.max((item.value / max) * 100, 2);
        const color = colors[i % colors.length];
        return (
          <div key={item.label} className="group">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-muted-foreground capitalize font-medium">{item.label}</span>
              <span className="font-semibold tabular-nums">{item.value}</span>
            </div>
            <div className="h-2.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-1000 ease-out group-hover:opacity-80"
                style={{ width: `${pct}%`, backgroundColor: color }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function StatPill({ label, count, color = "blue" }: { label: string; count: number; color?: string }) {
  const colorMap: Record<string, string> = {
    blue: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
    purple: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
    green: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
    amber: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
    red: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
  };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${colorMap[color] || colorMap.blue}`}>
      <span>{label}</span>
      <span className="font-bold">{count}</span>
    </div>
  );
}
