"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  Filter,
  Flame,
  HelpCircle,
  RefreshCw,
  Sparkles,
  Zap,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MathText } from "@/components/ui/MathText";
import { api } from "@/lib/api";
import {
  MistakeAnalyticsResponse,
  MistakeEntryItem,
  MistakeListResponse,
  MistakeStatus,
  MistakeType,
} from "@/types/mistake";

export default function MistakeBookPage() {
  const queryClient = useQueryClient();
  const [selectedSubject, setSelectedSubject] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedType, setSelectedType] = useState<string>("ALL");

  // Fetch analytics
  const { data: analytics, isLoading: analyticsLoading } = useQuery<MistakeAnalyticsResponse>({
    queryKey: ["mistake-analytics"],
    queryFn: () => api.getMistakeAnalytics(),
  });

  // Fetch next priority mistake
  const { data: nextMistake, isLoading: nextLoading } = useQuery<MistakeEntryItem | null>({
    queryKey: ["next-mistake"],
    queryFn: () => api.getNextMistake(),
  });

  // Fetch list of mistakes with filters
  const { data: mistakesData, isLoading: listLoading, refetch } = useQuery<MistakeListResponse>({
    queryKey: ["mistakes-list", selectedSubject, selectedStatus, selectedType],
    queryFn: () =>
      api.listMistakes({
        subject: selectedSubject === "ALL" ? undefined : selectedSubject,
        status: selectedStatus === "ALL" ? undefined : selectedStatus,
        mistake_type: selectedType === "ALL" ? undefined : selectedType,
        limit: 50,
      }),
  });

  // Review mutation
  const reviewMutation = useMutation({
    mutationFn: (id: string) => api.reviewMistake(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mistake-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["mistakes-list"] });
      queryClient.invalidateQueries({ queryKey: ["next-mistake"] });
    },
  });

  const getStatusBadge = (status: MistakeStatus) => {
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

  const getMistakeTypeLabel = (type: MistakeType | string) => {
    switch (type) {
      case "CONCEPT_GAP":
        return { label: "Concept Gap", color: "text-purple-400 bg-purple-500/15 border-purple-500/30" };
      case "CARELESS_ERROR":
        return { label: "Careless Error", color: "text-blue-400 bg-blue-500/15 border-blue-500/30" };
      case "MISREAD":
        return { label: "Question Misread", color: "text-amber-400 bg-amber-500/15 border-amber-500/30" };
      case "CALCULATION_ERROR":
        return { label: "Calculation Slip", color: "text-orange-400 bg-orange-500/15 border-orange-500/30" };
      case "TIME_PRESSURE":
        return { label: "Time Pressure", color: "text-red-400 bg-red-500/15 border-red-500/30" };
      default:
        return { label: "Unclassified", color: "text-slate-400 bg-slate-800 border-slate-700" };
    }
  };

  const formatDomain = (d: string) => {
    return d
      .toLowerCase()
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  };

  return (
    <AppShell>
      <div className="space-y-5 pb-10">
        {/* Header */}
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-rose-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">Mistake Book</h1>
              <p className="text-[11px] text-slate-400">Target 1400+ via deliberate error remediation</p>
            </div>
          </div>
          <Link
            href="/"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        {/* Analytics Telemetry Cards */}
        <div className="grid grid-cols-2 gap-2.5">
          <Card className="p-3 bg-slate-900/70 border-slate-800 flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-rose-500/15 border border-rose-500/20 flex items-center justify-center text-rose-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-slate-400">Active Errors</div>
              <div className="text-lg font-bold text-white">
                {analyticsLoading ? "..." : analytics?.active_mistakes ?? 0}
              </div>
            </div>
          </Card>

          <Card className="p-3 bg-slate-900/70 border-slate-800 flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Clock className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-slate-400">Due Reviews</div>
              <div className="text-lg font-bold text-amber-300">
                {analyticsLoading ? "..." : analytics?.due_reviews ?? 0}
              </div>
            </div>
          </Card>

          <Card className="p-3 bg-slate-900/70 border-slate-800 flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-slate-400">Mastered</div>
              <div className="text-lg font-bold text-emerald-300">
                {analyticsLoading ? "..." : analytics?.mastered_mistakes ?? 0}
              </div>
            </div>
          </Card>

          <Card className="p-3 bg-slate-900/70 border-slate-800 flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/15 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs text-slate-400">Mastery Rate</div>
              <div className="text-lg font-bold text-cyan-300">
                {analyticsLoading ? "..." : `${analytics?.mastery_rate ?? 0}%`}
              </div>
            </div>
          </Card>
        </div>

        {/* Priority Remediation Banner */}
        {nextMistake && (
          <Card
            variant="interactive"
            className="p-4 bg-gradient-to-br from-rose-950/40 via-slate-900 to-slate-900 border-rose-500/30 space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-rose-400 font-bold text-xs uppercase tracking-wider">
                <Flame className="w-3.5 h-3.5 text-rose-400" />
                <span>Highest Priority Remediation</span>
              </div>
              {nextMistake.is_due && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold animate-pulse">
                  Review Due Now
                </span>
              )}
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="font-semibold text-slate-300">{nextMistake.subject}</span>
                <span>•</span>
                <span>{formatDomain(nextMistake.domain)}</span>
              </div>
              <div className="text-xs text-slate-200 line-clamp-2 italic">
                <MathText text={nextMistake.question_text} />
              </div>
            </div>

            <div className="pt-1 flex items-center justify-between">
              <div className="text-[11px] text-slate-400">
                Retries: {nextMistake.correct_retry_count + nextMistake.incorrect_retry_count} (
                <span className="text-emerald-400">{nextMistake.correct_retry_count} correct</span>)
              </div>
              <Link href={`/mistakes/${nextMistake.id}`}>
                <Button size="sm" className="bg-rose-600 hover:bg-rose-500 text-white font-semibold flex items-center gap-1.5">
                  <span>Remediate Now</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          </Card>
        )}

        {/* Filter Controls */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="font-semibold uppercase tracking-wider flex items-center gap-1">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              Filter Mistakes
            </span>
            <span>Total: {mistakesData?.total ?? 0}</span>
          </div>

          {/* Subject Pills */}
          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {[
              { id: "ALL", label: "All Subjects" },
              { id: "MATH", label: "Math" },
              { id: "READING_WRITING", label: "Reading & Writing" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedSubject(tab.id)}
                className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedSubject === tab.id
                    ? "bg-rose-600 text-white shadow-sm"
                    : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Status Pills */}
          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {[
              { id: "ALL", label: "All Statuses" },
              { id: "ACTIVE", label: "Active" },
              { id: "IN_REVIEW", label: "In Review" },
              { id: "MASTERED", label: "Mastered" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedStatus(tab.id)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium whitespace-nowrap transition-colors ${
                  selectedStatus === tab.id
                    ? "bg-slate-200 text-slate-900 font-semibold"
                    : "bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Mistake Entries List */}
        <div className="space-y-3">
          {listLoading ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading mistake book...</div>
          ) : !mistakesData?.items || mistakesData.items.length === 0 ? (
            <Card className="p-8 text-center space-y-3 bg-slate-900/40 border-slate-800">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-white">No Mistakes Found</h3>
                <p className="text-xs text-slate-400 max-w-xs mx-auto">
                  {selectedSubject !== "ALL" || selectedStatus !== "ALL"
                    ? "No errors match your active filter criteria."
                    : "Great job! Complete practice drills or full SAT sessions to automatically track and remediate tricky problems."}
                </p>
              </div>
              <Link href="/math">
                <Button size="sm" variant="outline" className="mt-2 text-xs">
                  Train Math Skills
                </Button>
              </Link>
            </Card>
          ) : (
            mistakesData.items.map((entry) => {
              const statusBadge = getStatusBadge(entry.status);
              const typeBadge = getMistakeTypeLabel(entry.mistake_type);

              return (
                <Card
                  key={entry.id}
                  className="p-4 bg-slate-900/70 border-slate-800 space-y-3 hover:border-slate-700 transition"
                >
                  {/* Top tags row */}
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                        {entry.subject}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800/80 text-slate-400">
                        {formatDomain(entry.domain)}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded border font-medium ${typeBadge.color}`}
                      >
                        {typeBadge.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {entry.is_due && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold">
                          Due
                        </span>
                      )}
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${statusBadge.bg} ${statusBadge.text} ${statusBadge.border}`}
                      >
                        {statusBadge.label}
                      </span>
                    </div>
                  </div>

                  {/* Question snippet */}
                  <div className="text-xs text-slate-200 line-clamp-3 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/60">
                    <MathText text={entry.question_text} />
                  </div>

                  {/* Attempt Telemetry & Actions */}
                  <div className="flex items-center justify-between pt-1">
                    <div className="text-[11px] text-slate-400 flex items-center gap-2">
                      <span>
                        Retries:{" "}
                        <strong className="text-slate-200">
                          {entry.correct_retry_count + entry.incorrect_retry_count}
                        </strong>
                      </span>
                      <span>•</span>
                      <span className="text-emerald-400 font-medium">
                        {entry.correct_retry_count} correct
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => reviewMutation.mutate(entry.id)}
                        disabled={reviewMutation.isPending}
                        className="text-xs text-slate-400 hover:text-white px-2 py-1 h-auto"
                        title="Mark spaced repetition review"
                      >
                        <RefreshCw className="w-3.5 h-3.5 mr-1" />
                        Review
                      </Button>

                      <Link href={`/mistakes/${entry.id}`}>
                        <Button size="sm" className="bg-rose-600 hover:bg-rose-500 text-white text-xs px-3 py-1 h-8">
                          Solve & Retry
                        </Button>
                      </Link>
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      </div>
    </AppShell>
  );
}
