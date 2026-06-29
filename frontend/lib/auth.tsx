"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  getMe,
  login as apiLogin,
  registerClient as apiRegisterClient,
  registerSaloon as apiRegisterSaloon,
  setAuthToken,
} from "./api";
import type { AuthResult, User } from "./bookingTypes";

const TOKEN_KEY = "cutpoint_token";

interface AuthState {
  user: User | null;
  salonId: number | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  registerClient: (body: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
  }) => Promise<User>;
  registerSaloon: (body: unknown) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [salonId, setSalonId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore a session from a stored token on first load.
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }
    setAuthToken(token);
    getMe()
      .then((me) => {
        setUser(me.user);
        setSalonId(me.salon_id);
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setAuthToken(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const apply = useCallback((res: AuthResult): User => {
    localStorage.setItem(TOKEN_KEY, res.access_token);
    setAuthToken(res.access_token);
    setUser(res.user);
    setSalonId(res.salon_id);
    return res.user;
  }, []);

  const login = useCallback(
    async (email: string, password: string) => apply(await apiLogin(email, password)),
    [apply],
  );
  const registerClient = useCallback(
    async (body: { email: string; password: string; full_name: string; phone?: string }) =>
      apply(await apiRegisterClient(body)),
    [apply],
  );
  const registerSaloon = useCallback(
    async (body: unknown) => apply(await apiRegisterSaloon(body)),
    [apply],
  );
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setUser(null);
    setSalonId(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, salonId, loading, login, registerClient, registerSaloon, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
