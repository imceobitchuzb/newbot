"use client";

import Link from "next/link";
import { Calculator, ArrowLeft, ChevronRight } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";

export default function MathPage() {
  const domains = [
    {
      title: "Algebra",
      skills: ["Linear equations in 1 & 2 variables", "Linear functions & slope", "Systems of linear equations", "Linear inequalities"],
      target: "Essential Foundation",
    },
    {
      title: "Advanced Math",
      skills: ["Equivalent quadratic expressions", "Nonlinear equations in 1 variable", "Exponential functions", "Polynomial arithmetic"],
      target: "High-Yield Topics",
    },
    {
      title: "Problem-Solving & Data Analysis",
      skills: ["Ratios, rates, and proportions", "Percentages and percent change", "Scatterplots and two-way tables", "Probability and statistics"],
      target: "Critical Traps",
    },
    {
      title: "Geometry & Trigonometry",
      skills: ["Area, volume, and perimeter", "Lines, angles, and triangles", "Right triangles and trigonometry", "Circle equations and theorems"],
      target: "Precision Rules",
    },
  ];

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-blue-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              Math Module
            </h1>
          </div>
          <Link href="/" className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        <Card variant="gradient" className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-blue-400 font-semibold">SAT Math Mastery</span>
            <span className="text-slate-400">Target: 720+</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The Digital SAT Math section consists of 44 questions across two adaptive modules. Each domain will be unlocked with step-by-step lessons, SAT shortcuts, and Desmos tricks.
          </p>
          <div className="pt-1">
            <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-medium">
              Scheduled for Phase 5 — Math Question Engine
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
                    <span className="w-1 h-1 rounded-full bg-blue-400" />
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
