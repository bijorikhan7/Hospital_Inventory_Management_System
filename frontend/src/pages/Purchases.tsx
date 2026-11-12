import { useEffect, useState } from "react";
import api, { apiMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";

export function Purchases() {
  const { hasRole } = useAuth();
  const toast = useToast();
  const [rows, setRows] = useState<any[]>([]);
  const [assets, setAssets] = useState<any[]>([]);
  const [vendors, setVendors] = useState<any[]>([]);
  const [form, setForm] = useState({ asset: "", vendor: "", invoice_number: "", purchase_date: "", quantity: "1", unit_price: "" });

  function load() {
    api.get("/purchases/").then((r) => setRows(r.data.results)).catch((e) => toast(apiMessage(e), "error"));
    api.get("/assets/?page_size=100").then((r) => setAssets(r.data.results));
    api.get("/vendors/?page_size=100").then((r) => setVendors(r.data.results));
  }
  useEffect(load, []);

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Purchases</h1>
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
          <select className="rounded border px-2 py-2" value={form.vendor} onChange={(e) => setForm({ ...form, vendor: e.target.value })}>
            <option value="">Vendor</option>
            {vendors.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
          <input className="rounded border px-2 py-2" placeholder="Invoice" value={form.invoice_number} onChange={(e) => setForm({ ...form, invoice_number: e.target.value })} />
          <input type="date" className="rounded border px-2 py-2" value={form.purchase_date} onChange={(e) => setForm({ ...form, purchase_date: e.target.value })} />
          <input className="rounded border px-2 py-2" placeholder="Unit price" value={form.unit_price} onChange={(e) => setForm({ ...form, unit_price: e.target.value })} />
          <button
            className="rounded bg-blue-600 text-white"
            onClick={async () => {
              try {
                await api.post("/purchases/", form);
                toast("Purchase saved", "success");
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
              <th className="px-3 py-2">Invoice</th>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Qty</th>
              <th className="px-3 py-2">Total</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="px-3 py-2">{p.invoice_number}</td>
                <td className="px-3 py-2">{p.purchase_date}</td>
                <td className="px-3 py-2">{p.quantity}</td>
                <td className="px-3 py-2">{p.total_price}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
