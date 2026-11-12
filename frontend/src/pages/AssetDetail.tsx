import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import api, { apiMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Badge } from "../components/Badge";
import { ConfirmDialog, Modal } from "../components/Modal";
import { useToast } from "../components/Toast";
import type { Asset, Employee } from "../types";

export function AssetDetail() {
  const { code } = useParams();
  const { hasRole, user } = useAuth();
  const toast = useToast();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [error, setError] = useState("");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [modal, setModal] = useState<null | "assign" | "transfer" | "return" | "issue" | "repair" | "replace">(null);
  const [confirmDispose, setConfirmDispose] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});

  async function load() {
    try {
      const { data } = await api.get(`/assets/by-code/${code}/`);
      setAsset(data);
    } catch (e) {
      setError(apiMessage(e, "Asset not found"));
    }
  }

  useEffect(() => {
    load();
    if (hasRole("ADMIN", "IT_STAFF")) {
      api.get("/auth/employees/?status=ACTIVE&page_size=100").then((r) => setEmployees(r.data.results || r.data));
    }
  }, [code]);

  if (error) return <div className="rounded bg-rose-50 p-3 text-rose-700">{error}</div>;
  if (!asset) return <div className="text-slate-500">Loading asset…</div>;

  const staff = hasRole("ADMIN", "IT_STAFF");
  const canAssign = staff && asset.status === "AVAILABLE";
  const canReturn = staff && asset.status === "ASSIGNED";
  const canTransfer = staff && asset.status === "ASSIGNED";
  const canIssue = hasRole("ADMIN", "IT_STAFF") || (user?.employee && asset.current_employee === user.employee);
  const latestWarranty = asset.warranties?.[0];

  async function postAction(path: string, body: object) {
    try {
      await api.post(path, body);
      toast("Saved", "success");
      setModal(null);
      await load();
    } catch (e) {
      toast(apiMessage(e), "error");
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="lg:col-span-2 rounded-lg border bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 className="text-2xl font-semibold">{asset.name}</h1>
            <p className="text-sm text-slate-500">
              {asset.brand} {asset.model}
            </p>
          </div>
          <Badge value={asset.status} />
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-slate-500">Asset Code</dt>
            <dd className="font-medium">{asset.asset_code}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Serial</dt>
            <dd>{asset.serial_number}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Condition</dt>
            <dd>
              <Badge value={asset.condition} />
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Assigned To</dt>
            <dd>{asset.employee_name || "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Warranty</dt>
            <dd>
              <Badge value={asset.warranty_status} />
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Warranty Until</dt>
            <dd>{latestWarranty?.end_date || "—"}</dd>
          </div>
          {asset.purchase_price != null && (
            <div>
              <dt className="text-slate-500">Purchase price</dt>
              <dd>{asset.purchase_price}</dd>
            </div>
          )}
          <div>
            <dt className="text-slate-500">Location</dt>
            <dd>{asset.location || "—"}</dd>
          </div>
        </dl>
        <div className="mt-5 flex flex-wrap gap-2">
          {staff && (
            <Link className="rounded border px-3 py-1.5 text-sm" to={`/assets/${asset.id}/edit`}>
              Edit
            </Link>
          )}
          {canAssign && (
            <button className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white" onClick={() => setModal("assign")}>
              Assign
            </button>
          )}
          {canReturn && (
            <button className="rounded border px-3 py-1.5 text-sm" onClick={() => setModal("return")}>
              Return
            </button>
          )}
          {canTransfer && (
            <button className="rounded border px-3 py-1.5 text-sm" onClick={() => setModal("transfer")}>
              Transfer
            </button>
          )}
          {canIssue && (
            <button className="rounded border px-3 py-1.5 text-sm" onClick={() => setModal("issue")}>
              Report Problem
            </button>
          )}
          {staff && (
            <button className="rounded border px-3 py-1.5 text-sm" onClick={() => setModal("repair")}>
              Repair
            </button>
          )}
          {staff && (
            <Link className="rounded border px-3 py-1.5 text-sm" to={`/history?asset=${asset.id}`}>
              View History
            </Link>
          )}
          {hasRole("ADMIN") && !["REPLACED", "DISPOSED"].includes(asset.status) && (
            <button className="rounded border px-3 py-1.5 text-sm" onClick={() => setModal("replace")}>
              Replace
            </button>
          )}
          {hasRole("ADMIN") && !["DISPOSED"].includes(asset.status) && (
            <button className="rounded border px-3 py-1.5 text-sm text-rose-700" onClick={() => setConfirmDispose(true)}>
              Dispose
            </button>
          )}
          <Link className="rounded border px-3 py-1.5 text-sm" to={`/qr-print?code=${asset.asset_code}`}>
            Print QR
          </Link>
        </div>
      </div>
      <div className="rounded-lg border bg-white p-5 text-center">
        <div className="mb-2 text-sm font-medium">QR Code</div>
        <div className="flex justify-center">
          <QRCodeSVG value={asset.qr_payload || `/assets/${asset.asset_code}`} size={180} />
        </div>
        <p className="mt-2 break-all text-xs text-slate-500">{asset.qr_payload}</p>
        <button
          className="mt-3 inline-block text-sm text-blue-700"
          onClick={async () => {
            const res = await api.get(`/assets/${asset.id}/qr/`, { responseType: "blob" });
            const url = URL.createObjectURL(res.data);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${asset.asset_code}.png`;
            a.click();
          }}
        >
          Download PNG
        </button>
      </div>

      {modal === "assign" && (
        <Modal title="Assign asset" onClose={() => setModal(null)}>
          <select className="mb-3 w-full rounded border px-3 py-2" onChange={(e) => setForm({ employee_id: e.target.value })}>
            <option value="">Select employee</option>
            {employees.map((e) => (
              <option key={e.id} value={e.id}>
                {e.employee_code} — {e.name}
              </option>
            ))}
          </select>
          <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white" onClick={() => postAction(`/assets/${asset.id}/assign/`, form)}>
            Assign
          </button>
        </Modal>
      )}
      {modal === "transfer" && (
        <Modal title="Transfer asset" onClose={() => setModal(null)}>
          <select className="mb-3 w-full rounded border px-3 py-2" onChange={(e) => setForm({ employee_id: e.target.value })}>
            <option value="">Select employee</option>
            {employees.map((e) => (
              <option key={e.id} value={e.id}>
                {e.employee_code} — {e.name}
              </option>
            ))}
          </select>
          <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white" onClick={() => postAction(`/assets/${asset.id}/transfer/`, form)}>
            Transfer
          </button>
        </Modal>
      )}
      {modal === "return" && (
        <Modal title="Return asset" onClose={() => setModal(null)}>
          <textarea className="mb-3 w-full rounded border px-3 py-2" placeholder="Remarks" onChange={(e) => setForm({ remarks: e.target.value })} />
          <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white" onClick={() => postAction(`/assets/${asset.id}/return/`, form)}>
            Confirm return
          </button>
        </Modal>
      )}
      {modal === "issue" && (
        <Modal title="Report problem" onClose={() => setModal(null)}>
          <form
            onSubmit={(e: FormEvent) => {
              e.preventDefault();
              postAction("/issues/", {
                asset: asset.id,
                issue_type: form.issue_type || "HARDWARE",
                title: form.title,
                description: form.description,
                priority: form.priority || "MEDIUM",
                warranty_claim: form.warranty_claim === "true",
              });
            }}
            className="space-y-2"
          >
            <select className="w-full rounded border px-3 py-2" onChange={(e) => setForm((f) => ({ ...f, issue_type: e.target.value }))}>
              {["HARDWARE", "SOFTWARE", "NETWORK", "PHYSICAL_DAMAGE", "PERFORMANCE", "OTHER"].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
            <input required className="w-full rounded border px-3 py-2" placeholder="Title" onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
            <textarea required className="w-full rounded border px-3 py-2" placeholder="Description" onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
            <select className="w-full rounded border px-3 py-2" onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
              {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
            {asset.warranty_status && asset.warranty_status !== "EXPIRED" && (
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" onChange={(e) => setForm((f) => ({ ...f, warranty_claim: String(e.target.checked) }))} />
                Warranty claim
              </label>
            )}
            <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white">Submit</button>
          </form>
        </Modal>
      )}
      {modal === "repair" && (
        <Modal title="Start repair" onClose={() => setModal(null)}>
          <p className="mb-2 text-sm text-slate-600">Creates a repair from the latest open issue, or report an issue first.</p>
          <button
            className="rounded bg-blue-600 px-3 py-2 text-sm text-white"
            onClick={async () => {
              try {
                const issues = await api.get(`/issues/?asset=${asset.id}&status=OPEN`);
                const first = issues.data.results?.[0];
                if (!first) {
                  toast("No open issue. Report a problem first.", "error");
                  return;
                }
                await api.post(`/issues/${first.id}/start_repair/`, { repair_type: "HARDWARE" });
                toast("Repair started", "success");
                setModal(null);
                load();
              } catch (e) {
                toast(apiMessage(e), "error");
              }
            }}
          >
            Start repair from open issue
          </button>
        </Modal>
      )}
      {modal === "replace" && (
        <Modal title="Replace asset" onClose={() => setModal(null)}>
          <form
            className="space-y-2"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api.post("/replacements/", {
                  old_asset: asset.id,
                  new_asset: form.new_asset,
                  replacement_date: form.replacement_date || new Date().toISOString().slice(0, 10),
                  reason: form.reason,
                  remarks: form.remarks || "",
                });
                toast("Replacement recorded", "success");
                setModal(null);
                load();
              } catch (err) {
                toast(apiMessage(err), "error");
              }
            }}
          >
            <input className="w-full rounded border px-3 py-2" placeholder="New asset ID" onChange={(e) => setForm((f) => ({ ...f, new_asset: e.target.value }))} required />
            <input type="date" className="w-full rounded border px-3 py-2" onChange={(e) => setForm((f) => ({ ...f, replacement_date: e.target.value }))} />
            <textarea className="w-full rounded border px-3 py-2" placeholder="Reason" required onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))} />
            <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white">Replace</button>
          </form>
        </Modal>
      )}
      {confirmDispose && (
        <ConfirmDialog
          title="Dispose asset?"
          message="Disposed assets cannot be assigned again."
          onCancel={() => setConfirmDispose(false)}
          onConfirm={async () => {
            try {
              await api.post(`/assets/${asset.id}/status/`, { status: "DISPOSED" });
              toast("Asset disposed", "success");
              setConfirmDispose(false);
              load();
            } catch (e) {
              toast(apiMessage(e), "error");
            }
          }}
        />
      )}
    </div>
  );
}
