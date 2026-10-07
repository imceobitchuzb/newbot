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
import {
  getTelegramInitData,
  isTelegramWebAppAvailable,
  initTelegramWebApp,
} from "@/lib/telegram";
import { User } from "@/types/user";

export type AuthStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated"
  | "error"
  | "telegram_required";

export type AuthErrorCategory =
  | "none"
  | "auth_failed"
  | "server_unavailable"
  | "database_error";

interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  error: string | null;
  errorCategory: AuthErrorCategory;
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
  const [errorCategory, setErrorCategory] = useState<AuthErrorCategory>("none");

  const initAuth = useCallback(async () => {
    setStatus("loading");
    setError(null);
    setErrorCategory("none");

    // 1. Check if we already have a valid JWT token in local storage
    if (authService.hasToken()) {
      try {
        const existingUser = await authService.getCurrentUser();
        if (existingUser) {
          setUser(existingUser);
          setStatus("authenticated");
          return;
        }
      } catch (err) {
        authService.logout();
      }
    }

    // 2. If in Telegram environment with initData, authenticate automatically
    initTelegramWebApp();
    const isTg = isTelegramWebAppAvailable();
    const initData = getTelegramInitData();

    if (isTg && initData) {
      try {
        const authenticatedUser = await authService.authenticateWithTelegram();
        setUser(authenticatedUser);
        setStatus("authenticated");
        return;
      } catch (err: any) {
        console.warn("Telegram authentication attempt failed:", err);
        if (err?.status === 401 || err?.status === 403 || err?.isAuthError) {
          setErrorCategory("auth_failed");
          setError("Не удалось авторизоваться через Telegram. Пожалуйста, запустите приложение через бота @jfsjf2ijridjbot.");
        } else if (err?.isNetworkError || err?.status === 502 || err?.status === 503 || err?.status === 504) {
          setErrorCategory("server_unavailable");
          setError("Сервер временно недоступен. Проверьте интернет-соединение или повторите попытку.");
        } else {
          setErrorCategory("auth_failed");
          setError(err?.message || "Не удалось загрузить профиль через Telegram.");
        }
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
    setErrorCategory("none");
    try {
      const authUser = await authService.authenticateWithTelegram();
      setUser(authUser);
      setStatus("authenticated");
    } catch (err: any) {
      if (err?.status === 401 || err?.status === 403 || err?.isAuthError) {
        setErrorCategory("auth_failed");
        setError("Не удалось войти через Telegram. Попробуйте перезапустить бота.");
      } else {
        setErrorCategory("server_unavailable");
        setError("Сервер временно недоступен. Попробуйте еще раз.");
      }
      setStatus("error");
    }
  };

  const loginDev = async () => {
    setStatus("loading");
    setError(null);
    setErrorCategory("none");
    try {
      const authUser = await authService.authenticateDev();
      setUser(authUser);
      setStatus("authenticated");
    } catch (err: any) {
      setError(err.message || "Dev login failed");
      setErrorCategory("server_unavailable");
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
        errorCategory,
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
