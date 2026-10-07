"use client";

import Link from "next/link";
import { ClipboardCheck, Clock, Calculator, BookOpen, AlertCircle, ArrowLeft } from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function DiagnosticPage() {
  const { user } = useAuth();
  const diagnosticStatus = user?.profile?.diagnostic_status || "not_started";

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="w-4 h-4 text-cyan-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              SAT Diagnostic Test
            </h1>
          </div>
          <Link href="/" className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        {/* Overview Banner */}
        <Card variant="gradient" className="p-5 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-blue-400 font-semibold">Baseline Calibration</span>
            <span className="px-2 py-0.5 rounded bg-blue-500/15 border border-blue-500/30 text-blue-300 text-[10px] font-semibold">
              45 Minutes
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            The diagnostic assesses your foundational readiness across Math and Reading & Writing. It establishes your initial ability ratings ($\theta$) and generates your custom remediation path towards 1400+.
          </p>

          <div className="pt-2 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center gap-2">
              <Calculator className="w-4 h-4 text-blue-400" />
              <div>
                <p className="font-semibold text-slate-200">Math</p>
                <p className="text-[10px] text-slate-400">15 Questions</p>
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              <div>
                <p className="font-semibold text-slate-200">Reading & Writing</p>
                <p className="text-[10px] text-slate-400">15 Questions</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Test Engine Status Card */}
        <Card className="p-4 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
            <AlertCircle className="w-4 h-4" />
            <span>Engine Preparation</span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Diagnostic test questions and evaluation routing will be wired in Phase 4 (Question Engine) and Phase 11.
          </p>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs space-y-1">
            <div className="flex justify-between text-slate-400">
              <span>Your Status:</span>
              <span className="font-semibold text-slate-200 capitalize">
                {diagnosticStatus.replace("_", " ")}
              </span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Target:</span>
              <span className="font-semibold text-cyan-400">
                {user?.profile?.target_score || 1400}+
              </span>
            </div>
          </div>

          <Button disabled variant="primary" size="md" className="w-full">
            <span>Start Calibrated Test (Phase 4)</span>
          </Button>
        </Card>
      </div>
    </AppShell>
  );
}
