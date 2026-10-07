"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, AlertCircle } from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { api } from "@/lib/api";

export function Header() {
  const { user } = useAuth();

  const { data: health, isLoading: isHealthLoading, isError: isHealthError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.getHealth(),
    refetchInterval: 15000,
  });

  const getInitials = (name?: string) => {
    if (!name) return "S";
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 px-4 py-2.5 flex items-center justify-between">
      {/* Brand title */}
      <Link href="/" className="flex items-center gap-2.5 group">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20 text-sm group-hover:scale-105 transition">
          S
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-semibold tracking-wider text-slate-100">
              SAT MASTER
            </span>
          </div>
          <p className="text-[10px] text-slate-400">
            {user ? `Hi, ${user.first_name}` : "Digital SAT Prep"}
          </p>
        </div>
      </Link>

      {/* Right controls: Health & Profile */}
      <div className="flex items-center gap-2">
        {/* System Health Badge */}
        <div
          title={isHealthError ? "API Offline" : "API Connected"}
          className="flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-medium bg-slate-900 border border-slate-800"
        >
          {isHealthLoading ? (
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          ) : isHealthError ? (
            <AlertCircle className="w-3 h-3 text-rose-500" />
          ) : (
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          )}
          <span className="hidden sm:inline text-slate-400">
            {isHealthError ? "Offline" : "API"}
          </span>
        </div>

        {/* Profile Avatar / Shortcut */}
        <Link
          href="/profile"
          className="flex items-center gap-1.5 p-1 rounded-full hover:bg-slate-800/60 transition active:scale-95"
          aria-label="View user profile"
        >
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.first_name}
              className="w-7 h-7 rounded-full border border-blue-500/40 object-cover"
            />
          ) : (
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow-sm">
              {getInitials(user?.first_name)}
            </div>
          )}
        </Link>
      </div>
    </header>
  );
}
