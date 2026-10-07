"use client";

import Link from "next/link";
import { BarChart3, Target, ArrowRight } from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function ProgressPage() {
  const { user } = useAuth();
  const diagnosticStatus = user?.profile?.diagnostic_status || "not_started";
  const targetScore = user?.profile?.target_score || 1400;

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center gap-2 px-1">
          <BarChart3 className="w-4 h-4 text-cyan-400" />
          <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
            Score & Telemetry Analytics
          </h1>
        </div>

        {/* Score Target Overview */}
        <Card variant="gradient" className="p-5 space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Score Calibration</span>
            <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-semibold text-[10px]">
              Digital SAT Scale
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
                Current Score
              </span>
              <p className={`text-xl font-bold ${diagnosticStatus === "completed" ? "text-slate-100" : "text-slate-400"}`}>
                {diagnosticStatus === "completed" && (user?.profile?.math_estimate || user?.profile?.rw_estimate)
                  ? (user.profile.math_estimate || 350) + (user.profile.rw_estimate || 350)
                  : "Not measured"}
              </p>
              <p className="text-[10px] text-slate-400 mt-1">
                {diagnosticStatus === "completed" ? "Calibrated Baseline" : "Requires Diagnostic"}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-[10px] uppercase tracking-wider text-cyan-400 block mb-1">
                Target Score
              </span>
              <p className="text-xl font-bold text-cyan-400">{targetScore}+</p>
              <p className="text-[10px] text-slate-400 mt-1">Goal Objective</p>
            </div>
          </div>

          {/* Sectional Breakdown */}
          <div className="pt-2 border-t border-slate-800 space-y-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <span className="text-slate-300">Math Section (200-800)</span>
              <span className={`font-semibold ${diagnosticStatus === "completed" && user?.profile?.math_estimate ? "text-blue-400" : "text-slate-400"}`}>
                {diagnosticStatus === "completed" && user?.profile?.math_estimate ? `~${user.profile.math_estimate}` : "Not measured"}
              </span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <span className="text-slate-300">Reading & Writing (200-800)</span>
              <span className={`font-semibold ${diagnosticStatus === "completed" && user?.profile?.rw_estimate ? "text-emerald-400" : "text-slate-400"}`}>
                {diagnosticStatus === "completed" && user?.profile?.rw_estimate ? `~${user.profile.rw_estimate}` : "Not measured"}
              </span>
            </div>
          </div>
        </Card>

        {/* Diagnostic Action Prompt */}
        {diagnosticStatus === "not_started" && (
          <Card className="p-4 bg-slate-900/70 border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
              <Target className="w-4 h-4" />
              <span>Diagnostic Required</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Score estimation, mastery radar maps, and topic strengths will generate dynamically once you complete your baseline diagnostic test.
            </p>
            <Link href="/diagnostic" className="block">
              <Button size="md" className="w-full">
                <span>Take Diagnostic</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </Card>
        )}

        {diagnosticStatus === "completed" && (
          <Card className="p-4 bg-slate-900/70 border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                <Target className="w-4 h-4" />
                <span>Baseline Calibrated</span>
              </div>
              <span className="text-[10px] text-slate-400">40 Questions Evaluated</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Your baseline diagnostic is complete. Review your comprehensive domain strengths and weak area breakdown:
            </p>
            <Link href="/diagnostic/result" className="block">
              <Button size="md" variant="secondary" className="w-full justify-center">
                <span>View Full Diagnostic Report</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
