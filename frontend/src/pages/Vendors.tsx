import { useEffect, useState } from "react";
import api, { apiMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";

type Vendor = {
  id: number;
  name: string;
  contact_person: string;
  phone: string;
  email: string;
  vendor_type: string;
  is_active: boolean;
};

export function Vendors() {
  const { hasRole } = useAuth();
  const toast = useToast();
  const [rows, setRows] = useState<Vendor[]>([]);
  const [form, setForm] = useState({ name: "", vendor_type: "SUPPLIER", contact_person: "", phone: "", email: "" });

  function load() {
    api
      .get("/vendors/")
      .then((r) => setRows(r.data.results))
      .catch((e) => toast(apiMessage(e), "error"));
  }
  useEffect(load, []);

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Vendors</h1>
      {hasRole("ADMIN") && (
        <div className="mb-4 grid gap-2 rounded-lg border bg-white p-4 md:grid-cols-6">
          <input className="rounded border px-3 py-2" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <select className="rounded border px-3 py-2" value={form.vendor_type} onChange={(e) => setForm({ ...form, vendor_type: e.target.value })}>
            {["SUPPLIER", "MANUFACTURER", "REPAIR_CENTER", "SERVICE_PROVIDER", "OTHER"].map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
          <input className="rounded border px-3 py-2" placeholder="Contact" value={form.contact_person} onChange={(e) => setForm({ ...form, contact_person: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <button
            className="rounded bg-blue-600 text-white"
            onClick={async () => {
              try {
                await api.post("/vendors/", form);
                toast("Vendor created", "success");
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
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Contact</th>
              <th className="px-3 py-2">Phone</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((v) => (
              <tr key={v.id} className="border-t">
                <td className="px-3 py-2">{v.name}</td>
                <td className="px-3 py-2">{v.vendor_type}</td>
                <td className="px-3 py-2">{v.contact_person}</td>
                <td className="px-3 py-2">{v.phone}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
