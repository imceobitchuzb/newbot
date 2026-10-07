"use client";

import { Sparkles, HelpCircle, BookOpen, KeyRound, Lightbulb, Zap } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";

export default function TutorPage() {
  const modes = [
    {
      name: "HINT",
      description: "Provides Socratic guiding clues without spoiling the final answer.",
      icon: Lightbulb,
      color: "text-amber-400",
    },
    {
      name: "EXPLAIN",
      description: "Breaks down concepts and shows step-by-step resolution logic.",
      icon: BookOpen,
      color: "text-blue-400",
    },
    {
      name: "SOLVE",
      description: "Generates full mathematical or grammatical solution.",
      icon: KeyRound,
      color: "text-emerald-400",
    },
    {
      name: "ANOTHER METHOD",
      description: "Shows alternate solution methods (e.g. backsolving, plugin values).",
      icon: HelpCircle,
      color: "text-cyan-400",
    },
    {
      name: "SAT TRICK",
      description: "Reveals high-speed test-taking shortcuts and Desmos calculator techniques.",
      icon: Zap,
      color: "text-purple-400",
    },
  ];

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center gap-2 px-1">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
            AI SAT Tutor
          </h1>
        </div>

        <Card variant="gradient" className="p-4 space-y-2.5">
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold">
            <span>Socratic Learning Assistant</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Your personal SAT tutor will explain difficult questions, deliver progressive hints, and help you systematically eliminate repeated mistakes.
          </p>
          <div className="pt-1">
            <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/15 border border-blue-500/30 text-blue-300 font-medium">
              Architecture ready for Phase 10
            </span>
          </div>
        </Card>

        <div className="space-y-2.5">
          <h2 className="text-xs uppercase tracking-wider text-slate-400 font-semibold px-1">
            Tutor Modes
          </h2>

          <div className="space-y-2">
            {modes.map((mode) => {
              const Icon = mode.icon;
              return (
                <Card
                  key={mode.name}
                  className="p-3 bg-slate-900/70 border-slate-800 space-y-1"
                >
                  <div className="flex items-center gap-2">
                    <Icon className={`w-3.5 h-3.5 ${mode.color}`} />
                    <span className="text-xs font-bold text-slate-200">
                      {mode.name}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed pl-5.5">
                    {mode.description}
                  </p>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
