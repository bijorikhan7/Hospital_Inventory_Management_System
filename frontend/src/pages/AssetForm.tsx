import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { apiMessage } from "../api/client";
import { useToast } from "../components/Toast";

export function AssetForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const toast = useToast();
  const navigate = useNavigate();
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const [vendors, setVendors] = useState<{ id: number; name: string }[]>([]);
  const [form, setForm] = useState<Record<string, string>>({ condition: "NEW" });
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/categories/?page_size=100").then((r) => setCategories(r.data.results || r.data));
    api.get("/vendors/?page_size=100").then((r) => setVendors(r.data.results || [])).catch(() => undefined);
    if (isEdit) {
      api.get(`/assets/${id}/`).then((r) => {
        const a = r.data;
        setForm({
          name: a.name,
          brand: a.brand || "",
          model: a.model || "",
          serial_number: a.serial_number,
          category: String(a.category),
          vendor: a.vendor ? String(a.vendor) : "",
          location: a.location || "",
          description: a.description || "",
          condition: a.condition,
          purchase_date: a.purchase_date || "",
          purchase_price: a.purchase_price || "",
        });
      });
    }
  }, [id, isEdit]);

  function set(k: string, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      const payload = { ...form, vendor: form.vendor || null, purchase_price: form.purchase_price || null };
      if (isEdit) await api.patch(`/assets/${id}/`, payload);
      else await api.post("/assets/", payload);
      toast("Asset saved", "success");
      navigate("/assets");
    } catch (err) {
      setError(apiMessage(err));
    }
  }

  return (
    <form onSubmit={onSubmit} className="max-w-xl space-y-3 rounded-lg border bg-white p-5">
      <h1 className="text-xl font-semibold">{isEdit ? "Edit asset" : "Add asset"}</h1>
      {error && <div className="rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</div>}
      {[
        ["name", "Name"],
        ["brand", "Brand"],
        ["model", "Model"],
        ["serial_number", "Serial number"],
        ["location", "Location"],
      ].map(([k, label]) => (
        <label key={k} className="block text-sm">
          {label}
          <input className="mt-1 w-full rounded border px-3 py-2" value={form[k] || ""} onChange={(e) => set(k, e.target.value)} required={k === "name" || k === "serial_number"} />
        </label>
      ))}
      <label className="block text-sm">
        Category
        <select required className="mt-1 w-full rounded border px-3 py-2" value={form.category || ""} onChange={(e) => set("category", e.target.value)}>
          <option value="">Select</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        Vendor
        <select className="mt-1 w-full rounded border px-3 py-2" value={form.vendor || ""} onChange={(e) => set("vendor", e.target.value)}>
          <option value="">None</option>
          {vendors.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        Condition
        <select className="mt-1 w-full rounded border px-3 py-2" value={form.condition} onChange={(e) => set("condition", e.target.value)}>
          {["NEW", "GOOD", "FAIR", "DAMAGED", "CRITICAL"].map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        Description
        <textarea className="mt-1 w-full rounded border px-3 py-2" value={form.description || ""} onChange={(e) => set("description", e.target.value)} />
      </label>
      <button className="rounded bg-blue-600 px-4 py-2 text-white">Save</button>
    </form>
  );
}
