"use client";

import Link from "next/link";
import { Target, Calculator, BookOpen, AlertTriangle, RotateCcw, ArrowRight } from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function PracticePage() {
  const { user } = useAuth();
  const diagnosticStatus = user?.profile?.diagnostic_status || "not_started";

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center gap-2 px-1">
          <Target className="w-4 h-4 text-cyan-400" />
          <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
            Adaptive Practice
          </h1>
        </div>

        {/* Diagnostic Banner */}
        <Card variant="gradient" className="p-4 space-y-3">
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold">
            <span>Adaptive Engine Calibration</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Adaptive practice will become your main training loop. The algorithm routes questions based on your Item Response Theory (IRT) ability rating.
          </p>
          {diagnosticStatus === "not_started" && (
            <div className="pt-1">
              <Link href="/diagnostic">
                <Button size="sm" className="w-full">
                  <span>First: Complete Diagnostic</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </Link>
            </div>
          )}
        </Card>

        {/* Practice Modes */}
        <div className="space-y-2.5">
          <h2 className="text-xs uppercase tracking-wider text-slate-400 font-semibold px-1">
            Practice Modes
          </h2>

          <div className="grid grid-cols-1 gap-2.5">
            <Card className="p-3.5 bg-slate-900/60 border-slate-800 flex items-center justify-between opacity-80">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-blue-600/15 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Calculator className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Math Practice</h3>
                  <p className="text-[11px] text-slate-400">Targeted drills across 4 math domains</p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                Phase 5
              </span>
            </Card>

            <Card className="p-3.5 bg-slate-900/60 border-slate-800 flex items-center justify-between opacity-80">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-600/15 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Reading & Writing</h3>
                  <p className="text-[11px] text-slate-400">Passage comprehension & grammar rules</p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                Phase 6
              </span>
            </Card>

            <Card className="p-3.5 bg-slate-900/60 border-slate-800 flex items-center justify-between opacity-80">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-amber-600/15 border border-amber-500/20 flex items-center justify-center text-amber-400">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Weak Topics Drill</h3>
                  <p className="text-[11px] text-slate-400">Targeted remediation on detected gaps</p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                Phase 8
              </span>
            </Card>

            <Card className="p-3.5 bg-slate-900/60 border-slate-800 flex items-center justify-between opacity-80">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-purple-600/15 border border-purple-500/20 flex items-center justify-center text-purple-400">
                  <RotateCcw className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Mistake Review</h3>
                  <p className="text-[11px] text-slate-400">Spaced repetition on previous errors</p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                Phase 7
              </span>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
