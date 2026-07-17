"use client";

export function LocationCards({ data }: { data: { source: string; count: number }[] }) {
  const PAK_CITIES = ["Islamabad", "Rawalpindi", "Lahore", "Karachi"];

  const pak = PAK_CITIES.filter((c) => data.some((d) => d.source.toLowerCase().includes(c.toLowerCase()))).map(
    (c) => {
      const found = data.filter((d) => d.source.toLowerCase().includes(c.toLowerCase()));
      return { label: c, count: found.reduce((s, d) => s + d.count, 0) };
    }
  );

  const remote = data.filter(
    (d) =>
      d.source.toLowerCase().includes("remote") &&
      !PAK_CITIES.some((c) => d.source.toLowerCase().includes(c.toLowerCase()))
  );
  const remoteCount = remote.reduce((s, d) => s + d.count, 0);

  const otherCount = data
    .filter(
      (d) =>
        !PAK_CITIES.some((c) => d.source.toLowerCase().includes(c.toLowerCase())) &&
        !d.source.toLowerCase().includes("remote")
    )
    .reduce((s, d) => s + d.count, 0);

  const all = [...pak, { label: "Remote", count: remoteCount }, { label: "Other", count: otherCount }].filter(
    (c) => c.count > 0
  );

  if (all.length === 0) return <p className="text-sm text-muted-foreground py-4 text-center">No location data yet</p>;

  return (
    <div className="grid grid-cols-2 gap-3">
      {all.map((loc) => (
        <div
          key={loc.label}
          className="flex flex-col items-center justify-center p-4 rounded-xl border bg-gradient-to-b from-muted/50 to-muted/20 hover:border-primary/30 transition-colors"
        >
          <span className="text-2xl font-bold tracking-tight">{loc.count}</span>
          <span className="text-xs text-muted-foreground mt-1 font-medium">{loc.label}</span>
        </div>
      ))}
    </div>
  );
}
