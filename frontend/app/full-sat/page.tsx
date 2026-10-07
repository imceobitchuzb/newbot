"use client";

import Link from "next/link";
import { Clock, ArrowLeft, ShieldAlert } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function FullSatPage() {
  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-purple-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              Full SAT Exam Simulation
            </h1>
          </div>
          <Link href="/" className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        <Card variant="gradient" className="p-5 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-purple-400 font-semibold">Digital SAT Simulation</span>
            <span className="text-slate-400">134 Minutes Total</span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Full-length timed exam simulation replicating Bluebook test structure: Reading & Writing (2 modules of 27 questions each, 32 min each) followed by Math (2 modules of 22 questions each, 35 min each) with multistage adaptive routing.
          </p>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1.5">
            <div className="flex justify-between">
              <span className="text-slate-400">Module 1 Routing:</span>
              <span className="text-slate-200 font-medium">Standard mixed difficulty</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Module 2 Routing:</span>
              <span className="text-cyan-400 font-medium">Adaptive (Easy vs Hard)</span>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
            <ShieldAlert className="w-4 h-4" />
            <span>Simulation Readiness</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Full simulation tests will unlock in Month 4 (Phase 11) after mastering individual domain foundations.
          </p>

          <Button disabled variant="primary" size="md" className="w-full">
            <span>Unlock Full Simulation (Phase 11)</span>
          </Button>
        </Card>
      </div>
    </AppShell>
  );
}
