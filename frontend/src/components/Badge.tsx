const colors: Record<string, string> = {
  AVAILABLE: "bg-emerald-100 text-emerald-800",
  ASSIGNED: "bg-blue-100 text-blue-800",
  UNDER_REPAIR: "bg-amber-100 text-amber-800",
  DAMAGED: "bg-orange-100 text-orange-800",
  LOST: "bg-slate-200 text-slate-800",
  DISPOSED: "bg-zinc-200 text-zinc-700",
  REPLACED: "bg-purple-100 text-purple-800",
  ACTIVE: "bg-emerald-100 text-emerald-800",
  EXPIRING_SOON: "bg-amber-100 text-amber-800",
  EXPIRED: "bg-rose-100 text-rose-800",
  OPEN: "bg-sky-100 text-sky-800",
  CRITICAL: "bg-rose-100 text-rose-800",
  HIGH: "bg-orange-100 text-orange-800",
  GOOD: "bg-emerald-100 text-emerald-800",
  NEW: "bg-blue-100 text-blue-800",
};

export function Badge({ value }: { value?: string | null }) {
  if (!value) return <span className="text-slate-400">—</span>;
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${colors[value] || "bg-slate-100 text-slate-700"}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
