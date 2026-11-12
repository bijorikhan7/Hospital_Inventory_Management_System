import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../api/client";
import { Badge } from "../components/Badge";

export function History() {
  const [params] = useSearchParams();
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    const asset = params.get("asset");
    const url = asset ? `/history/?asset=${asset}` : "/history/";
    api.get(url).then((r) => setRows(r.data.results));
  }, [params]);
  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Asset History</h1>
      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-3 py-2">When</th>
              <th className="px-3 py-2">Asset</th>
              <th className="px-3 py-2">Action</th>
              <th className="px-3 py-2">Description</th>
              <th className="px-3 py-2">By</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((h) => (
              <tr key={h.id} className="border-t">
                <td className="px-3 py-2">{new Date(h.created_at).toLocaleString()}</td>
                <td className="px-3 py-2">{h.asset}</td>
                <td className="px-3 py-2">
                  <Badge value={h.action} />
                </td>
                <td className="px-3 py-2">{h.description}</td>
                <td className="px-3 py-2">{h.performed_by_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
