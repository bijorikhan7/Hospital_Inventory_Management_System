import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import api from "../api/client";
import type { Role, User } from "../types";

type AuthState = {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
};

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me/")
      .then((res) => {
        const data = Array.isArray(res.data) ? res.data[0] : res.data.results?.[0] ?? res.data;
        setUser(data);
      })
      .catch(() => {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      async login(username, password) {
        const { data } = await api.post("/auth/login/", { username, password });
        localStorage.setItem("access", data.access);
        localStorage.setItem("refresh", data.refresh);
        setUser(data.user);
      },
      logout() {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        setUser(null);
      },
      hasRole: (...roles: Role[]) => (user ? roles.includes(user.role) : false),
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
