import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import api from "../api/client";

export function QRPrint() {
  const [params] = useSearchParams();
  const [items, setItems] = useState<{ asset_code: string; name: string; qr_payload: string }[]>([]);

  useEffect(() => {
    const code = params.get("code");
    if (code) {
      api.get(`/assets/by-code/${code}/`).then((r) => setItems([r.data]));
    } else {
      api.get("/assets/?page_size=50").then((r) => setItems(r.data.results));
    }
  }, [params]);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between print:hidden">
        <h1 className="text-2xl font-semibold">QR Print</h1>
        <button className="rounded bg-blue-600 px-3 py-2 text-white" onClick={() => window.print()}>
          Print
        </button>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        {items.map((a) => (
          <div key={a.asset_code} className="flex flex-col items-center rounded border bg-white p-4">
            <QRCodeSVG value={a.qr_payload || `/assets/${a.asset_code}`} size={140} />
            <div className="mt-2 font-semibold">{a.asset_code}</div>
            <div className="text-xs text-slate-500">{a.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
