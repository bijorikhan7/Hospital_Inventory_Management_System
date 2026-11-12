import { useEffect, useState } from "react";
import api, { apiMessage } from "../api/client";
import { Badge } from "../components/Badge";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";

export function Warranties() {
  const { hasRole } = useAuth();
  const toast = useToast();
  const [rows, setRows] = useState<any[]>([]);
  const [assets, setAssets] = useState<any[]>([]);
  const [form, setForm] = useState({ asset: "", provider: "", warranty_type: "MANUFACTURER", start_date: "", end_date: "", warranty_number: "" });

  function load() {
    api.get("/warranties/").then((r) => setRows(r.data.results)).catch((e) => toast(apiMessage(e), "error"));
    api.get("/assets/?page_size=100").then((r) => setAssets(r.data.results)).catch(() => undefined);
  }
  useEffect(load, []);

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Warranties</h1>
      {hasRole("ADMIN") && (
        <div className="mb-4 grid gap-2 rounded-lg border bg-white p-4 md:grid-cols-6">
          <select className="rounded border px-2 py-2" value={form.asset} onChange={(e) => setForm({ ...form, asset: e.target.value })}>
            <option value="">Asset</option>
            {assets.map((a) => (
              <option key={a.id} value={a.id}>
                {a.asset_code}
              </option>
            ))}
          </select>
          <input className="rounded border px-2 py-2" placeholder="Provider" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} />
          <input type="date" className="rounded border px-2 py-2" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
          <input type="date" className="rounded border px-2 py-2" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
          <input className="rounded border px-2 py-2" placeholder="Warranty #" value={form.warranty_number} onChange={(e) => setForm({ ...form, warranty_number: e.target.value })} />
          <button
            className="rounded bg-blue-600 text-white"
            onClick={async () => {
              try {
                await api.post("/warranties/", form);
                toast("Warranty saved", "success");
                load();
              } catch (e) {
                toast(apiMessage(e), "error");
              }
            }}
          >
            Add
          </button>
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-3 py-2">Asset</th>
              <th className="px-3 py-2">Provider</th>
              <th className="px-3 py-2">End</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((w) => (
              <tr key={w.id} className="border-t">
                <td className="px-3 py-2">{w.asset}</td>
                <td className="px-3 py-2">{w.provider}</td>
                <td className="px-3 py-2">{w.end_date}</td>
                <td className="px-3 py-2">
                  <Badge value={w.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
