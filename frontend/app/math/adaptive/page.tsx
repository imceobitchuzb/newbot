"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  Clock,
  HelpCircle,
  Info,
  Lightbulb,
  PlayCircle,
  RefreshCw,
  Sparkles,
  Target,
  Trophy,
  XCircle,
  Zap,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { MathText } from "@/components/ui/MathText";
import { api } from "@/lib/api";
import {
  AdaptiveAnswerResponse,
  AdaptiveQuestionItem,
  AdaptiveSessionResponse,
  RecommendationType,
} from "@/types/adaptive";

export default function AdaptivePracticePage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [lastAnswerResult, setLastAnswerResult] = useState<AdaptiveAnswerResponse | null>(null);
  const [showHint, setShowHint] = useState<boolean>(false);
  const [showShortcut, setShowShortcut] = useState<boolean>(false);
  const [showWhyReason, setShowWhyReason] = useState<boolean>(true);

  // Fetch or start active adaptive session
  const {
    data: session,
    isLoading: sessionLoading,
    refetch: refetchSession,
  } = useQuery<AdaptiveSessionResponse>({
    queryKey: ["adaptive-session-current"],
    queryFn: async () => {
      const active = await api.getCurrentAdaptiveSession("MATH");
      if (active && active.status === "IN_PROGRESS") {
        return active;
      }
      return await api.startAdaptiveSession({ total_questions: 10, subject: "MATH" });
    },
    staleTime: 0,
  });

  // Track time spent per question
  useEffect(() => {
    setStartTime(Date.now());
    setSelectedOptionId(null);
    setLastAnswerResult(null);
    setShowHint(false);
    setShowShortcut(false);
  }, [session?.current_question_index]);

  // Answer submission mutation
  const answerMutation = useMutation({
    mutationFn: async () => {
      if (!session || !session.current_question || !selectedOptionId) return null;
      const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
      return await api.submitAdaptiveAnswer(
        session.id,
        session.current_question.question_id,
        {
          selected_option_id: selectedOptionId,
          time_spent_seconds: timeSpent,
        }
      );
    },
    onSuccess: (result) => {
      if (result) {
        setLastAnswerResult(result);
        queryClient.invalidateQueries({ queryKey: ["adaptive-analytics"] });
      }
    },
  });

  const getDifficultyBadge = (diff: string) => {
    switch (diff?.toUpperCase()) {
      case "HARD":
        return { label: "Hard", bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/30" };
      case "EASY":
        return { label: "Easy", bg: "bg-emerald-500/15", text: "text-emerald-400", border: "border-emerald-500/30" };
      case "MEDIUM":
      default:
        return { label: "Medium", bg: "bg-amber-500/15", text: "text-amber-400", border: "border-amber-500/30" };
    }
  };

  const getRecommendationBadge = (recType: RecommendationType | string) => {
    switch (recType) {
      case "MISTAKE_REVIEW":
        return { label: "Mistake Remediation", color: "text-rose-400 bg-rose-500/15 border-rose-500/30" };
      case "WEAK_SKILL":
        return { label: "Target Weak Skill", color: "text-amber-400 bg-amber-500/15 border-amber-500/30" };
      case "DIFFICULTY_UP":
        return { label: "Step Up Difficulty", color: "text-cyan-400 bg-cyan-500/15 border-cyan-500/30" };
      case "DIFFICULTY_DOWN":
        return { label: "Core Reinforcement", color: "text-blue-400 bg-blue-500/15 border-blue-500/30" };
      case "NEW_SKILL":
        return { label: "New Syllabus Skill", color: "text-purple-400 bg-purple-500/15 border-purple-500/30" };
      case "MAINTENANCE":
      default:
        return { label: "Skill Retention", color: "text-emerald-400 bg-emerald-500/15 border-emerald-500/30" };
    }
  };

  if (sessionLoading) {
    return (
      <AppShell>
        <div className="py-24 text-center text-xs text-slate-400 space-y-2">
          <div className="w-8 h-8 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin mx-auto" />
          <p>Calibrating adaptive recommendation...</p>
        </div>
      </AppShell>
    );
  }

  // Session completed view
  if (lastAnswerResult?.session_completed || (session && session.status === "COMPLETED")) {
    const summary = lastAnswerResult?.session_summary;
    const accuracyPct = summary ? Math.round(summary.accuracy * 100) : 0;

    return (
      <AppShell>
        <div className="space-y-5 pb-12">
          {/* Header */}
          <div className="text-center py-4 space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mx-auto shadow-lg shadow-cyan-500/10">
              <Trophy className="w-6 h-6" />
            </div>
            <h1 className="text-lg font-bold text-white tracking-tight">Adaptive Session Complete</h1>
            <p className="text-xs text-slate-400">
              Your Math mastery has been calibrated through real question performance.
            </p>
          </div>

          {/* Performance Summary Cards */}
          <div className="grid grid-cols-2 gap-3">
            <Card className="p-3.5 bg-slate-900/80 border-slate-800 text-center space-y-0.5">
              <div className="text-xs text-slate-400">Accuracy</div>
              <div className="text-2xl font-black text-cyan-400">{accuracyPct}%</div>
              <div className="text-[11px] text-slate-400">
                {summary?.total_correct ?? 0} of {summary?.total_completed ?? 0} correct
              </div>
            </Card>

            <Card className="p-3.5 bg-slate-900/80 border-slate-800 text-center space-y-0.5">
              <div className="text-xs text-slate-400">Final Difficulty</div>
              <div className="text-2xl font-black text-white">
                {summary?.next_recommended_difficulty || session?.current_difficulty || "MEDIUM"}
              </div>
              <div className="text-[11px] text-slate-400">Calibrated Level</div>
            </Card>
          </div>

          {/* Difficulty Progression */}
          {summary?.difficulty_progression && (
            <Card className="p-4 bg-slate-900/60 border-slate-800 space-y-2">
              <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <BrainCircuit className="w-4 h-4 text-cyan-400" />
                <span>Difficulty Progression</span>
              </div>
              <div className="flex items-center gap-1.5 overflow-x-auto py-1">
                {summary.difficulty_progression.map((d, i) => {
                  const b = getDifficultyBadge(d);
                  return (
                    <div key={i} className="flex items-center gap-1.5 shrink-0">
                      <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${b.bg} ${b.text} ${b.border}`}>
                        Q{i + 1}: {b.label}
                      </span>
                      {i < summary.difficulty_progression.length - 1 && (
                        <ChevronRight className="w-3 h-3 text-slate-600" />
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Next Recommended Focus */}
          {summary?.next_recommended_skill && (
            <Card className="p-4 bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-900 border-cyan-500/30 space-y-2">
              <div className="text-xs text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5" />
                <span>Next Recommended Focus</span>
              </div>
              <div className="text-sm font-semibold text-white">
                {summary.next_recommended_skill}
              </div>
              <p className="text-xs text-slate-300">
                Continue deliberate drills to reinforce weak conceptual links and advance your mastery score.
              </p>
            </Card>
          )}

          {/* CTAs */}
          <div className="space-y-2 pt-2">
            <Button
              className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-3"
              onClick={async () => {
                await api.startAdaptiveSession({ total_questions: 10, subject: "MATH" });
                refetchSession();
              }}
            >
              Start Another Adaptive Drill
            </Button>

            <Link href="/math" className="block">
              <Button variant="outline" className="w-full text-xs">
                Back to Math Hub
              </Button>
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  const currentApq = session?.current_question;
  const currentQ = currentApq?.question;

  if (!currentApq || !currentQ) {
    return (
      <AppShell>
        <div className="py-20 text-center space-y-3">
          <p className="text-xs text-slate-400">No active questions in session.</p>
          <Link href="/math">
            <Button size="sm">Back to Math Hub</Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  const diffBadge = getDifficultyBadge(currentApq.difficulty_at_assignment);
  const recBadge = getRecommendationBadge(currentApq.recommendation_type);
  const progressPercent = Math.round(
    ((session.current_question_index + (lastAnswerResult ? 1 : 0)) / session.total_questions) * 100
  );

  return (
    <AppShell>
      <div className="space-y-4 pb-16">
        {/* Top Header & Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <Link href="/math" className="hover:text-slate-200 flex items-center gap-1 transition">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Math Hub</span>
            </Link>

            <div className="flex items-center gap-2">
              <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${diffBadge.bg} ${diffBadge.text} ${diffBadge.border}`}>
                {diffBadge.label}
              </span>
              <span className="font-semibold text-slate-300">
                Question {session.current_question_index + 1} of {session.total_questions}
              </span>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Explainable "Why This Question?" Section */}
        {currentApq.reason && (
          <Card className="p-3 bg-slate-900/60 border-slate-800/80 space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${recBadge.color}`}>
                  {recBadge.label}
                </span>
                <span className="text-[11px] text-slate-400 font-medium">
                  • {currentQ.skill}
                </span>
              </div>
              <button
                onClick={() => setShowWhyReason(!showWhyReason)}
                className="text-[10px] text-slate-400 hover:text-slate-200 transition"
              >
                {showWhyReason ? "Hide reason" : "Why this question?"}
              </button>
            </div>

            {showWhyReason && (
              <p className="text-[11px] text-slate-300 leading-relaxed bg-slate-950/40 p-2 rounded-lg border border-slate-800/60 flex items-start gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                <span>{currentApq.reason}</span>
              </p>
            )}
          </Card>
        )}

        {/* Question Text Box */}
        <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
          <div className="text-xs text-slate-400 font-medium">
            {currentQ.domain}
          </div>
          <div className="text-sm text-slate-100 leading-relaxed">
            <MathText text={currentQ.question_text} />
          </div>
        </Card>

        {/* Multiple Choice Options */}
        <div className="space-y-2">
          <div className="text-[11px] text-slate-400 px-1 font-semibold uppercase tracking-wider">
            Select Your Answer:
          </div>

          <div className="grid grid-cols-1 gap-2.5">
            {currentQ.options.map((opt: import("@/types/question").QuestionOption) => {
              const isSelected = selectedOptionId === opt.id;
              let style = "bg-slate-900/60 border-slate-800 text-slate-200 hover:border-slate-700";

              if (lastAnswerResult) {
                if (opt.id === lastAnswerResult.correct_option_id) {
                  style = "bg-emerald-950/40 border-emerald-500/60 text-emerald-200";
                } else if (opt.id === lastAnswerResult.selected_option_id && !lastAnswerResult.is_correct) {
                  style = "bg-rose-950/40 border-rose-500/60 text-rose-200";
                }
              } else if (isSelected) {
                style = "bg-cyan-950/30 border-cyan-500/60 text-white shadow-sm";
              }

              return (
                <button
                  key={opt.id}
                  onClick={() => !lastAnswerResult && setSelectedOptionId(opt.id)}
                  disabled={!!lastAnswerResult || answerMutation.isPending}
                  className={`w-full text-left p-3.5 rounded-xl border flex items-start gap-3 transition-all ${style}`}
                >
                  <span className="w-6 h-6 rounded-md bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-xs font-bold shrink-0 text-slate-300">
                    {opt.label}
                  </span>
                  <div className="text-xs pt-0.5 leading-relaxed">
                    <MathText text={opt.text} />
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Button: Submit or Proceed */}
        {!lastAnswerResult ? (
          <Button
            size="lg"
            className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-3"
            disabled={!selectedOptionId || answerMutation.isPending}
            onClick={() => answerMutation.mutate()}
          >
            {answerMutation.isPending ? "Validating answer..." : "Submit Answer"}
          </Button>
        ) : (
          <div className="space-y-3">
            {/* Answer Result Banner */}
            {lastAnswerResult.is_correct ? (
              <Card className="p-3.5 bg-emerald-950/30 border-emerald-500/40 flex items-center gap-2.5 text-emerald-300 text-xs font-semibold">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span>Correct! Target mastery score updated.</span>
              </Card>
            ) : (
              <Card className="p-3.5 bg-rose-950/30 border-rose-500/40 space-y-1 text-xs">
                <div className="flex items-center gap-2 text-rose-400 font-bold">
                  <XCircle className="w-5 h-5 shrink-0" />
                  <span>Incorrect. Automatically captured in Mistake Book.</span>
                </div>
              </Card>
            )}

            {/* Step-by-Step Explanation */}
            <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-slate-300 font-semibold uppercase tracking-wider">
                <HelpCircle className="w-4 h-4 text-cyan-400" />
                <span>Step-by-Step Explanation</span>
              </div>
              <div className="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-3 rounded-lg border border-slate-800/80">
                <MathText text={lastAnswerResult.explanation} />
              </div>
            </Card>

            {/* Hint & Shortcut Accordions */}
            {lastAnswerResult.hint && (
              <div className="space-y-1">
                <button
                  onClick={() => setShowHint(!showHint)}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-medium text-amber-300 flex items-center justify-between"
                >
                  <span className="flex items-center gap-1.5">
                    <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                    {showHint ? "Hide Conceptual Hint" : "View Conceptual Hint"}
                  </span>
                </button>
                {showHint && (
                  <div className="p-3 bg-amber-950/20 border border-amber-500/20 rounded-lg text-xs text-amber-200">
                    <MathText text={lastAnswerResult.hint} />
                  </div>
                )}
              </div>
            )}

            {lastAnswerResult.sat_shortcut && (
              <div className="space-y-1">
                <button
                  onClick={() => setShowShortcut(!showShortcut)}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-medium text-cyan-300 flex items-center justify-between"
                >
                  <span className="flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-cyan-400" />
                    {showShortcut ? "Hide SAT Shortcut" : "View Desmos / SAT Shortcut"}
                  </span>
                </button>
                {showShortcut && (
                  <div className="p-3 bg-cyan-950/20 border border-cyan-500/20 rounded-lg text-xs text-cyan-200">
                    <MathText text={lastAnswerResult.sat_shortcut} />
                  </div>
                )}
              </div>
            )}

            {/* Next Question CTA */}
            <Button
              size="lg"
              className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-3 flex items-center justify-center gap-2"
              onClick={() => {
                refetchSession();
              }}
            >
              <span>Continue to Next Question</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
