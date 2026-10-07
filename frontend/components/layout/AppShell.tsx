"use client";

import { ReactNode } from "react";
import { Terminal, User as UserIcon, AlertCircle, RefreshCw } from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { Header } from "@/components/layout/Header";
import { BottomNav } from "@/components/layout/BottomNav";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

export interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { user, status, error, errorCategory, loginDev, loginWithTelegram } = useAuth();

  const getErrorTitle = () => {
    switch (errorCategory) {
      case "auth_failed":
        return "Не удалось войти через Telegram";
      case "server_unavailable":
        return "Сервер временно недоступен";
      case "database_error":
        return "Сервис временно недоступен";
      default:
        return "Не удалось загрузить профиль";
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white relative">
      {/* Ambient background glows */}
      <div className="fixed -top-40 -left-40 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed top-1/3 -right-40 w-80 h-80 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Mobile-first container */}
      <div className="w-full max-w-md mx-auto flex-1 flex flex-col relative z-10 border-x border-slate-900 shadow-2xl">
        <Header />

        <main className="flex-1 p-4 pb-24 overflow-y-auto">
          {/* 1. Loading Skeleton */}
          {status === "loading" && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-center gap-2 py-2 text-xs text-blue-400 font-medium">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Загрузка профиля...</span>
              </div>
              <Skeleton className="h-40 w-full rounded-2xl" />
              <div className="grid grid-cols-2 gap-2.5">
                <Skeleton className="h-20 rounded-xl" />
                <Skeleton className="h-20 rounded-xl" />
              </div>
              <Skeleton className="h-24 w-full rounded-xl" />
              <Skeleton className="h-24 w-full rounded-xl" />
            </div>
          )}

          {/* 2. Development Browser Mode Notice */}
          {status === "telegram_required" && !user && (
            <div className="pt-4 space-y-4">
              <Card variant="elevated" className="border-amber-500/30 p-5 space-y-3">
                <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
                  <Terminal className="w-4 h-4" />
                  <span>Development Browser Mode</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Telegram WebApp HMAC-SHA256 authentication is active. To explore and test the dashboard outside Telegram, click below to connect with a simulated dev session.
                </p>
                <Button
                  variant="amber"
                  size="md"
                  className="w-full"
                  onClick={() => loginDev()}
                >
                  <UserIcon className="w-4 h-4 mr-1.5" />
                  <span>Connect as Dev Student</span>
                </Button>
              </Card>
            </div>
          )}

          {/* 3. Authentication Error Notice */}
          {status === "error" && (
            <div className="pt-4 space-y-4">
              <Card className="border-rose-800 bg-rose-950/30 p-5 space-y-3">
                <div className="flex items-center gap-2 text-rose-400 text-xs font-semibold">
                  <AlertCircle className="w-4 h-4" />
                  <span>{getErrorTitle()}</span>
                </div>
                <p className="text-xs text-rose-200 leading-relaxed">
                  {error || "Не удалось соединиться с сервисом авторизации SAT MASTER."}
                </p>
                <div className="flex flex-col sm:flex-row gap-2 pt-1">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    onClick={() => {
                      loginWithTelegram().catch(() => loginDev());
                    }}
                  >
                    <RefreshCw className="w-3.5 h-3.5 mr-1" />
                    <span>Повторить попытку</span>
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="flex-1"
                    onClick={() => loginDev()}
                  >
                    <UserIcon className="w-3.5 h-3.5 mr-1" />
                    <span>Войти как гость</span>
                  </Button>
                </div>
              </Card>
            </div>
          )}

          {/* 4. Authenticated View */}
          {(status === "authenticated" || user) && children}
        </main>

        <BottomNav />
      </div>
    </div>
  );
}
