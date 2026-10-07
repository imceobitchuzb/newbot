"use client";

import { Suspense, useEffect, useState } from "react";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Award,
  BookOpen,
  Calculator,
  CheckCircle2,
  Clock,
  Compass,
  RotateCcw,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import { DiagnosticResult } from "@/types/diagnostic";

function DiagnosticResultContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id") || undefined;
  const { user } = useAuth();


  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchResult() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getDiagnosticResult(sessionId);
        setResult(data);
      } catch (err: any) {
        console.error("Failed to load diagnostic results:", err);
        setError(err?.message || "No completed diagnostic results found.");
      } finally {
        setLoading(false);
      }
    }
    fetchResult();
  }, [sessionId]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins === 0) return `${secs}s`;
    return `${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <AppShell>
        <div className="py-20 text-center space-y-3">
          <div className="w-8 h-8 mx-auto border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400">Loading diagnostic calibration report...</p>
        </div>
      </AppShell>
    );
  }

  if (error || !result) {
    return (
      <AppShell>
        <div className="space-y-4 max-w-lg mx-auto py-8">
          <Card className="p-6 text-center space-y-4 bg-slate-900 border-slate-800">
            <div className="w-12 h-12 mx-auto rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Compass className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">No Diagnostic Results Found</h2>
              <p className="text-xs text-slate-400 mt-1">
                {error || "You haven't completed a diagnostic assessment yet."}
              </p>
            </div>
            <Link href="/diagnostic">
              <Button variant="primary" size="md" className="w-full justify-center">
                <span>Start Diagnostic Assessment</span>
              </Button>
            </Link>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-5 max-w-2xl mx-auto pb-10">
        {/* Header */}
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4 text-cyan-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              Diagnostic Report
            </h1>
          </div>
          <Link href="/" className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        {/* Hero Score Estimate Card */}
        <Card variant="gradient" className="p-6 space-y-5 text-center sm:text-left">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 bg-cyan-500/10 px-2.5 py-0.5 rounded-full border border-cyan-500/20">
                Calibrated SAT Baseline
              </span>
              <h2 className="text-xl font-bold text-slate-100 mt-1">
                Estimated SAT Score Range
              </h2>
            </div>
            <div className="flex items-center justify-center sm:justify-start gap-1.5 text-xs text-slate-400">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Completed in {formatDuration(result.duration_seconds)}</span>
            </div>
          </div>

          {/* Primary Score Numbers */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-1">
            <div>
              <div className="text-4xl sm:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400 font-mono tracking-tight">
                {result.estimated_total_low} – {result.estimated_total_high}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Target Goal: <span className="text-cyan-400 font-semibold">{user?.profile?.target_score || 1400}+</span>
              </p>
            </div>

            <div className="text-right space-y-1">
              <div className="text-xs text-slate-400">Overall Accuracy</div>
              <div className="text-xl font-bold text-slate-100 font-mono">
                {Math.round(result.total_accuracy * 100)}%
              </div>
              <div className="text-[11px] text-slate-500">
                {result.math_correct + result.rw_correct} / 40 correct
              </div>
            </div>
          </div>

          {/* Section Score Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {/* Math Section */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2 text-left">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400">
                    <Calculator className="w-3.5 h-3.5" />
                  </div>
                  <span className="font-semibold text-slate-200 text-xs">Math</span>
                </div>
                <span className="text-xs font-mono font-bold text-blue-400">
                  {result.estimated_math_low} – {result.estimated_math_high}
                </span>
              </div>

              <div className="flex justify-between items-center text-[11px] text-slate-400 pt-1">
                <span>Accuracy</span>
                <span className="font-semibold text-slate-200">
                  {Math.round(result.math_accuracy * 100)}% ({result.math_correct}/{result.math_total})
                </span>
              </div>
            </div>

            {/* Reading & Writing Section */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2 text-left">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <BookOpen className="w-3.5 h-3.5" />
                  </div>
                  <span className="font-semibold text-slate-200 text-xs">Reading & Writing</span>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {result.estimated_rw_low} – {result.estimated_rw_high}
                </span>
              </div>

              <div className="flex justify-between items-center text-[11px] text-slate-400 pt-1">
                <span>Accuracy</span>
                <span className="font-semibold text-slate-200">
                  {Math.round(result.rw_accuracy * 100)}% ({result.rw_correct}/{result.rw_total})
                </span>
              </div>
            </div>
          </div>

          <div className="pt-2 text-[10px] text-slate-500 text-center sm:text-left italic">
            * Note: This score range is a proprietary SAT Master calibration estimate for study guidance, not an official College Board test score.
          </div>
        </Card>

        {/* Priority Focus Areas (Weak Domains) */}
        {result.weak_domains.length > 0 && (
          <Card className="p-5 space-y-3 bg-slate-900/90 border-slate-800">
            <div className="flex items-center gap-2 text-rose-400 text-xs font-semibold">
              <AlertTriangle className="w-4 h-4" />
              <span>Priority Areas for Growth ({result.weak_domains.length})</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              These domains showed accuracy below 60%. Focusing on these topics will yield the fastest score improvements toward your 1400+ goal:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {result.weak_domains.map((dom) => (
                <span
                  key={dom}
                  className="px-3 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-300 text-xs font-medium flex items-center gap-1.5"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                  <span>{dom.replace(/_/g, " ")}</span>
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Strengths (Strong Domains) */}
        {result.strong_domains.length > 0 && (
          <Card className="p-5 space-y-3 bg-slate-900/90 border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>Demonstrated Strengths ({result.strong_domains.length})</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              You achieved 75%+ accuracy in these domains. Solid foundation established!
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {result.strong_domains.map((dom) => (
                <span
                  key={dom}
                  className="px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs font-medium flex items-center gap-1.5"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>{dom.replace(/_/g, " ")}</span>
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Full Domain Breakdown */}
        <Card className="p-5 space-y-4 bg-slate-900/90 border-slate-800">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              All 8 Domain Breakdown
            </h3>
            <span className="text-[10px] text-slate-500 font-medium">8 Tested Domains</span>
          </div>

          <div className="space-y-2.5">
            {result.domain_breakdown.map((item) => {
              const isWeak = item.classification === "WEAK";
              const isStrong = item.classification === "STRONG";

              return (
                <div
                  key={item.domain}
                  className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200">
                        {item.domain.replace(/_/g, " ")}
                      </span>
                      <span
                        className={`text-[9px] uppercase font-bold px-2 py-0.5 rounded ${
                          isWeak
                            ? "bg-rose-500/15 text-rose-400 border border-rose-500/20"
                            : isStrong
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {item.classification}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400">
                      {item.subject === "MATH" ? "Math" : "Reading & Writing"} • {item.correct_questions} of {item.total_questions} questions correct
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden shrink-0">
                      <div
                        className={`h-full rounded-full ${
                          isWeak
                            ? "bg-rose-400"
                            : isStrong
                            ? "bg-emerald-400"
                            : "bg-cyan-400"
                        }`}
                        style={{ width: `${Math.max(4, item.accuracy)}%` }}
                      />
                    </div>
                    <span className="font-mono font-bold text-slate-100 min-w-[3rem] text-right">
                      {Math.round(item.accuracy)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <Link href="/practice" className="flex-1">
            <Button variant="primary" size="lg" className="w-full justify-center gap-2">
              <span>Start Targeted Practice</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Link href="/diagnostic" className="sm:w-auto">
            <Button variant="secondary" size="lg" className="w-full justify-center gap-2">
              <RotateCcw className="w-4 h-4" />
              <span>Retake Diagnostic</span>
            </Button>
          </Link>
        </div>
      </div>
    </AppShell>
  );
}

export default function DiagnosticResultPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <div className="py-20 text-center space-y-3">
            <div className="w-8 h-8 mx-auto border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-slate-400">Loading diagnostic calibration report...</p>
          </div>
        </AppShell>
      }
    >
      <DiagnosticResultContent />
    </Suspense>
  );
}

