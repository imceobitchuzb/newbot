"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  ArrowLeft,
  RefreshCw,
  Loader2,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { QuestionCard } from "@/components/questions/QuestionCard";
import { api } from "@/lib/api";
import { Question } from "@/types/question";

const RW_DOMAINS = [
  { value: "ALL", label: "All Domains" },
  { value: "INFORMATION_IDEAS", label: "Information & Ideas" },
  { value: "CRAFT_STRUCTURE", label: "Craft & Structure" },
  { value: "EXPRESSION_IDEAS", label: "Expression of Ideas" },
  { value: "STANDARD_ENGLISH_CONVENTIONS", label: "Standard English" },
];

const RW_DIFFICULTIES = [
  { value: "ALL", label: "All Difficulties" },
  { value: "EASY", label: "Easy" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HARD", label: "Hard" },
];

const DOMAIN_DETAILS = [
  {
    title: "Information & Ideas",
    skills: ["Central ideas & details", "Command of evidence (textual & quantitative)", "Inferences without overreach"],
    target: "Passage Comprehension",
  },
  {
    title: "Craft & Structure",
    skills: ["Words in context (academic vocabulary)", "Text structure and purpose", "Cross-text connections"],
    target: "Vocabulary & Rhetoric",
  },
  {
    title: "Expression of Ideas",
    skills: ["Rhetorical synthesis (bullet notes to claim)", "Transitions (contrast, cause, sequence)"],
    target: "Logical Flow",
  },
  {
    title: "Standard English Conventions",
    skills: ["Sentence boundaries (periods, semicolons)", "Subject-verb & pronoun agreement", "Modifiers & parallel structure"],
    target: "Grammar Rules",
  },
];

export default function ReadingWritingPage() {
  const [selectedDomain, setSelectedDomain] = useState<string>("ALL");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("ALL");
  const [showSyllabus, setShowSyllabus] = useState<boolean>(false);
  const [shuffleKey, setShuffleKey] = useState<number>(0);

  // Fetch real R&W question from Question Engine 2.0
  const {
    data: question,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<Question>({
    queryKey: [
      "reading-writing-question",
      selectedDomain,
      selectedDifficulty,
      shuffleKey,
    ],
    queryFn: async () => {
      if (selectedDomain !== "ALL") {
        const questions = await api.getQuestions({
          subject: "READING_WRITING",
          domain: selectedDomain,
          difficulty: selectedDifficulty !== "ALL" ? selectedDifficulty : undefined,
          limit: 10,
        });
        if (questions && questions.length > 0) {
          // Pick a question from the returned list (already prioritized by selector)
          return questions[Math.floor(Math.random() * questions.length)];
        }
      }
      return api.getRandomQuestion({
        subject: "READING_WRITING",
        difficulty: selectedDifficulty !== "ALL" ? selectedDifficulty : undefined,
      });
    },
    staleTime: 0,
  });

  const handleNextQuestion = () => {
    setShuffleKey((prev) => prev + 1);
  };

  return (
    <AppShell>
      <div className="space-y-4 pb-12">
        {/* Navigation Header */}
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">
                Reading & Writing Practice
              </h1>
              <p className="text-[11px] text-slate-400">
                Digital SAT passages, grammar & vocabulary
              </p>
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

        {/* Target Mastery Banner */}
        <Card variant="gradient" className="p-4 border border-emerald-500/20 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-emerald-400 font-bold flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" /> Reading & Writing Mastery
            </span>
            <span className="text-slate-400 font-mono text-[11px]">Target: 680+</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Practice actual Digital SAT questions with passage analysis, rhetorical synthesis, and grammar conventions powered by Question Engine 2.0.
          </p>
        </Card>

        {/* Filter Controls Bar */}
        <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2 text-xs">
          {/* Domain Filter Pills */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-none">
            {RW_DOMAINS.map((dom) => (
              <button
                key={dom.value}
                type="button"
                onClick={() => {
                  setSelectedDomain(dom.value);
                  setShuffleKey((prev) => prev + 1);
                }}
                className={`px-2.5 py-1 rounded-lg font-medium shrink-0 transition text-[11px] ${
                  selectedDomain === dom.value
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                {dom.label}
              </button>
            ))}
          </div>

          {/* Difficulty Filter & Shuffle Button */}
          <div className="flex items-center justify-between pt-1 border-t border-slate-800/60">
            <div className="flex items-center gap-1">
              {RW_DIFFICULTIES.map((diff) => (
                <button
                  key={diff.value}
                  type="button"
                  onClick={() => {
                    setSelectedDifficulty(diff.value);
                    setShuffleKey((prev) => prev + 1);
                  }}
                  className={`px-2 py-0.5 rounded-md font-medium transition text-[10px] ${
                    selectedDifficulty === diff.value
                      ? "bg-slate-700 text-emerald-300 border border-emerald-500/30"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {diff.label}
                </button>
              ))}
            </div>

            <Button
              size="sm"
              variant="ghost"
              onClick={handleNextQuestion}
              disabled={isFetching}
              className="text-[11px] h-7 px-2 text-slate-300 hover:text-white"
            >
              <RefreshCw
                className={`w-3 h-3 mr-1 ${isFetching ? "animate-spin" : ""}`}
              />
              <span>New Question</span>
            </Button>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="p-12 text-center space-y-3 bg-slate-900/50 rounded-xl border border-slate-800">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mx-auto" />
            <p className="text-xs text-slate-400">Loading Reading & Writing question...</p>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <Card className="p-5 border-rose-800 bg-rose-950/30 space-y-2">
            <p className="text-xs text-rose-300">
              {(error as any)?.message || "Failed to load Reading & Writing question."}
            </p>
            <Button size="sm" variant="secondary" onClick={() => refetch()}>
              Try again
            </Button>
          </Card>
        )}

        {/* Active Question Card */}
        {question && (
          <QuestionCard
            key={question.id}
            question={question}
            onNextQuestion={handleNextQuestion}
          />
        )}

        {/* Collapsible Syllabus & Domain Target Breakdown */}
        <div className="pt-2">
          <button
            onClick={() => setShowSyllabus(!showSyllabus)}
            className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 hover:text-slate-100 transition"
          >
            <span className="font-semibold flex items-center gap-2">
              <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
              <span>Digital SAT R&W Curriculum (4 Domains)</span>
            </span>
            {showSyllabus ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </button>

          {showSyllabus && (
            <div className="space-y-2.5 pt-3">
              {DOMAIN_DETAILS.map((domain) => (
                <Card key={domain.title} className="p-3.5 bg-slate-900/80 border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xs font-bold text-slate-200">{domain.title}</h2>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                      {domain.target}
                    </span>
                  </div>
                  <ul className="text-[11px] text-slate-400 space-y-1 pl-1">
                    {domain.skills.map((skill) => (
                      <li key={skill} className="flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-emerald-400 shrink-0" />
                        <span>{skill}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
