import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const nav = [
  { to: "/", label: "Dashboard", roles: ["ADMIN", "IT_STAFF", "EMPLOYEE"] },
  { to: "/assets", label: "Assets", roles: ["ADMIN", "IT_STAFF", "EMPLOYEE"] },
  { to: "/employees", label: "Employees", roles: ["ADMIN", "IT_STAFF"] },
  { to: "/categories", label: "Categories", roles: ["ADMIN", "IT_STAFF"] },
  { to: "/vendors", label: "Vendors", roles: ["ADMIN", "IT_STAFF"] },
  { to: "/purchases", label: "Purchases", roles: ["ADMIN", "IT_STAFF"] },
  { to: "/warranties", label: "Warranty", roles: ["ADMIN", "IT_STAFF", "EMPLOYEE"] },
  { to: "/issues", label: "Issues", roles: ["ADMIN", "IT_STAFF", "EMPLOYEE"] },
  { to: "/repairs", label: "Repairs", roles: ["ADMIN", "IT_STAFF"] },
  { to: "/history", label: "History", roles: ["ADMIN", "IT_STAFF"] },
  { to: "/scan", label: "QR Scanner", roles: ["ADMIN", "IT_STAFF", "EMPLOYEE"] },
  { to: "/qr-print", label: "QR Print", roles: ["ADMIN", "IT_STAFF"] },
];

export function Layout() {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 flex items-center justify-between border-b bg-white px-4 py-3">
        <div>
          <div className="text-sm font-semibold text-brand-700">Office IT Assets</div>
          <div className="text-xs text-slate-500">Inventory management</div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="hidden sm:inline text-slate-600">
            {user?.username} · {user?.role}
          </span>
          <button
            className="rounded border px-3 py-1"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Logout
          </button>
        </div>
      </header>
      <div className="flex">
        <aside className="hidden min-h-[calc(100vh-57px)] w-56 shrink-0 border-r bg-white p-3 md:block">
          <nav className="space-y-1">
            {nav
              .filter((n) => hasRole(...(n.roles as ("ADMIN" | "IT_STAFF" | "EMPLOYEE")[])))
              .map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.to === "/"}
                  className={({ isActive }) =>
                    `block rounded px-3 py-2 text-sm ${isActive ? "bg-blue-50 font-medium text-blue-700" : "text-slate-700 hover:bg-slate-50"}`
                  }
                >
                  {n.label}
                </NavLink>
              ))}
          </nav>
        </aside>
        <main className="min-w-0 flex-1 p-4 md:p-6">
          <div className="mb-4 flex gap-2 overflow-x-auto md:hidden">
            {nav
              .filter((n) => hasRole(...(n.roles as ("ADMIN" | "IT_STAFF" | "EMPLOYEE")[])))
              .map((n) => (
                <NavLink key={n.to} to={n.to} className="whitespace-nowrap rounded border bg-white px-3 py-1 text-xs">
                  {n.label}
                </NavLink>
              ))}
          </div>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
