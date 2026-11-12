import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { apiMessage } from "../api/client";
import { Badge } from "../components/Badge";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";

export function Issues() {
  const { hasRole } = useAuth();
  const toast = useToast();
  const [rows, setRows] = useState<any[]>([]);

  function load() {
    api.get("/issues/").then((r) => setRows(r.data.results)).catch((e) => toast(apiMessage(e), "error"));
  }
  useEffect(load, []);

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Issues</h1>
      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-3 py-2">Asset</th>
              <th className="px-3 py-2">Title</th>
              <th className="px-3 py-2">Priority</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((i) => (
              <tr key={i.id} className="border-t">
                <td className="px-3 py-2">
                  <Link className="text-blue-700" to={`/assets/${i.asset_code}`}>
                    {i.asset_code}
                  </Link>
                </td>
                <td className="px-3 py-2">{i.title}</td>
                <td className="px-3 py-2">
                  <Badge value={i.priority} />
                </td>
                <td className="px-3 py-2">
                  <Badge value={i.status} />
                </td>
                <td className="px-3 py-2">
                  {hasRole("ADMIN", "IT_STAFF") && i.status === "OPEN" && (
                    <button
                      className="text-blue-700"
                      onClick={async () => {
                        await api.post(`/issues/${i.id}/review/`);
                        load();
                      }}
                    >
                      Review
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function Repairs() {
  const toast = useToast();
  const [rows, setRows] = useState<any[]>([]);
  function load() {
    api.get("/repairs/").then((r) => setRows(r.data.results)).catch((e) => toast(apiMessage(e), "error"));
  }
  useEffect(load, []);
  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Repairs</h1>
      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-3 py-2">Asset</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Warranty</th>
              <th className="px-3 py-2">Cost</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="px-3 py-2">{r.asset_code}</td>
                <td className="px-3 py-2">
                  <Badge value={r.status} />
                </td>
                <td className="px-3 py-2">{r.warranty_covered ? "Yes" : "No"}</td>
                <td className="px-3 py-2">{r.actual_cost || r.estimated_cost || "—"}</td>
                <td className="px-3 py-2 space-x-2">
                  {r.status === "PENDING" && (
                    <button className="text-blue-700" onClick={async () => { await api.patch(`/repairs/${r.id}/`, { status: "IN_PROGRESS" }); load(); }}>
                      In progress
                    </button>
                  )}
                  {r.status === "IN_PROGRESS" && (
                    <button className="text-emerald-700" onClick={async () => { await api.patch(`/repairs/${r.id}/`, { status: "COMPLETED" }); load(); }}>
                      Complete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
