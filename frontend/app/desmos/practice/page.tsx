"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Calculator,
  CheckCircle2,
  Clock,
  ExternalLink,
  Flame,
  HelpCircle,
  RotateCcw,
  Sparkles,
  Trophy,
  XCircle,
  Zap,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { MathText } from "@/components/ui/MathText";
import { DesmosPanel } from "@/components/desmos/DesmosPanel";
import { api } from "@/lib/api";
import { DesmosAnswerResponse, DesmosQuestionItem, DesmosSession } from "@/types/desmos";

function DesmosPracticeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const techniqueSlug = searchParams.get("technique") || undefined;
  const countParam = parseInt(searchParams.get("count") || "10", 10);
  const recommendedOnly = searchParams.get("recommended") === "true";

  const [session, setSession] = useState<DesmosSession | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [lastAnswerResult, setLastAnswerResult] = useState<DesmosAnswerResponse | null>(null);
  const [timerSeconds, setTimerSeconds] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [desmosUsed, setDesmosUsed] = useState<boolean>(true);

  // Timer effect
  useEffect(() => {
    if (!session || session.status === "COMPLETED") return;
    const interval = setInterval(() => {
      setTimerSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [session]);

  // Start or resume session
  const startSessionMutation = useMutation({
    mutationFn: async () => {
      return await api.startDesmosSession({
        technique_slug: techniqueSlug,
        target_count: countParam,
        recommended_only: recommendedOnly,
      });
    },
    onSuccess: (data) => {
      setSession(data);
    },
    onError: (err) => {
      console.error("Failed to start Desmos session", err);
    },
  });

  useEffect(() => {
    startSessionMutation.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const currentQ: DesmosQuestionItem | null =
    session?.questions.find((q) => !q.is_answered) || null;

  const currentIndex = session
    ? session.questions.findIndex((q) => !q.is_answered)
    : 0;

  const handleSelectOption = (optId: string) => {
    if (lastAnswerResult) return; // Answer already revealed
    setSelectedOptionId(optId);
  };

  const handleSubmitAnswer = async () => {
    if (!session || !currentQ || !selectedOptionId || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const res = await api.submitDesmosAnswer(session.id, currentQ.question_id, {
        selected_option_id: selectedOptionId,
        time_spent_seconds: Math.max(1, timerSeconds),
        desmos_used: desmosUsed,
      });

      setLastAnswerResult(res);

      // Update local question state
      const updatedQuestions = session.questions.map((q) => {
        if (q.question_id === currentQ.question_id) {
          return {
            ...q,
            is_answered: true,
            is_correct: res.is_correct,
            selected_option_id: selectedOptionId,
          };
        }
        return q;
      });

      setSession({
        ...session,
        completed_count: session.completed_count + 1,
        correct_count: res.is_correct ? session.correct_count + 1 : session.correct_count,
        accuracy_percent: res.session_accuracy,
        status: res.session_completed ? "COMPLETED" : "IN_PROGRESS",
        questions: updatedQuestions,
      });

      queryClient.invalidateQueries({ queryKey: ["desmos"] });
    } catch (err) {
      console.error("Failed to submit answer", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    setLastAnswerResult(null);
    setSelectedOptionId(null);
    setTimerSeconds(0);
  };

  if (startSessionMutation.isPending) {
    return (
      <AppShell>
        <div className="p-12 text-center space-y-3">
          <Calculator className="w-8 h-8 text-cyan-400 mx-auto animate-pulse" />
          <p className="text-xs text-slate-400">Loading Desmos Practice Session...</p>
        </div>
      </AppShell>
    );
  }

  if (startSessionMutation.isError || !session) {
    return (
      <AppShell>
        <div className="p-8 text-center space-y-3">
          <p className="text-xs text-rose-400">Failed to load Desmos practice session.</p>
          <Link href="/desmos">
            <Button size="sm" variant="outline">
              Back to Desmos Lab
            </Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  // Session Completed Screen
  if (session.status === "COMPLETED" && !lastAnswerResult) {
    return (
      <AppShell>
        <div className="space-y-6 pb-12">
          <Card variant="gradient" className="p-6 text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center mx-auto">
              <Trophy className="w-7 h-7" />
            </div>

            <div>
              <h1 className="text-base font-bold text-slate-100">
                Desmos Session Complete!
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                {session.technique_title || "Mixed Desmos Practice"}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3 max-w-sm mx-auto pt-2">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-lg font-bold text-slate-100">
                  {session.correct_count} / {session.completed_count}
                </div>
                <div className="text-[10px] text-slate-500 uppercase">Correct</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-lg font-bold text-cyan-400">
                  {session.accuracy_percent}%
                </div>
                <div className="text-[10px] text-slate-500 uppercase">Accuracy</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-lg font-bold text-slate-100">
                  {session.target_count}
                </div>
                <div className="text-[10px] text-slate-500 uppercase">Total Qs</div>
              </div>
            </div>

            <div className="pt-4 flex flex-col sm:flex-row gap-2 justify-center">
              <Link href="/desmos">
                <Button variant="primary" size="sm" className="w-full sm:w-auto text-xs font-bold">
                  Return to Desmos Lab
                </Button>
              </Link>
              <Link href="/math">
                <Button variant="outline" size="sm" className="w-full sm:w-auto text-xs">
                  Math Dashboard
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </AppShell>
    );
  }

  if (!currentQ && !lastAnswerResult) {
    return (
      <AppShell>
        <div className="p-8 text-center space-y-3">
          <p className="text-xs text-slate-400">All questions answered in this session.</p>
          <Link href="/desmos">
            <Button size="sm" variant="primary">
              Back to Desmos Lab
            </Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  const activeQuestion = currentQ || session.questions[session.questions.length - 1];

  return (
    <AppShell>
      <div className="space-y-4 pb-16">
        {/* Top Session Progress Bar */}
        <div className="flex items-center justify-between text-xs px-1">
          <div className="flex items-center gap-2">
            <Link
              href="/desmos"
              className="text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Exit</span>
            </Link>
            <span className="text-slate-600">•</span>
            <span className="text-slate-300 font-semibold">
              Question {currentIndex >= 0 ? currentIndex + 1 : session.completed_count} of {session.target_count}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 text-slate-400 font-mono text-[11px]">
              <Clock className="w-3 h-3 text-cyan-400" />
              <span>{timerSeconds}s</span>
            </div>
            <Badge variant="outline" className="text-[10px]">
              {session.correct_count} Correct
            </Badge>
          </div>
        </div>

        {/* Progress bar line */}
        <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-cyan-500 transition-all duration-300"
            style={{
              width: `${(session.completed_count / session.target_count) * 100}%`,
            }}
          />
        </div>

        {/* Desmos Strategy Panel */}
        <DesmosPanel
          status={activeQuestion.recommendation_status}
          reason={activeQuestion.recommendation_reason}
          techniqueTitle={activeQuestion.technique_title}
          techniqueSlug={activeQuestion.technique_slug}
          desmosUsed={desmosUsed}
          onToggleDesmosUsed={setDesmosUsed}
        />

        {/* Question Card */}
        <Card className="p-4 sm:p-5 bg-slate-900/90 border-slate-800 space-y-4">
          <div className="flex items-center justify-between gap-2 text-[11px] text-slate-400">
            <span className="font-semibold text-slate-300">{activeQuestion.domain}</span>
            <Badge variant="outline" className="text-[10px] uppercase">
              {activeQuestion.difficulty}
            </Badge>
          </div>

          {/* Question Text */}
          <div className="text-xs sm:text-sm text-slate-100 leading-relaxed">
            <MathText text={activeQuestion.question_text} />
          </div>

          {/* Multiple-Choice Options */}
          <div className="space-y-2 pt-1">
            {activeQuestion.options.map((opt) => {
              const isSelected = selectedOptionId === opt.id;
              const isRevealed = Boolean(lastAnswerResult);
              const isCorrectOption =
                lastAnswerResult && lastAnswerResult.correct_option_id === opt.id;
              const isWrongSelected =
                lastAnswerResult && isSelected && !lastAnswerResult.is_correct;

              let optionClasses =
                "p-3 rounded-xl border text-xs transition-all flex items-start gap-3 cursor-pointer ";

              if (!isRevealed) {
                if (isSelected) {
                  optionClasses +=
                    "bg-cyan-500/20 border-cyan-500/60 text-slate-100 shadow-sm";
                } else {
                  optionClasses +=
                    "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900/60";
                }
              } else {
                if (isCorrectOption) {
                  optionClasses +=
                    "bg-emerald-500/20 border-emerald-500 text-emerald-200 font-semibold";
                } else if (isWrongSelected) {
                  optionClasses +=
                    "bg-rose-500/20 border-rose-500 text-rose-200";
                } else {
                  optionClasses +=
                    "bg-slate-950/60 border-slate-800 text-slate-500 opacity-60";
                }
              }

              return (
                <div
                  key={opt.id}
                  onClick={() => handleSelectOption(opt.id)}
                  className={optionClasses}
                >
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5 ${
                      isSelected
                        ? "bg-cyan-500 text-white"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {opt.label}
                  </span>
                  <div className="leading-relaxed">
                    <MathText text={opt.text} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Button */}
          {!lastAnswerResult ? (
            <div className="pt-2">
              <Button
                variant="primary"
                onClick={handleSubmitAnswer}
                disabled={!selectedOptionId || isSubmitting}
                className="w-full text-xs font-bold h-10 flex items-center justify-center gap-1.5"
              >
                {isSubmitting ? "Evaluating..." : "Check Answer"}
              </Button>
            </div>
          ) : (
            <div className="pt-2">
              <Button
                variant="primary"
                onClick={handleNextQuestion}
                className="w-full text-xs font-bold h-10 flex items-center justify-center gap-1.5 shadow-lg shadow-cyan-500/20"
              >
                <span>{session.status === "COMPLETED" ? "Finish Session" : "Next Question"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          )}
        </Card>

        {/* Immediate Feedback Card */}
        {lastAnswerResult && (
          <Card
            className={`p-4 border space-y-3 ${
              lastAnswerResult.is_correct
                ? "bg-emerald-950/20 border-emerald-500/40"
                : "bg-rose-950/20 border-rose-500/40"
            }`}
          >
            <div className="flex items-center justify-between text-xs font-bold">
              <div className="flex items-center gap-1.5">
                {lastAnswerResult.is_correct ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-emerald-300">Correct! Great execution.</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 text-rose-400" />
                    <span className="text-rose-300">Incorrect. Review Desmos strategy.</span>
                  </>
                )}
              </div>

              {!lastAnswerResult.is_correct && (
                <span className="text-[10px] text-amber-400 font-medium">
                  Logged in Mistake Book
                </span>
              )}
            </div>

            {/* Explanation */}
            <div className="text-xs text-slate-300 leading-relaxed pt-1">
              <div className="font-semibold text-slate-200 text-[11px] mb-1">Detailed Explanation:</div>
              <MathText text={lastAnswerResult.explanation} />
            </div>

            {/* Desmos Guidance */}
            {lastAnswerResult.desmos_guidance && (
              <div className="pt-2 border-t border-slate-800/80 text-xs text-cyan-300 leading-relaxed flex items-start gap-1.5">
                <Zap className="w-3.5 h-3.5 shrink-0 mt-0.5 text-cyan-400" />
                <div>
                  <span className="font-bold">Desmos Insight: </span>
                  <MathText text={lastAnswerResult.desmos_guidance} />
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </AppShell>
  );
}

export default function DesmosPracticePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-4">
          <div className="text-center space-y-3">
            <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mx-auto" />
            <p className="text-xs text-slate-400">Loading Desmos Practice...</p>
          </div>
        </div>
      }
    >
      <DesmosPracticeContent />
    </Suspense>
  );
}

