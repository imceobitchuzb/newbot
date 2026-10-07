"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  Calculator,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Flame,
  HelpCircle,
  Lightbulb,
  Play,
  Zap,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { MathText } from "@/components/ui/MathText";
import { api } from "@/lib/api";

export default function TechniqueDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params.technique as string) || "";
  const [showExampleSolution, setShowExampleSolution] = useState(false);

  const { data: technique, isLoading, error } = useQuery({
    queryKey: ["desmos", "technique", slug],
    queryFn: () => api.getDesmosTechniqueBySlug(slug),
    enabled: Boolean(slug),
  });

  if (isLoading) {
    return (
      <AppShell>
        <div className="p-8 text-center text-xs text-slate-500">
          Loading Desmos technique...
        </div>
      </AppShell>
    );
  }

  if (error || !technique) {
    return (
      <AppShell>
        <div className="p-8 text-center space-y-3">
          <p className="text-xs text-rose-400">Technique not found.</p>
          <Link href="/desmos">
            <Button size="sm" variant="outline">
              Back to Desmos Lab
            </Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  const diffBadgeVariant =
    technique.difficulty === "EASY"
      ? "success"
      : technique.difficulty === "MEDIUM"
      ? "warning"
      : "error";

  return (
    <AppShell>
      <div className="space-y-6 pb-16">
        {/* Header */}
        <div className="flex items-center justify-between px-1">
          <Link
            href="/desmos"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Desmos Lab</span>
          </Link>

          <a
            href="https://www.desmos.com/calculator"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
          >
            <span>Open Desmos</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* Title Header Card */}
        <Card variant="gradient" className="p-5 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <Badge variant={diffBadgeVariant} className="text-[10px] uppercase font-bold tracking-wider">
              {technique.difficulty} Difficulty
            </Badge>
            <span className="text-[11px] text-cyan-400 font-mono uppercase">
              {technique.technique_type.replace(/_/g, " ")}
            </span>
          </div>

          <h1 className="text-base sm:text-lg font-bold text-slate-100 flex items-center gap-2">
            <Zap className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>{technique.title}</span>
          </h1>

          <p className="text-xs text-slate-300 leading-relaxed">
            {technique.description}
          </p>

          <div className="pt-2 flex flex-wrap gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={() => router.push(`/desmos/practice?technique=${technique.slug}`)}
              className="text-xs font-bold flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Practice This Technique</span>
            </Button>

            <a
              href="https://www.desmos.com/calculator"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button
                variant="outline"
                size="sm"
                className="text-xs border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 flex items-center gap-1.5"
              >
                <Calculator className="w-3.5 h-3.5 text-cyan-400" />
                <span>Open Calculator</span>
              </Button>
            </a>
          </div>
        </Card>

        {/* When to Use vs When NOT to Use */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Card className="p-4 bg-slate-900/80 border-emerald-500/30 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4" />
              <span>When to Use</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              <MathText text={technique.when_to_use} />
            </p>
          </Card>

          <Card className="p-4 bg-slate-900/80 border-amber-500/30 space-y-2">
            <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4" />
              <span>When NOT to Use</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              <MathText text={technique.when_not_to_use} />
            </p>
          </Card>
        </div>

        {/* Step-by-Step Instructions */}
        <div className="space-y-3">
          <h2 className="text-xs uppercase tracking-wider font-bold text-slate-400 px-1 flex items-center gap-1.5">
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <span>Step-by-Step Workflow</span>
          </h2>

          <div className="space-y-2">
            {technique.steps.map((step, idx) => (
              <Card key={idx} className="p-3.5 bg-slate-900/70 border-slate-800 flex items-start gap-3">
                <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <div className="text-xs text-slate-200 leading-relaxed">
                  <MathText text={step} />
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* SAT Speed Tip */}
        <Card className="p-4 bg-cyan-950/20 border-cyan-500/30 space-y-2">
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
            <Flame className="w-4 h-4" />
            <span>Digital SAT Speed Hack</span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed">
            <MathText text={technique.sat_tip} />
          </p>
        </Card>

        {/* Common Pitfalls */}
        {technique.common_mistakes && technique.common_mistakes.length > 0 && (
          <div className="space-y-2">
            <h2 className="text-xs uppercase tracking-wider font-bold text-slate-400 px-1 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Common Traps to Avoid</span>
            </h2>

            <div className="space-y-2">
              {technique.common_mistakes.map((mistake, idx) => (
                <Card key={idx} className="p-3 bg-slate-900/60 border-slate-800 text-xs text-slate-300 leading-relaxed flex items-start gap-2">
                  <span className="text-rose-400 font-bold">•</span>
                  <div>
                    <MathText text={mistake} />
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Example SAT Question Walkthrough */}
        {technique.example_question && (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xs uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
                <HelpCircle className="w-4 h-4 text-cyan-400" />
                <span>Example SAT Question</span>
              </h2>
              <span className="text-[11px] text-slate-500">
                {technique.example_question.skill}
              </span>
            </div>

            <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
              <div className="text-xs text-slate-200 leading-relaxed">
                <MathText text={technique.example_question.question_text} />
              </div>

              {/* Options */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                {technique.example_question.options.map((opt) => (
                  <div
                    key={opt.id}
                    className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-center gap-2"
                  >
                    <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-400 font-bold text-[10px] flex items-center justify-center shrink-0">
                      {opt.label}
                    </span>
                    <MathText text={opt.text} />
                  </div>
                ))}
              </div>

              {/* Toggle Solution */}
              <div className="pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowExampleSolution(!showExampleSolution)}
                  className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-semibold"
                >
                  {showExampleSolution ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  <span>{showExampleSolution ? "Hide Desmos Walkthrough" : "Reveal Desmos Walkthrough"}</span>
                </button>

                {showExampleSolution && (
                  <div className="mt-3 p-3 rounded-lg bg-slate-950 border border-cyan-500/20 space-y-2 text-xs">
                    <div className="text-cyan-400 font-semibold text-[11px]">Explanation:</div>
                    <p className="text-slate-300 leading-relaxed">
                      <MathText text={technique.example_question.explanation} />
                    </p>
                    {technique.example_question.sat_shortcut && (
                      <div className="pt-1 text-[11px] text-emerald-400 flex items-start gap-1">
                        <Zap className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold">Desmos Shortcut: </span>
                          <MathText text={technique.example_question.sat_shortcut} />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Live Embedded Desmos Workspace on the Technique Page */}
        <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calculator className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs uppercase tracking-wider font-bold text-slate-200">
                Interactive Desmos Workspace
              </h2>
            </div>
            <span className="text-[10px] text-cyan-400 bg-cyan-950/40 border border-cyan-500/30 px-2 py-0.5 rounded font-medium">
              Try This Technique Here
            </span>
          </div>

          <div className="w-full h-80 sm:h-96 rounded-xl overflow-hidden border border-cyan-500/30 bg-slate-950 relative">
            <iframe
              src="https://www.desmos.com/calculator"
              title="Interactive Desmos Calculator"
              className="w-full h-full border-0"
              sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
              loading="lazy"
            />
          </div>
          <p className="text-[11px] text-slate-400 text-center">
            Follow the steps above and test them live in the calculator!
          </p>
        </Card>

        {/* Bottom CTA */}
        <div className="pt-4 flex justify-center">
          <Button
            variant="primary"
            onClick={() => router.push(`/desmos/practice?technique=${technique.slug}`)}
            className="w-full sm:w-auto px-8 h-10 text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Start Practice Drills on {technique.title}</span>
          </Button>
        </div>
      </div>
    </AppShell>
  );
}
