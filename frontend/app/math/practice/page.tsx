"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Calculator,
  ChevronRight,
  Clock,
  Sparkles,
  Zap,
  HelpCircle,
  CheckCircle2,
  XCircle,
  RotateCcw,
  PlayCircle,
  Layers,
  BarChart2,
  Check,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MathText } from "@/components/ui/MathText";
import { Skeleton } from "@/components/ui/Skeleton";
import { AnswerOption } from "@/components/questions/AnswerOption";
import { api } from "@/lib/api";
import {
  MathPracticeAnswerResponse,
  MathPracticeResultResponse,
  MathPracticeSessionResponse,
  MathPracticeStartRequest,
} from "@/types/math";

const DOMAINS_LIST = [
  { value: "ALL", label: "All Math Domains" },
  { value: "ALGEBRA", label: "Algebra" },
  { value: "ADVANCED_MATH", label: "Advanced Math" },
  { value: "PROBLEM_SOLVING_DATA_ANALYSIS", label: "Problem-Solving & Data Analysis" },
  { value: "GEOMETRY_TRIGONOMETRY", label: "Geometry & Trigonometry" },
];

const DIFFICULTIES_LIST = [
  { value: "MIXED", label: "Mixed Difficulty" },
  { value: "EASY", label: "Easy" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HARD", label: "Hard" },
];

function PracticeRunnerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // URL search params pre-seeding
  const paramDomain = searchParams.get("domain") || "ALL";
  const paramSkill = searchParams.get("skill") || "";
  const paramDiff = searchParams.get("difficulty") || "MIXED";

  // Setup state
  const [selectedDomain, setSelectedDomain] = useState<string>(paramDomain);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>(paramDiff);
  const [selectedSkill, setSelectedSkill] = useState<string>(paramSkill);
  const [selectedCount, setSelectedCount] = useState<number>(10);

  // Runner state
  const [activeSession, setActiveSession] = useState<MathPracticeSessionResponse | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [lastAnswerResponse, setLastAnswerResponse] = useState<MathPracticeAnswerResponse | null>(null);
  const [completedResult, setCompletedResult] = useState<MathPracticeResultResponse | null>(null);
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());

  // 1. Check for active session
  const { data: currentSessionData, isLoading: isLoadingCurrent } = useQuery<MathPracticeSessionResponse | null>({
    queryKey: ["current-math-practice"],
    queryFn: () => api.getCurrentMathPractice(),
  });

  useEffect(() => {
    if (currentSessionData && currentSessionData.status === "IN_PROGRESS") {
      setActiveSession(currentSessionData);
      setQuestionStartTime(Date.now());
    }
  }, [currentSessionData]);

  // 2. Start session mutation
  const startMutation = useMutation({
    mutationFn: (req: MathPracticeStartRequest) => api.startMathPractice(req),
    onSuccess: (session) => {
      setActiveSession(session);
      setSelectedOptionId(null);
      setLastAnswerResponse(null);
      setCompletedResult(null);
      setQuestionStartTime(Date.now());
      queryClient.invalidateQueries({ queryKey: ["current-math-practice"] });
    },
  });

  // 3. Submit answer mutation
  const answerMutation = useMutation({
    mutationFn: async ({
      sessionId,
      practiceQuestionId,
      optionId,
      timeSpent,
    }: {
      sessionId: string;
      practiceQuestionId: string;
      optionId: string;
      timeSpent: number;
    }) => {
      return api.submitMathPracticeAnswer(sessionId, practiceQuestionId, {
        selected_option_id: optionId,
        time_spent_seconds: timeSpent,
      });
    },
    onSuccess: async (data) => {
      setLastAnswerResponse(data);
      if (data.session_completed && activeSession) {
        // Fetch completion result
        const res = await api.getMathPracticeResult(activeSession.id);
        setCompletedResult(res);
        queryClient.invalidateQueries({ queryKey: ["math-analytics"] });
      }
    },
  });

  const handleStartSession = () => {
    startMutation.mutate({
      domain: selectedDomain === "ALL" ? null : selectedDomain,
      difficulty: selectedDifficulty === "MIXED" ? null : selectedDifficulty,
      skill: selectedSkill ? selectedSkill : null,
      question_count: selectedCount,
    });
  };

  const currentQ = activeSession?.current_question;

  const handleSubmitAnswer = () => {
    if (!activeSession || !currentQ || !selectedOptionId || answerMutation.isPending) return;
    const timeSpent = Math.max(1, Math.round((Date.now() - questionStartTime) / 1000));
    answerMutation.mutate({
      sessionId: activeSession.id,
      practiceQuestionId: currentQ.practice_question_id,
      optionId: selectedOptionId,
      timeSpent,
    });
  };

  const handleNextQuestion = async () => {
    if (!activeSession) return;
    setSelectedOptionId(null);
    setLastAnswerResponse(null);
    setQuestionStartTime(Date.now());

    // Refresh current session state
    const updated = await api.getMathPracticeSession(activeSession.id);
    setActiveSession(updated);
  };

  // ================= VIEW 1: COMPLETED RESULTS =================
  if (completedResult) {
    return (
      <AppShell>
        <div className="space-y-5 pb-8">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs uppercase tracking-wider font-bold text-slate-400">Practice Summary</span>
            <Link href="/math" className="text-xs text-blue-400 hover:text-blue-300 font-semibold">
              Done
            </Link>
          </div>

          <Card variant="gradient" className="p-5 text-center space-y-4 border border-blue-500/20">
            <div className="w-12 h-12 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center mx-auto">
              <Check className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h2 className="text-xl font-black text-white">Practice Session Complete!</h2>
              <p className="text-xs text-slate-300">
                You scored {completedResult.correct_count} out of {completedResult.total_questions} questions correct.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2 pt-2">
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-base font-bold text-white">{completedResult.accuracy_percentage}%</div>
                <div className="text-[10px] text-slate-400">Accuracy</div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-base font-bold text-white">
                  {completedResult.correct_count}/{completedResult.total_questions}
                </div>
                <div className="text-[10px] text-slate-400">Score</div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-base font-bold text-white">{completedResult.total_time_seconds}s</div>
                <div className="text-[10px] text-slate-400">Time</div>
              </div>
            </div>

            <div className="pt-2 flex flex-col gap-2">
              <Button
                onClick={() => {
                  setCompletedResult(null);
                  setActiveSession(null);
                  setSelectedOptionId(null);
                  setLastAnswerResponse(null);
                }}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold h-11"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                <span>Practice Again</span>
              </Button>

              <Button
                variant="outline"
                onClick={() => router.push("/math")}
                className="w-full border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-200 h-11"
              >
                Back to Math Hub
              </Button>
            </div>
          </Card>

          {/* Question Review Section */}
          <div className="space-y-3 pt-2">
            <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 px-1">Question Review</h3>
            <div className="space-y-3">
              {completedResult.questions.map((q, idx) => (
                <Card key={q.practice_question_id} className="p-4 bg-slate-900/80 border-slate-800 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-300">Question {idx + 1}</span>
                    <span
                      className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                        q.is_correct
                          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                          : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                      }`}
                    >
                      {q.is_correct ? "Correct" : "Incorrect"}
                    </span>
                  </div>

                  <div className="text-xs text-slate-200">
                    <MathText content={q.question_text} />
                  </div>

                  {q.explanation && (
                    <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1 text-xs">
                      <span className="font-semibold text-blue-400 text-[11px] block">Explanation:</span>
                      <MathText content={q.explanation} />
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  // ================= VIEW 2: ACTIVE QUESTION RUNNER =================
  if (activeSession && currentQ) {
    const isSubmitted = !!lastAnswerResponse;
    const isCorrect = lastAnswerResponse?.is_correct;
    const currentIndex = activeSession.current_question_index;
    const totalCount = activeSession.total_questions;
    const progressPercent = Math.round(((currentIndex + 1) / totalCount) * 100);

    return (
      <AppShell>
        <div className="space-y-4 pb-8">
          {/* Header navigation & progress */}
          <div className="flex items-center justify-between px-1">
            <button
              onClick={() => {
                if (confirm("Leave current practice session? You can resume it anytime.")) {
                  router.push("/math");
                }
              }}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Exit</span>
            </button>

            <span className="text-xs font-bold text-slate-200">
              Question {currentIndex + 1} of {totalCount}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-blue-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
              {currentQ.domain.replace(/_/g, " ")}
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-medium">
              {currentQ.skill}
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium uppercase">
              {currentQ.difficulty}
            </span>
            {currentQ.desmos_recommended && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold flex items-center gap-1">
                <Calculator className="w-3 h-3" /> Desmos Fast
              </span>
            )}
          </div>

          {/* Question Text Card */}
          <Card key={currentQ.question_id} className="p-4 bg-slate-900/90 border-slate-800 text-slate-100 text-xs sm:text-sm leading-relaxed space-y-3">
            <MathText content={currentQ.question_text} />
          </Card>

          {/* Options */}
          <div className="space-y-2">
            {currentQ.options.map((opt) => {
              const isSelected = selectedOptionId === opt.id;
              const isAnswerKey = isSubmitted && lastAnswerResponse?.correct_option_id === opt.id;

              return (
                <AnswerOption
                  key={opt.id}
                  option={opt}
                  isSelected={isSelected}
                  onSelect={(id) => {
                    if (!isSubmitted) setSelectedOptionId(id);
                  }}
                  isSubmitted={isSubmitted}
                  isCorrect={isCorrect}
                  isAnswerKey={isAnswerKey}
                />
              );
            })}
          </div>

          {/* Action / Next buttons */}
          {!isSubmitted ? (
            <Button
              onClick={handleSubmitAnswer}
              disabled={!selectedOptionId || answerMutation.isPending}
              className="w-full h-11 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl"
            >
              {answerMutation.isPending ? "Checking Answer..." : "Submit Answer"}
            </Button>
          ) : (
            <div className="space-y-3 pt-1">
              {/* Immediate Feedback Banner */}
              <div
                className={`p-3.5 rounded-xl border flex items-center gap-2.5 ${
                  isCorrect
                    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                    : "bg-rose-500/10 border-rose-500/30 text-rose-300"
                }`}
              >
                {isCorrect ? <CheckCircle2 className="w-5 h-5 shrink-0" /> : <XCircle className="w-5 h-5 shrink-0 text-rose-400" />}
                <div className="text-xs">
                  <div className="font-bold">{isCorrect ? "Correct!" : "Incorrect"}</div>
                  <div className="text-[11px] opacity-90">
                    {isCorrect ? "Great work! Review the explanation below." : "Don't worry, check the breakdown below to learn the pattern."}
                  </div>
                </div>
              </div>

              {/* Step-by-Step Explanation */}
              {lastAnswerResponse.explanation && (
                <Card className="p-4 bg-slate-900 border-slate-800 space-y-2 text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-blue-400 text-xs">
                    <HelpCircle className="w-4 h-4" />
                    <span>Step-by-Step Explanation</span>
                  </div>
                  <div className="text-slate-300 leading-relaxed pt-1">
                    <MathText content={lastAnswerResponse.explanation} />
                  </div>
                </Card>
              )}

              {/* SAT Shortcut Card */}
              {lastAnswerResponse.sat_shortcut && (
                <Card className="p-3.5 bg-gradient-to-r from-amber-500/10 to-slate-900 border border-amber-500/30 space-y-1 text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-amber-400 text-xs">
                    <Zap className="w-4 h-4" />
                    <span>Digital SAT Shortcut & Trap Warning</span>
                  </div>
                  <div className="text-slate-300 leading-relaxed pt-0.5">
                    <MathText content={lastAnswerResponse.sat_shortcut} />
                  </div>
                </Card>
              )}

              {/* Next Question / Finish Button */}
              <Button
                onClick={handleNextQuestion}
                className="w-full h-11 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2"
              >
                <span>{lastAnswerResponse.session_completed ? "View Final Results" : "Next Question"}</span>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </AppShell>
    );
  }

  // ================= VIEW 3: SETUP SCREEN =================
  return (
    <AppShell>
      <div className="space-y-5 pb-8">
        <div className="flex items-center justify-between px-1">
          <Link
            href="/math"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Math Hub</span>
          </Link>
          <span className="text-xs font-bold text-slate-200">Practice Setup</span>
        </div>

        <Card variant="gradient" className="p-4 space-y-2 border border-blue-500/20">
          <h1 className="text-base font-bold text-white flex items-center gap-2">
            <Calculator className="w-5 h-5 text-blue-400" />
            <span>Custom Math Practice</span>
          </h1>
          <p className="text-xs text-slate-300 leading-relaxed">
            Configure your target domain, difficulty level, and question volume. All questions feature step-by-step
            explanations, Desmos guidance, and College Board shortcuts.
          </p>
        </Card>

        {/* Configuration form */}
        <Card className="p-4 bg-slate-900/80 border-slate-800 space-y-4">
          {/* Domain selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Select Domain</label>
            <div className="grid grid-cols-1 gap-2">
              {DOMAINS_LIST.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setSelectedDomain(d.value)}
                  className={`w-full text-left p-2.5 rounded-xl border text-xs font-medium transition-all flex items-center justify-between ${
                    selectedDomain === d.value
                      ? "bg-blue-600/15 border-blue-500 text-blue-200"
                      : "bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <span>{d.label}</span>
                  {selectedDomain === d.value && <Check className="w-4 h-4 text-blue-400" />}
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Difficulty Level</label>
            <div className="grid grid-cols-2 gap-2">
              {DIFFICULTIES_LIST.map((diff) => (
                <button
                  key={diff.value}
                  type="button"
                  onClick={() => setSelectedDifficulty(diff.value)}
                  className={`p-2.5 rounded-xl border text-xs font-medium transition-all text-center ${
                    selectedDifficulty === diff.value
                      ? "bg-blue-600/15 border-blue-500 text-blue-200"
                      : "bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  {diff.label}
                </button>
              ))}
            </div>
          </div>

          {/* Question Count */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Question Volume</label>
            <div className="grid grid-cols-3 gap-2">
              {[5, 10, 20].map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => setSelectedCount(count)}
                  className={`p-2.5 rounded-xl border text-xs font-bold transition-all text-center ${
                    selectedCount === count
                      ? "bg-blue-600/15 border-blue-500 text-blue-200"
                      : "bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  {count} Questions
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={handleStartSession}
            disabled={startMutation.isPending}
            className="w-full h-11 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2 mt-2 shadow-lg shadow-blue-500/20"
          >
            <PlayCircle className="w-5 h-5" />
            <span>{startMutation.isPending ? "Generating Session..." : "Start Practice Session"}</span>
          </Button>
        </Card>
      </div>
    </AppShell>
  );
}

export default function MathPracticePage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-2xl m-4" />}>
      <PracticeRunnerContent />
    </Suspense>
  );
}
