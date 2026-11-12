import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { apiMessage } from "../api/client";
import { Badge } from "../components/Badge";
import type { Employee, Paginated } from "../types";

export function Employees() {
  const [rows, setRows] = useState<Employee[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    api
      .get<Paginated<Employee>>("/auth/employees/")
      .then((r) => setRows(r.data.results))
      .catch((e) => setError(apiMessage(e)));
  }, []);
  if (error) return <div className="text-rose-700">{error}</div>;
  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Employees</h1>
      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-3 py-2">Code</th>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Department</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.id} className="border-t">
                <td className="px-3 py-2">
                  <Link className="text-blue-700" to={`/employees/${e.id}`}>
                    {e.employee_code}
                  </Link>
                </td>
                <td className="px-3 py-2">{e.name}</td>
                <td className="px-3 py-2">{e.department}</td>
                <td className="px-3 py-2">
                  <Badge value={e.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function EmployeeDetail() {
  const [emp, setEmp] = useState<Employee | null>(null);
  const id = window.location.pathname.split("/").pop();
  useEffect(() => {
    api.get(`/auth/employees/${id}/`).then((r) => setEmp(r.data));
  }, [id]);
  if (!emp) return <div>Loading…</div>;
  return (
    <div className="rounded-lg border bg-white p-5">
      <h1 className="text-xl font-semibold">{emp.name}</h1>
      <p className="text-sm text-slate-500">{emp.employee_code}</p>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-slate-500">Email</dt>
          <dd>{emp.email}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Department</dt>
          <dd>{emp.department}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Designation</dt>
          <dd>{emp.designation}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Location</dt>
          <dd>{emp.location}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Status</dt>
          <dd>
            <Badge value={emp.status} />
          </dd>
        </div>
      </dl>
    </div>
  );
}
