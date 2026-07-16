export function BarChart({ data }: { data: { label: string; value: number }[] }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  const colors = ["#3b82f6", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"];

  return (
    <div className="space-y-2">
      {data.map((item, i) => (
        <div key={item.label} className="flex items-center gap-2 text-sm">
          <span className="w-24 text-right text-muted-foreground truncate capitalize">{item.label}</span>
          <div className="flex-1 h-6 bg-muted rounded overflow-hidden">
            <div
              className="h-full rounded transition-all duration-700 ease-out"
              style={{
                width: `${(item.value / max) * 100}%`,
                backgroundColor: colors[i % colors.length],
              }}
            />
          </div>
          <span className="w-12 text-right font-medium tabular-nums">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

export function LineChart({ data, height = 200 }: { data: { label: string; value: number }[]; height?: number }) {
  if (data.length < 2) return <p className="text-sm text-muted-foreground py-4">Not enough data points</p>;

  const max = Math.max(...data.map((d) => d.value), 1);
  const width = 100 / (data.length - 1);
  const points = data.map((d, i) => `${i * width},${height - (d.value / max) * (height - 20) - 10}`).join(" ");

  return (
    <svg viewBox={`0 0 100 ${height}`} className="w-full" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke="#3b82f6"
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
      {data.map((d, i) => (
        <g key={d.label}>
          <circle cx={i * width} cy={height - (d.value / max) * (height - 20) - 10} r="3" fill="#3b82f6" />
          <text x={i * width} y={height - 5} textAnchor="middle" fontSize="5" fill="currentColor" className="opacity-50">{d.label}</text>
          <text x={i * width} y={height - (d.value / max) * (height - 20) - 16} textAnchor="middle" fontSize="4" fill="currentColor" className="opacity-70">{d.value}</text>
        </g>
      ))}
    </svg>
  );
}
