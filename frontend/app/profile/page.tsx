"use client";

import { useAuth } from "@/features/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { User as UserIcon, LogOut, Target, Award, Calendar, Clock } from "lucide-react";

export default function ProfilePage() {
  const { user, logout } = useAuth();

  return (
    <AppShell>
      {user && (
        <div className="space-y-5">
          <div className="flex items-center gap-2 px-1">
            <UserIcon className="w-4 h-4 text-cyan-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              Student Profile
            </h1>
          </div>

          {/* User ID / Identity Card */}
          <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-lg shadow-md">
                {user.first_name.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-100">
                  {user.first_name} {user.last_name || ""}
                </h2>
                <p className="text-xs text-slate-400">
                  {user.username ? `@${user.username}` : `Telegram ID: ${user.telegram_id}`}
                </p>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs">
              <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 text-[10px] block">Level</span>
                <span className="font-semibold text-slate-200">Level {user.level}</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 text-[10px] block">Total XP</span>
                <span className="font-semibold text-slate-200">{user.xp} XP</span>
              </div>
            </div>
          </Card>

          {/* Learning Settings & Target */}
          <Card className="p-4 bg-slate-900/80 border-slate-800 space-y-3 text-xs">
            <h3 className="text-xs uppercase tracking-wider font-semibold text-slate-400">
              Curriculum Goals
            </h3>

            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/60">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-blue-400" />
                  <span className="text-slate-300">Target SAT Score</span>
                </div>
                <span className="font-bold text-cyan-400">{user.profile?.target_score || 1400}+</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/60">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-400" />
                  <span className="text-slate-300">Daily Goal</span>
                </div>
                <span className="font-medium text-slate-200">{user.profile?.daily_goal_minutes || 30} min/day</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/60">
                <div className="flex items-center gap-2">
                  <Award className="w-4 h-4 text-amber-400" />
                  <span className="text-slate-300">Diagnostic Status</span>
                </div>
                <span className="capitalize px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                  {user.profile?.diagnostic_status.replace("_", " ") || "Not started"}
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/60">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-purple-400" />
                  <span className="text-slate-300">Study Plan</span>
                </div>
                <span className="font-medium text-slate-300">{user.profile?.study_goal || "Score 1400+ in 4 months"}</span>
              </div>
            </div>
          </Card>

          {/* Sign Out Action */}
          <div className="pt-2">
            <Button
              variant="outline"
              size="md"
              className="w-full text-rose-400 border-rose-900/60 hover:bg-rose-950/40 hover:text-rose-300"
              onClick={() => logout()}
            >
              <LogOut className="w-4 h-4 mr-2" />
              <span>Sign out</span>
            </Button>
          </div>
        </div>
      )}
    </AppShell>
  );
}
