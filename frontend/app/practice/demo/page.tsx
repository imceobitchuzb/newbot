"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Target, ArrowLeft, RefreshCw, Loader2 } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { QuestionCard } from "@/components/questions/QuestionCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

export default function PracticeDemoPage() {
  const [selectedSubject, setSelectedSubject] = useState<string | undefined>(undefined);

  const {
    data: question,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["randomQuestion", selectedSubject],
    queryFn: () => api.getRandomQuestion({ subject: selectedSubject }),
    staleTime: 0, // Always load fresh on manual trigger
  });

  return (
    <AppShell>
      <div className="space-y-4">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-cyan-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              Question Engine Demo
            </h1>
          </div>
          <Link
            href="/practice"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Practice</span>
          </Link>
        </div>

        {/* Filter controls */}
        <div className="flex items-center justify-between gap-2 p-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setSelectedSubject(undefined)}
              className={`px-2.5 py-1 rounded-lg font-medium transition ${
                selectedSubject === undefined
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => setSelectedSubject("MATH")}
              className={`px-2.5 py-1 rounded-lg font-medium transition ${
                selectedSubject === "MATH"
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Math
            </button>
            <button
              type="button"
              onClick={() => setSelectedSubject("READING_WRITING")}
              className={`px-2.5 py-1 rounded-lg font-medium transition ${
                selectedSubject === "READING_WRITING"
                  ? "bg-emerald-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Reading
            </button>
          </div>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => refetch()}
            disabled={isFetching}
            className="text-[11px] h-8 px-2"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 mr-1 ${isFetching ? "animate-spin" : ""}`}
            />
            <span>Shuffle</span>
          </Button>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="p-12 text-center space-y-3">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
            <p className="text-xs text-slate-400">Loading question from Question Engine...</p>
          </div>
        )}

        {/* Error state */}
        {isError && (
          <Card className="p-5 border-rose-800 bg-rose-950/30 space-y-2">
            <p className="text-xs text-rose-300">
              {(error as any)?.message || "Failed to load question."}
            </p>
            <Button size="sm" variant="secondary" onClick={() => refetch()}>
              Try again
            </Button>
          </Card>
        )}

        {/* Interactive Question Card */}
        {question && (
          <QuestionCard
            key={question.id}
            question={question}
            onNextQuestion={() => refetch()}
          />
        )}
      </div>
    </AppShell>
  );
}
