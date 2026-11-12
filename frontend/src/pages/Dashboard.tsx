import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { apiMessage } from "../api/client";
import { Badge } from "../components/Badge";
import type { DashboardData } from "../types";

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/dashboard/")
      .then((r) => setData(r.data))
      .catch((e) => setError(apiMessage(e)));
  }, []);

  if (error) return <div className="rounded bg-rose-50 p-3 text-rose-700">{error}</div>;
  if (!data) return <div className="text-slate-500">Loading dashboard…</div>;

  const cards = [
    ["Total Assets", data.assets.total],
    ["Available", data.assets.available],
    ["Assigned", data.assets.assigned],
    ["Under Repair", data.assets.under_repair],
    ["Damaged", data.assets.damaged],
    ["Lost", data.assets.lost],
    ["Disposed", data.assets.disposed],
    ["Replaced", data.assets.replaced],
    ["Warranty expiring", data.warranties.expiring_soon],
    ["Warranty expired", data.warranties.expired],
    ["Open issues", data.open_issues],
    ["Active warranties", data.warranties.active],
  ];

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Dashboard</h1>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {cards.map(([label, value]) => (
          <div key={String(label)} className="rounded-lg border bg-white p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
            <div className="mt-1 text-2xl font-semibold">{value ?? 0}</div>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-lg border bg-white">
        <div className="border-b px-4 py-3 font-medium">Recent activities</div>
        {data.recent_activities.length === 0 ? (
          <div className="p-6 text-sm text-slate-500">No recent activity.</div>
        ) : (
          <ul className="divide-y">
            {data.recent_activities.map((a) => (
              <li key={a.id} className="flex items-center justify-between px-4 py-2 text-sm">
                <div>
                  <Link className="font-medium text-blue-700" to={`/assets/${a.asset_code}`}>
                    {a.asset_code}
                  </Link>{" "}
                  <Badge value={a.action} />
                  <div className="text-slate-500">{a.description}</div>
                </div>
                <div className="text-xs text-slate-400">{new Date(a.created_at).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
