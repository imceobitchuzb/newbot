"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Lightbulb,
  Zap,
  Tag,
  Clock,
  Sparkles,
  Trophy,
  RefreshCw,
  Bot,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MathText } from "@/components/ui/MathText";
import { api } from "@/lib/api";
import {
  MistakeEntryItem,
  MistakeRetryResponse,
  MistakeStatus,
  MistakeType,
} from "@/types/mistake";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function MistakeDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const queryClient = useQueryClient();

  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [retryResult, setRetryResult] = useState<MistakeRetryResponse | null>(null);
  const [showHint, setShowHint] = useState<boolean>(false);
  const [showShortcut, setShowShortcut] = useState<boolean>(false);

  // Fetch current mistake entry
  const { data: mistake, isLoading, isError } = useQuery<MistakeEntryItem>({
    queryKey: ["mistake", id],
    queryFn: () => api.getMistakeById(id),
  });

  // Classify mistake mutation
  const classifyMutation = useMutation({
    mutationFn: (type: MistakeType) =>
      api.classifyMistake(id, { mistake_type: type }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["mistake", id], updated);
      queryClient.invalidateQueries({ queryKey: ["mistake-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["mistakes-list"] });
    },
  });

  // Retry mutation
  const retryMutation = useMutation({
    mutationFn: (optionId: string) =>
      api.retryMistake(id, { selected_option_id: optionId, time_spent_seconds: 30 }),
    onSuccess: (data) => {
      setRetryResult(data);
      queryClient.invalidateQueries({ queryKey: ["mistake", id] });
      queryClient.invalidateQueries({ queryKey: ["mistake-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["mistakes-list"] });
      queryClient.invalidateQueries({ queryKey: ["next-mistake"] });
    },
  });

  const getStatusBadge = (status: MistakeStatus | string) => {
    switch (status) {
      case "MASTERED":
        return {
          label: "Mastered",
          bg: "bg-emerald-500/15",
          text: "text-emerald-400",
          border: "border-emerald-500/30",
        };
      case "IN_REVIEW":
        return {
          label: "In Review",
          bg: "bg-amber-500/15",
          text: "text-amber-400",
          border: "border-amber-500/30",
        };
      case "ACTIVE":
      default:
        return {
          label: "Active Error",
          bg: "bg-rose-500/15",
          text: "text-rose-400",
          border: "border-rose-500/30",
        };
    }
  };

  const mistakeTypes: { type: MistakeType; label: string }[] = [
    { type: "CONCEPT_GAP", label: "Concept Gap" },
    { type: "CARELESS_ERROR", label: "Careless Error" },
    { type: "MISREAD", label: "Question Misread" },
    { type: "CALCULATION_ERROR", label: "Calculation Slip" },
    { type: "TIME_PRESSURE", label: "Time Pressure" },
  ];

  if (isLoading) {
    return (
      <AppShell>
        <div className="py-20 text-center text-xs text-slate-400">Loading mistake remediation view...</div>
      </AppShell>
    );
  }

  if (isError || !mistake) {
    return (
      <AppShell>
        <div className="py-20 text-center space-y-3">
          <p className="text-sm text-rose-400 font-semibold">Mistake entry not found or access denied.</p>
          <Link href="/mistakes">
            <Button size="sm">Back to Mistake Book</Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  const currentStatus = retryResult?.new_status || mistake.status;
  const statusBadge = getStatusBadge(currentStatus);

  return (
    <AppShell>
      <div className="space-y-5 pb-12">
        {/* Navigation Header */}
        <div className="flex items-center justify-between px-1">
          <Link
            href="/mistakes"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Mistake Book</span>
          </Link>

          <div className="flex items-center gap-2">
            <span
              className={`text-[10px] px-2.5 py-0.5 rounded-full border font-semibold ${statusBadge.bg} ${statusBadge.text} ${statusBadge.border}`}
            >
              {statusBadge.label}
            </span>
          </div>
        </div>

        {/* Remediation Goal Banner */}
        <Card className="p-3 bg-slate-900/60 border-slate-800 flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/15 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
            <Trophy className="w-4 h-4" />
          </div>
          <div className="text-xs space-y-0.5">
            <div className="font-semibold text-slate-200">Deliberate Mastery Criterion</div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Achieve at least 2 consecutive correct retries without hints to promote this error to{" "}
              <strong className="text-emerald-400">Mastered</strong>.
            </p>
          </div>
        </Card>

        {/* Self-Diagnosis Classification Pills */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 px-1 font-semibold uppercase tracking-wider">
            <Tag className="w-3.5 h-3.5 text-slate-400" />
            <span>Diagnose Your Error Cause</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {mistakeTypes.map((mt) => {
              const isSelected = mistake.mistake_type === mt.type;
              return (
                <button
                  key={mt.type}
                  onClick={() => classifyMutation.mutate(mt.type)}
                  disabled={classifyMutation.isPending}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                    isSelected
                      ? "bg-rose-600/20 text-rose-300 border-rose-500/50 shadow-sm"
                      : "bg-slate-900/50 text-slate-400 hover:text-slate-200 border-slate-800"
                  }`}
                >
                  {mt.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Question Problem Statement */}
        <Card className="p-4 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-[11px] text-slate-400 pb-1 border-b border-slate-800/60">
            <div className="flex items-center gap-2">
              <span className="font-medium text-slate-300">{mistake.subject}</span>
              <span>•</span>
              <span>{mistake.skill}</span>
            </div>
            <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
              {mistake.difficulty}
            </span>
          </div>

          <div className="text-sm text-slate-100 leading-relaxed">
            <MathText text={mistake.question_text} />
          </div>
        </Card>

        {/* Multiple Choice Retry Options */}
        <div className="space-y-2">
          <div className="text-xs text-slate-400 px-1 font-semibold uppercase tracking-wider">
            Choose Answer:
          </div>

          <div className="grid grid-cols-1 gap-2.5">
            {mistake.options.map((opt) => {
              const isSelected = selectedOptionId === opt.id;
              let btnStyle = "bg-slate-900/60 border-slate-800 text-slate-200 hover:border-slate-700";

              if (retryResult) {
                if (opt.id === retryResult.correct_option_id) {
                  btnStyle = "bg-emerald-950/40 border-emerald-500/60 text-emerald-200";
                } else if (opt.id === retryResult.selected_option_id && !retryResult.is_correct) {
                  btnStyle = "bg-rose-950/40 border-rose-500/60 text-rose-200";
                }
              } else if (isSelected) {
                btnStyle = "bg-cyan-950/30 border-cyan-500/60 text-white shadow-sm";
              }

              return (
                <button
                  key={opt.id}
                  onClick={() => !retryResult && setSelectedOptionId(opt.id)}
                  disabled={!!retryResult || retryMutation.isPending}
                  className={`w-full text-left p-3.5 rounded-xl border flex items-start gap-3 transition-all ${btnStyle}`}
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

        {/* Retry Submit Action */}
        {!retryResult ? (
          <Button
            size="lg"
            className="w-full bg-rose-600 hover:bg-rose-500 text-white font-semibold py-3"
            disabled={!selectedOptionId || retryMutation.isPending}
            onClick={() => selectedOptionId && retryMutation.mutate(selectedOptionId)}
          >
            {retryMutation.isPending ? "Evaluating Attempt..." : "Submit Retry Attempt"}
          </Button>
        ) : (
          <div className="space-y-3">
            {/* Instant Result Banner */}
            {retryResult.is_correct ? (
              <Card className="p-4 bg-emerald-950/30 border-emerald-500/40 space-y-2">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Correct Answer!</span>
                </div>
                {retryResult.is_mastered ? (
                  <div className="text-xs text-emerald-300 bg-emerald-500/10 p-2.5 rounded-lg border border-emerald-500/20 flex items-center gap-2">
                    <Trophy className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>
                      Congratulations! You have completed 2 consecutive correct retries. This question is now{" "}
                      <strong>Mastered</strong>!
                    </span>
                  </div>
                ) : (
                  <p className="text-xs text-slate-300">
                    Solid work! Solve it again on your next scheduled review to achieve Mastered status.
                  </p>
                )}
              </Card>
            ) : (
              <Card className="p-4 bg-rose-950/30 border-rose-500/40 space-y-1.5">
                <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
                  <XCircle className="w-5 h-5" />
                  <span>Incorrect. Review the concept below:</span>
                </div>
                <p className="text-xs text-slate-300">
                  Carefully read through the step-by-step breakdown and SAT shortcut.
                </p>
              </Card>
            )}

            {/* Explanation Card */}
            <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-2.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-300 font-semibold uppercase tracking-wider">
                <HelpCircle className="w-4 h-4 text-cyan-400" />
                <span>Step-by-Step Explanation</span>
              </div>
              <div className="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-3 rounded-lg border border-slate-800/80">
                <MathText text={retryResult.explanation} />
              </div>
            </Card>

            {/* Hint & SAT Shortcut Accordions */}
            {(retryResult.hint || mistake.hint) && (
              <div className="space-y-1">
                <button
                  onClick={() => setShowHint(!showHint)}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-medium text-amber-300 flex items-center justify-between"
                >
                  <span className="flex items-center gap-1.5">
                    <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                    {showHint ? "Hide Hint" : "Show Conceptual Hint"}
                  </span>
                </button>
                {showHint && (
                  <div className="p-3 bg-amber-950/20 border border-amber-500/20 rounded-lg text-xs text-amber-200">
                    <MathText text={retryResult.hint || mistake.hint || ""} />
                  </div>
                )}
              </div>
            )}

            {(retryResult.sat_shortcut || mistake.sat_shortcut) && (
              <div className="space-y-1">
                <button
                  onClick={() => setShowShortcut(!showShortcut)}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-medium text-cyan-300 flex items-center justify-between"
                >
                  <span className="flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-cyan-400" />
                    {showShortcut ? "Hide SAT Shortcut" : "Show Desmos / SAT Shortcut"}
                  </span>
                </button>
                {showShortcut && (
                  <div className="p-3 bg-cyan-950/20 border border-cyan-500/20 rounded-lg text-xs text-cyan-200">
                    <MathText text={retryResult.sat_shortcut || mistake.sat_shortcut || ""} />
                  </div>
                )}
              </div>
            )}

            {/* Back to Mistakes and Explain with AI buttons */}
            <div className="pt-2 flex flex-col sm:flex-row gap-2">
              <Link href={`/tutor?context=MISTAKE&id=${mistake.id}`} className="flex-1">
                <Button className="w-full text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/20">
                  <Bot className="w-3.5 h-3.5" />
                  <span>Explain My Mistake with AI</span>
                </Button>
              </Link>
              <Link href="/mistakes" className="flex-1">
                <Button variant="outline" className="w-full text-xs">
                  Back to Mistake Book
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
