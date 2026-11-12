import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(apiMessage(err, "Invalid credentials"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm rounded-xl bg-white p-6 shadow">
        <h1 className="mb-1 text-xl font-semibold">IT Asset Management</h1>
        <p className="mb-5 text-sm text-slate-500">Sign in to continue</p>
        {error && <div className="mb-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</div>}
        <label className="mb-3 block text-sm">
          Username
          <input className="mt-1 w-full rounded border px-3 py-2" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </label>
        <label className="mb-4 block text-sm">
          Password
          <input type="password" className="mt-1 w-full rounded border px-3 py-2" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        <button disabled={busy} className="w-full rounded bg-blue-600 py-2 text-white disabled:opacity-60">
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
