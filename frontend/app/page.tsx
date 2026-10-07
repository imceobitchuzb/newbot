"use client";

import { useEffect, useState } from "react";
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
} from "lucide-react";
import { api } from "@/lib/api";
import { getTelegramUser, isTelegramWebAppAvailable } from "@/lib/telegram";

export default function Home() {
  const [isTelegram, setIsTelegram] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    const available = isTelegramWebAppAvailable();
    setIsTelegram(available);
    if (available) {
      const user = getTelegramUser();
      if (user?.first_name) {
        setUserName(user.first_name);
      }
    }
  }, []);

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
      {/* Background glow effects */}
      <div className="absolute -top-32 -left-32 w-72 h-72 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 -right-32 w-72 h-72 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header bar */}
      <header className="flex items-center justify-between py-2 border-b border-slate-800/80 mb-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
            S
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-wider text-slate-200">
              SAT MASTER
            </h1>
            <p className="text-[10px] text-slate-400">Digital SAT System</p>
          </div>
        </div>

        {/* Live System Health Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-900 border border-slate-800">
          {isHealthLoading ? (
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          ) : isHealthError ? (
            <>
              <AlertCircle className="w-3 h-3 text-rose-500" />
              <span className="text-rose-400">API Offline</span>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">API Active</span>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="flex-1 flex flex-col justify-center space-y-6">
        {/* Score Target Hero Card */}
        <div className="rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-900/40 border border-slate-800 p-5 shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              {userName ? `Welcome, ${userName}` : "Target Trajectory"}
            </span>
            <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px] font-semibold">
              4 Months Plan
            </span>
          </div>

          <div className="flex items-baseline justify-between mt-3 mb-4">
            <div>
              <p className="text-[11px] uppercase tracking-wider text-slate-400">
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
                1400+
              </p>
              <p className="text-[10px] text-slate-400">Target Range</p>
            </div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Your personal AI-driven SAT preparation pipeline. Systematic diagnosis, gap identification, Desmos mastery, and targeted spaced practice.
          </p>
        </div>

        {/* Modules Roadmap Grid */}
        <div className="space-y-3">
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

        {/* Primary Action Button */}
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

      {/* Footer Info */}
      <footer className="pt-6 pb-2 border-t border-slate-800/60 mt-6 flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5">
          <Smartphone className="w-3.5 h-3.5" />
          <span>{isTelegram ? "Telegram Mini App" : "Standard Browser"}</span>
        </div>
        <div className="flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
          <span>v0.1.0 Foundation</span>
        </div>
      </footer>
    </main>
  );
}
