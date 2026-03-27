import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";
import { loginApi, registerApi } from "../api/auth";

interface AuthContextType {
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token")
  );

  const login = async (email: string, password: string) => {
    const data = await loginApi(email, password);
    setToken(data.access_token);
    localStorage.setItem("token", data.access_token);
  };

  const register = async (email: string, password: string) => {
    await registerApi(email, password);
    await login(email, password);
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider value={{ token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth 必須在 AuthProvider 內使用");
  return ctx;
};