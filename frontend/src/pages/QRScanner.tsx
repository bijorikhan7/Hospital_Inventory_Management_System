import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Html5Qrcode } from "html5-qrcode";
import api, { apiMessage } from "../api/client";
import { useToast } from "../components/Toast";

export function QRScanner() {
  const nav = useNavigate();
  const toast = useToast();
  const [manual, setManual] = useState("");
  const [camError, setCamError] = useState("");
  const started = useRef(false);

  useEffect(() => {
    const elId = "qr-reader";
    const scanner = new Html5Qrcode(elId);
    Html5Qrcode.getCameras()
      .then((cams) => {
        if (!cams.length) {
          setCamError("No camera found. Use manual asset code search.");
          return;
        }
        started.current = true;
        return scanner.start(
          { facingMode: "environment" },
          { fps: 8, qrbox: 220 },
          (decoded) => {
            const code = extractCode(decoded);
            if (code) {
              scanner.stop().catch(() => undefined);
              nav(`/assets/${code}`);
            }
          },
          () => undefined,
        );
      })
      .catch(() => setCamError("Camera scanning unavailable. Use manual search."));
    return () => {
      if (started.current) scanner.stop().catch(() => undefined);
    };
  }, [nav]);

  async function search() {
    try {
      const { data } = await api.get(`/assets/by-code/${manual.trim().toUpperCase()}/`);
      nav(`/assets/${data.asset_code}`);
    } catch (e) {
      toast(apiMessage(e, "Asset not found"), "error");
    }
  }

  return (
    <div className="max-w-lg">
      <h1 className="mb-4 text-2xl font-semibold">QR Scanner</h1>
      <div id="qr-reader" className="mb-4 overflow-hidden rounded-lg border bg-black" />
      {camError && <p className="mb-3 text-sm text-amber-700">{camError}</p>}
      <div className="flex gap-2">
        <input className="flex-1 rounded border px-3 py-2" placeholder="IT-LAP-0001" value={manual} onChange={(e) => setManual(e.target.value)} />
        <button className="rounded bg-blue-600 px-3 py-2 text-white" onClick={search}>
          Lookup
        </button>
      </div>
    </div>
  );
}

function extractCode(value: string): string | null {
  const match = value.match(/IT-[A-Z0-9]+-\d+/i);
  if (match) return match[0].toUpperCase();
  try {
    const url = new URL(value);
    const parts = url.pathname.split("/").filter(Boolean);
    return parts[parts.length - 1] || null;
  } catch {
    return value || null;
  }
}
