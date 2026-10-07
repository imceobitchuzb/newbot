"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Sparkles,
  ArrowRight,
  Calculator,
  BookOpen,
  LineChart,
  CheckCircle2,
  AlertCircle,
  Smartphone,
  ShieldCheck,
  User as UserIcon,
  LogOut,
  Terminal,
  Loader2,
} from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { api } from "@/lib/api";
import { isTelegramWebAppAvailable } from "@/lib/telegram";

export default function Home() {
  const { user, status, error, loginDev, logout } = useAuth();
  const isTgAvailable = isTelegramWebAppAvailable();

  const {
    data: health,
    isLoading: isHealthLoading,
    isError: isHealthError,
  } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.getHealth(),
    refetchInterval: 10000,
  });

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-4 max-w-md mx-auto relative overflow-hidden font-sans">
      {/* Background ambient lighting */}
      <div className="absolute -top-32 -left-32 w-72 h-72 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 -right-32 w-72 h-72 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header bar */}
      <header className="flex items-center justify-between py-2 border-b border-slate-800/80 mb-5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20 text-sm">
            S
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-wider text-slate-200">
              SAT MASTER
            </h1>
            <p className="text-[10px] text-slate-400">Digital SAT System</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {user && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-950/60 border border-blue-800/60 text-[10px] font-medium text-blue-300">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              Lvl {user.level}
            </div>
          )}

          {/* System Health indicator */}
          <div className="flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-medium bg-slate-900 border border-slate-800">
            {isHealthLoading ? (
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            ) : isHealthError ? (
              <>
                <AlertCircle className="w-3 h-3 text-rose-500" />
                <span className="text-rose-400">Offline</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400">Active</span>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Body */}
      <section className="flex-1 flex flex-col justify-center space-y-5">
        {/* Loading state */}
        {status === "loading" && (
          <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-8 text-center space-y-3">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
            <p className="text-xs text-slate-400">Verifying Telegram credentials...</p>
          </div>
        )}

        {/* Development Browser Mode (when outside Telegram) */}
        {status === "telegram_required" && (
          <div className="rounded-2xl bg-slate-900/90 border border-amber-500/30 p-5 space-y-4 shadow-xl">
            <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
              <Terminal className="w-4 h-4" />
              <span>Development Browser Mode</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Telegram WebApp authentication is active on the backend. Because you are testing directly in a desktop browser outside of Telegram, you can simulate a student session below.
            </p>
            <button
              onClick={() => loginDev()}
              type="button"
              className="w-full py-2.5 px-3 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-semibold transition flex items-center justify-center gap-2"
            >
              <UserIcon className="w-3.5 h-3.5" />
              <span>Connect as Dev Student</span>
            </button>
          </div>
        )}

        {/* Error state */}
        {status === "error" && (
          <div className="rounded-2xl bg-rose-950/40 border border-rose-800 p-5 space-y-3">
            <div className="flex items-center gap-2 text-rose-400 text-xs font-semibold">
              <AlertCircle className="w-4 h-4" />
              <span>Authentication Error</span>
            </div>
            <p className="text-xs text-rose-300">{error || "Could not authenticate session."}</p>
            <button
              onClick={() => loginDev()}
              type="button"
              className="py-1.5 px-3 rounded-lg bg-rose-900/40 text-rose-200 text-xs font-medium border border-rose-800"
            >
              Retry
            </button>
          </div>
        )}

        {/* Authenticated Student Card */}
        {user && (
          <div className="rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-900/50 border border-slate-800 p-5 shadow-xl relative overflow-hidden">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-medium text-slate-200">
                  Hi, {user.first_name}
                  {user.username ? ` (@${user.username})` : ""}
                </span>
              </div>
              <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px] font-semibold">
                4-Month Path
              </span>
            </div>

            <div className="flex items-baseline justify-between mt-3 mb-4">
              <div>
                <p className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
                  Baseline Diagnostic
                </p>
                <p className="text-3xl font-extrabold text-slate-300">700</p>
                <p className="text-[10px] text-slate-500">M: ~360 | RW: ~340</p>
              </div>

              <div className="text-slate-500 font-light text-2xl">➔</div>

              <div className="text-right">
                <p className="text-[11px] uppercase tracking-wider text-cyan-400 font-medium">
                  Goal Score
                </p>
                <p className="text-3xl font-extrabold bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                  {user.profile?.target_score || 1400}+
                </p>
                <p className="text-[10px] text-slate-400">Target Range</p>
              </div>
            </div>

            {/* Diagnostic status badge - Real, not fake! */}
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-400">Diagnostic Status:</span>
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] font-medium capitalize">
                {user.profile?.diagnostic_status.replace("_", " ") || "Not started"}
              </span>
            </div>
          </div>
        )}

        {/* Training Modules Cards */}
        <div className="space-y-2.5">
          <h2 className="text-xs uppercase tracking-wider text-slate-400 font-semibold px-1">
            Training Modules
          </h2>

          <div className="grid grid-cols-1 gap-2.5">
            {/* Math Card */}
            <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex items-center justify-between hover:border-slate-700 transition">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-blue-600/15 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Calculator className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Math</h3>
                  <p className="text-[11px] text-slate-400">
                    Algebra, Advanced Math, Problem Solving, Geometry
                  </p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                Foundations
              </span>
            </div>

            {/* Reading & Writing Card */}
            <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex items-center justify-between hover:border-slate-700 transition">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-emerald-600/15 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">
                    Reading & Writing
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Craft & Structure, Information, Conventions
                  </p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                Conventions
              </span>
            </div>

            {/* Desmos Lab Card */}
            <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex items-center justify-between hover:border-slate-700 transition">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-cyan-600/15 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                  <LineChart className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">
                    Desmos Lab
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Graphing Tricks, Regressions, Intersections & Shortcuts
                  </p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                Techniques
              </span>
            </div>
          </div>
        </div>

        {/* Action button */}
        <div className="pt-2">
          <button
            type="button"
            className="w-full py-3.5 px-4 rounded-xl font-semibold text-sm bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg shadow-blue-600/20 flex items-center justify-center gap-2 active:scale-[0.99] transition"
          >
            <span>Start studying</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* Footer bar */}
      <footer className="pt-5 pb-2 border-t border-slate-800/60 mt-5 flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5">
          <Smartphone className="w-3.5 h-3.5" />
          <span>{isTgAvailable ? "Telegram Mini App" : "Standard Browser"}</span>
        </div>

        {user ? (
          <button
            onClick={() => logout()}
            type="button"
            className="flex items-center gap-1 text-slate-500 hover:text-slate-300 transition"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign out</span>
          </button>
        ) : (
          <div className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            <span>v0.2.0 Auth</span>
          </div>
        )}
      </footer>
    </main>
  );
}
