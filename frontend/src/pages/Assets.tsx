import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { apiMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Badge } from "../components/Badge";
import type { Asset, Paginated } from "../types";

export function Assets() {
  const { hasRole } = useAuth();
  const [rows, setRows] = useState<Asset[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page) });
    if (q) params.set("search", q);
    if (status) params.set("status", status);
    api
      .get<Paginated<Asset>>(`/assets/?${params}`)
      .then((r) => {
        setRows(r.data.results);
        setCount(r.data.count);
      })
      .catch((e) => setError(apiMessage(e)))
      .finally(() => setLoading(false));
  }, [page, q, status]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Assets</h1>
        {hasRole("ADMIN", "IT_STAFF") && (
          <Link to="/assets/new" className="rounded bg-blue-600 px-3 py-2 text-sm text-white">
            Add asset
          </Link>
        )}
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        <input
          placeholder="Search code, name, brand, serial, employee…"
          className="min-w-56 flex-1 rounded border px-3 py-2 text-sm"
          value={q}
          onChange={(e) => {
            setPage(1);
            setQ(e.target.value);
          }}
        />
        <select
          className="rounded border px-3 py-2 text-sm"
          value={status}
          onChange={(e) => {
            setPage(1);
            setStatus(e.target.value);
          }}
        >
          <option value="">All statuses</option>
          {["AVAILABLE", "ASSIGNED", "UNDER_REPAIR", "DAMAGED", "LOST", "DISPOSED", "REPLACED"].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </div>
      {error && <div className="mb-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</div>}
      {loading ? (
        <div className="text-slate-500">Loading…</div>
      ) : rows.length === 0 ? (
        <div className="rounded border bg-white p-8 text-center text-slate-500">No assets found.</div>
      ) : (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="px-3 py-2">Code</th>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Serial</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Assigned to</th>
                <th className="px-3 py-2">Warranty</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id} className="border-t">
                  <td className="px-3 py-2">
                    <Link className="font-medium text-blue-700" to={`/assets/${a.asset_code}`}>
                      {a.asset_code}
                    </Link>
                  </td>
                  <td className="px-3 py-2">
                    {a.name}
                    <div className="text-xs text-slate-500">
                      {a.brand} {a.model}
                    </div>
                  </td>
                  <td className="px-3 py-2">{a.serial_number}</td>
                  <td className="px-3 py-2">
                    <Badge value={a.status} />
                  </td>
                  <td className="px-3 py-2">{a.employee_name || "—"}</td>
                  <td className="px-3 py-2">
                    <Badge value={a.warranty_status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="mt-3 flex items-center justify-between text-sm">
        <span className="text-slate-500">{count} results</span>
        <div className="flex gap-2">
          <button disabled={page === 1} className="rounded border px-2 py-1 disabled:opacity-40" onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <button disabled={page * 20 >= count} className="rounded border px-2 py-1 disabled:opacity-40" onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
