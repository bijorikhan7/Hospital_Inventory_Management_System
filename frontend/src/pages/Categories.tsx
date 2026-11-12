import { useEffect, useState } from "react";
import api, { apiMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";

type Cat = { id: number; name: string; code: string; description: string; is_active: boolean };

export function Categories() {
  const { hasRole } = useAuth();
  const toast = useToast();
  const [rows, setRows] = useState<Cat[]>([]);
  const [form, setForm] = useState({ name: "", code: "", description: "" });
  const [error, setError] = useState("");

  function load() {
    api
      .get("/categories/")
      .then((r) => setRows(r.data.results || r.data))
      .catch((e) => setError(apiMessage(e)));
  }
  useEffect(load, []);

  async function create() {
    try {
      await api.post("/categories/", { ...form, is_active: true });
      toast("Category created", "success");
      setForm({ name: "", code: "", description: "" });
      load();
    } catch (e) {
      toast(apiMessage(e), "error");
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Categories</h1>
      {error && <div className="text-rose-700">{error}</div>}
      {hasRole("ADMIN") && (
        <div className="mb-4 grid gap-2 rounded-lg border bg-white p-4 md:grid-cols-4">
          <input className="rounded border px-3 py-2" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="Code (LAP)" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <input className="rounded border px-3 py-2" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <button className="rounded bg-blue-600 text-white" onClick={create}>
            Add
          </button>
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Code</th>
              <th className="px-3 py-2">Description</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="px-3 py-2">{r.name}</td>
                <td className="px-3 py-2">{r.code}</td>
                <td className="px-3 py-2">{r.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
