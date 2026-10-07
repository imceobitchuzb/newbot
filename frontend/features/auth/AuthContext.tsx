"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { authService } from "@/lib/auth";
import { getTelegramInitData, isTelegramWebAppAvailable } from "@/lib/telegram";
import { User } from "@/types/user";

export type AuthStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated"
  | "error"
  | "telegram_required";

interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  error: string | null;
  loginWithTelegram: () => Promise<void>;
  loginDev: () => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  const initAuth = useCallback(async () => {
    setStatus("loading");
    setError(null);

    // 1. Check if we already have a valid JWT token in local storage
    if (authService.hasToken()) {
      try {
        const existingUser = await authService.getCurrentUser();
        if (existingUser) {
          setUser(existingUser);
          setStatus("authenticated");
          return;
        }
      } catch {
        // Token invalid, clear and continue
        authService.logout();
      }
    }

    // 2. If in Telegram environment with initData, authenticate automatically
    const isTg = isTelegramWebAppAvailable();
    const initData = getTelegramInitData();

    if (isTg && initData) {
      try {
        const authenticatedUser = await authService.authenticateWithTelegram();
        setUser(authenticatedUser);
        setStatus("authenticated");
        return;
      } catch (err: any) {
        console.error("Telegram authentication failed:", err);
        setError(err.message || "Failed to authenticate with Telegram.");
        setStatus("error");
        return;
      }
    }

    // 3. Running in a standard browser outside Telegram
    setStatus("telegram_required");
  }, []);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  const loginWithTelegram = async () => {
    setStatus("loading");
    setError(null);
    try {
      const authUser = await authService.authenticateWithTelegram();
      setUser(authUser);
      setStatus("authenticated");
    } catch (err: any) {
      setError(err.message || "Authentication failed");
      setStatus("error");
    }
  };

  const loginDev = async () => {
    setStatus("loading");
    setError(null);
    try {
      const authUser = await authService.authenticateDev();
      setUser(authUser);
      setStatus("authenticated");
    } catch (err: any) {
      setError(err.message || "Dev login failed");
      setStatus("error");
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setStatus("unauthenticated");
  };

  const refreshUser = async () => {
    const freshUser = await authService.getCurrentUser();
    if (freshUser) {
      setUser(freshUser);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        status,
        error,
        loginWithTelegram,
        loginDev,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
