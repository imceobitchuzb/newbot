"use client";

import Link from "next/link";
import { BookOpen, ArrowLeft } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";

export default function ReadingWritingPage() {
  const domains = [
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

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-emerald-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              Reading & Writing
            </h1>
          </div>
          <Link href="/" className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        <Card variant="gradient" className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-emerald-400 font-semibold">Reading & Writing Mastery</span>
            <span className="text-slate-400">Target: 680+</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The Digital SAT R&W section consists of 54 questions across two adaptive modules. Each question features a short passage, graph, or bulleted synthesis notes.
          </p>
          <div className="pt-1">
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-medium">
              Scheduled for Phase 6 — Reading & Writing Module
            </span>
          </div>
        </Card>

        <div className="space-y-2.5">
          {domains.map((domain) => (
            <Card key={domain.title} className="p-4 bg-slate-900/80 border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-200">{domain.title}</h2>
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                  {domain.target}
                </span>
              </div>
              <ul className="text-xs text-slate-400 space-y-1 pl-2">
                {domain.skills.map((skill) => (
                  <li key={skill} className="flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-emerald-400" />
                    <span>{skill}</span>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
