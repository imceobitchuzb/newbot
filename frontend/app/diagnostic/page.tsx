"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Calculator,
  CheckCircle2,
  Clock,
  Compass,
  FileQuestion,
  HelpCircle,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MathText } from "@/components/ui/MathText";
import { api } from "@/lib/api";
import { CurrentDiagnosticState } from "@/types/diagnostic";

export default function DiagnosticPage() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();

  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [activeState, setActiveState] = useState<CurrentDiagnosticState | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [moduleInterstitial, setModuleInterstitial] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Informational test timer
  useEffect(() => {
    if (!activeState || activeState.status !== "IN_PROGRESS" || moduleInterstitial) return;
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [activeState, moduleInterstitial]);

  // Initial check for active diagnostic session
  useEffect(() => {
    async function checkCurrentDiagnostic() {
      try {
        setLoading(true);
        const current = await api.getCurrentDiagnostic();
        if (current && current.status === "IN_PROGRESS") {
          setActiveState(current);
          setQuestionStartTime(Date.now());
        }
      } catch (err: any) {
        console.error("Failed to check active diagnostic:", err);
      } finally {
        setLoading(false);
      }
    }
    checkCurrentDiagnostic();
  }, []);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleStartOrResume = async () => {
    try {
      setStarting(true);
      setError(null);
      await api.startOrResumeDiagnostic();
      const current = await api.getCurrentDiagnostic();
      if (current) {
        setActiveState(current);
        setSelectedOptionId(null);
        setQuestionStartTime(Date.now());
      }
    } catch (err: any) {
      setError(err?.message || "Failed to start diagnostic test.");
    } finally {
      setStarting(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!activeState || !activeState.current_question || !selectedOptionId) return;

    try {
      setSubmitting(true);
      setError(null);
      const timeSpent = Math.max(
        1,
        Math.min(3600, Math.round((Date.now() - questionStartTime) / 1000)),
      );

      const res = await api.submitDiagnosticAnswer(
        activeState.id,
        activeState.current_question.id,
        {
          selected_option_id: selectedOptionId,
          time_spent_seconds: timeSpent,
        },
      );

      setSelectedOptionId(null);

      if (res.diagnostic_completed) {
        // Full test finished -> navigate to results!
        await refreshUser();
        router.push(`/diagnostic/result?session_id=${activeState.id}`);
        return;
      }

      if (res.module_completed) {
        // Module 1 finished -> show interstitial before Module 2
        setModuleInterstitial(true);
      }

      // Fetch next question
      const nextState = await api.getCurrentDiagnostic();
      if (nextState) {
        setActiveState(nextState);
        setQuestionStartTime(Date.now());
      }
    } catch (err: any) {
      setError(err?.message || "Failed to submit answer. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="py-20 text-center space-y-3">
          <div className="w-8 h-8 mx-auto border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400">Loading diagnostic state...</p>
        </div>
      </AppShell>
    );
  }

  // --- INTERSTITIAL VIEW: MODULE 1 COMPLETE ---
  if (moduleInterstitial) {
    return (
      <AppShell>
        <div className="py-8 space-y-6 max-w-lg mx-auto">
          <Card variant="gradient" className="p-6 text-center space-y-4">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                Halfway Milestone Reached
              </span>
              <h2 className="text-lg font-bold text-slate-100 mt-2">
                Math Module Complete!
              </h2>
              <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
                You have successfully solved all 20 Math questions. Take a breath! Next up is Module 2: Reading & Writing (20 questions).
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs grid grid-cols-2 gap-2 text-left">
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Module 1</p>
                <p className="font-semibold text-slate-200">Math (20 Qs)</p>
                <p className="text-[10px] text-emerald-400 font-medium">Completed</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Module 2</p>
                <p className="font-semibold text-slate-200">Reading & Writing (20 Qs)</p>
                <p className="text-[10px] text-cyan-400 font-medium">Next Up</p>
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              className="w-full justify-center gap-2"
              onClick={() => setModuleInterstitial(false)}
            >
              <span>Begin Reading & Writing Module</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Card>
        </div>
      </AppShell>
    );
  }

  // --- ACTIVE TEST RUNNER VIEW ---
  if (activeState && activeState.status === "IN_PROGRESS" && activeState.current_question) {
    const q = activeState.current_question;
    const isMath = activeState.subject === "MATH";

    return (
      <AppShell>
        <div className="space-y-4 max-w-2xl mx-auto pb-8">
          {/* Top Progress & Timer Bar */}
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <span
                className={`text-[11px] font-bold px-2.5 py-1 rounded-lg border ${
                  isMath
                    ? "bg-blue-500/15 border-blue-500/30 text-blue-300"
                    : "bg-emerald-500/15 border-emerald-500/30 text-emerald-300"
                }`}
              >
                Module {activeState.module_number}: {isMath ? "Math" : "Reading & Writing"}
              </span>
              <span className="text-xs text-slate-400 font-medium">
                Q{activeState.answered_in_module + 1} of {activeState.total_in_module}
              </span>
            </div>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-300">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span>{formatTimer(elapsedSeconds)}</span>
            </div>
          </div>

          {/* Overall Progress Tracker */}
          <div className="space-y-1.5 px-1">
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>Overall Diagnostic Progress</span>
              <span className="font-semibold text-slate-300">
                {activeState.total_answered} / {activeState.total_questions} ({activeState.progress_percent}%)
              </span>
            </div>
            <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-300 rounded-full"
                style={{ width: `${Math.max(2, activeState.progress_percent)}%` }}
              />
            </div>
          </div>

          {/* Question Card */}
          <Card className="p-5 space-y-4 bg-slate-900/90 border-slate-800">
            {/* Domain & Skill tags */}
            <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                {q.domain.replace(/_/g, " ")}
              </span>
              <span className="text-slate-500">•</span>
              <span className="text-slate-400">{q.skill}</span>
            </div>

            {/* Passage if present */}
            {q.passage && (
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto space-y-1.5">
                {q.passage.title && (
                  <p className="font-semibold text-slate-200">{q.passage.title}</p>
                )}
                <MathText text={q.passage.passage_text} />
              </div>
            )}

            {/* Question Prompt */}
            <div className="text-sm font-medium text-slate-100 leading-relaxed pt-1">
              <MathText text={q.question_text} />
            </div>

            {/* Answer Choices */}
            <div className="space-y-2 pt-2">
              {q.options.map((opt) => {
                const isSelected = selectedOptionId === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setSelectedOptionId(opt.id)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-start gap-3 ${
                      isSelected
                        ? "bg-cyan-500/10 border-cyan-500 text-slate-100 shadow-sm shadow-cyan-500/10"
                        : "bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-200"
                    }`}
                  >
                    <div
                      className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 transition-colors ${
                        isSelected
                          ? "bg-cyan-500 text-slate-950 font-extrabold"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {opt.label}
                    </div>
                    <div className="text-xs leading-relaxed flex-1 pt-0.5">
                      <MathText text={opt.text} />
                    </div>
                  </button>
                );
              })}
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Action */}
            <div className="pt-2 flex justify-end">
              <Button
                variant="primary"
                size="md"
                disabled={!selectedOptionId || submitting}
                onClick={handleSubmitAnswer}
                className="w-full sm:w-auto px-6 justify-center gap-2"
              >
                {submitting ? (
                  <span>Recording Answer...</span>
                ) : (
                  <>
                    <span>Next Question</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </Card>
        </div>
      </AppShell>
    );
  }

  // --- INTRO / START SCREEN ---
  const isCompleted = user?.profile?.diagnostic_status === "completed";

  return (
    <AppShell>
      <div className="space-y-5 max-w-lg mx-auto">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-cyan-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              Diagnostic Assessment
            </h1>
          </div>
          <Link href="/" className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        {/* Hero Card */}
        <Card variant="gradient" className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 bg-cyan-500/10 px-2.5 py-0.5 rounded-full border border-cyan-500/20">
              Official Calibration
            </span>
            <div className="flex items-center gap-1 text-[11px] text-slate-400">
              <Clock className="w-3.5 h-3.5" />
              <span>~45–60 Minutes</span>
            </div>
          </div>

          <div>
            <h2 className="text-lg font-bold text-slate-100">
              SAT Master Diagnostic
            </h2>
            <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
              This diagnostic accurately measures your baseline score and identifies your strongest and weakest areas across all 8 Digital SAT domains.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs pt-1">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Calculator className="w-4 h-4" />
              </div>
              <div>
                <p className="font-semibold text-slate-200">Math</p>
                <p className="text-[10px] text-slate-400">20 Questions</p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <BookOpen className="w-4 h-4" />
              </div>
              <div>
                <p className="font-semibold text-slate-200">Reading & Writing</p>
                <p className="text-[10px] text-slate-400">20 Questions</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Structure & Test Rules */}
        <Card className="p-4 space-y-3 bg-slate-900/80 border-slate-800 text-xs">
          <p className="font-semibold text-slate-200 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>How This Calibration Works</span>
          </p>

          <ul className="space-y-2 text-slate-300 text-[11px] leading-relaxed">
            <li className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
              <span><strong>Balanced Distribution:</strong> Covers all 4 Math domains and 4 Reading & Writing domains with Easy, Medium, and Hard difficulty levels.</span>
            </li>
            <li className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
              <span><strong>Zero Answer Leaks:</strong> Correctness and detailed step-by-step solutions are kept hidden until test completion to preserve test validity.</span>
            </li>
            <li className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
              <span><strong>Actionable Report:</strong> Upon finishing, you receive your Estimated SAT Score Range, accuracy percent, and list of Priority Weak Domains.</span>
            </li>
          </ul>

          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isCompleted && (
            <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xs space-y-1">
              <p className="font-semibold text-cyan-300">Previous Calibration Available</p>
              <p className="text-[11px] text-slate-300">
                You already completed a diagnostic test (Math: {user?.profile?.math_estimate || "—"}, RW: {user?.profile?.rw_estimate || "—"}). You can review your previous results or start a fresh diagnostic session.
              </p>
              <div className="pt-2 flex gap-2">
                <Link href="/diagnostic/result" className="flex-1">
                  <Button variant="secondary" size="sm" className="w-full text-xs">
                    View Results
                  </Button>
                </Link>
              </div>
            </div>
          )}

          <Button
            variant="primary"
            size="lg"
            disabled={starting}
            onClick={handleStartOrResume}
            className="w-full justify-center gap-2 mt-2"
          >
            {starting ? (
              <span>Preparing Diagnostic Session...</span>
            ) : isCompleted ? (
              <span>Retake Diagnostic (40 Questions)</span>
            ) : (
              <span>Start Diagnostic Test (40 Questions)</span>
            )}
          </Button>
        </Card>
      </div>
    </AppShell>
  );
}
