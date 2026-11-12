import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Assets } from "./pages/Assets";
import { AssetDetail } from "./pages/AssetDetail";
import { AssetForm } from "./pages/AssetForm";
import { Employees } from "./pages/Employees";
import { EmployeeDetail } from "./pages/EmployeeDetail";
import { Categories } from "./pages/Categories";
import { Vendors } from "./pages/Vendors";
import { Purchases } from "./pages/Purchases";
import { Warranties } from "./pages/Warranties";
import { Issues } from "./pages/Issues";
import { Repairs } from "./pages/Repairs";
import { History } from "./pages/History";
import { QRScanner } from "./pages/QRScanner";
import { QRPrint } from "./pages/QRPrint";

function Private({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-500">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <Private>
            <Layout />
          </Private>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="assets" element={<Assets />} />
        <Route path="assets/new" element={<AssetForm />} />
        <Route path="assets/:id/edit" element={<AssetForm />} />
        <Route path="assets/:code" element={<AssetDetail />} />
        <Route path="employees" element={<Employees />} />
        <Route path="employees/:id" element={<EmployeeDetail />} />
        <Route path="categories" element={<Categories />} />
        <Route path="vendors" element={<Vendors />} />
        <Route path="purchases" element={<Purchases />} />
        <Route path="warranties" element={<Warranties />} />
        <Route path="issues" element={<Issues />} />
        <Route path="repairs" element={<Repairs />} />
        <Route path="history" element={<History />} />
        <Route path="scan" element={<QRScanner />} />
        <Route path="qr-print" element={<QRPrint />} />
      </Route>
    </Routes>
  );
}
