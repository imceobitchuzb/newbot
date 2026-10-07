"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  BookOpen,
  Calculator,
  CheckCircle2,
  Clock,
  ExternalLink,
  Flame,
  HelpCircle,
  Play,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { TechniqueCard } from "@/components/desmos/TechniqueCard";
import { api } from "@/lib/api";
import { DesmosTechnique } from "@/types/desmos";

export default function DesmosHubPage() {
  const router = useRouter();
  const [selectedCount, setSelectedCount] = useState<number>(10);
  const [selectedTechnique, setSelectedTechnique] = useState<string>("all");
  const [recommendedOnly, setRecommendedOnly] = useState<boolean>(false);

  // Fetch Techniques
  const { data: techniquesData, isLoading: loadingTechniques } = useQuery({
    queryKey: ["desmos", "techniques"],
    queryFn: () => api.getDesmosTechniques(),
  });

  // Fetch Analytics
  const { data: analyticsData } = useQuery({
    queryKey: ["desmos", "analytics"],
    queryFn: () => api.getDesmosAnalytics(),
  });

  const techniques = techniquesData?.items || [];

  const handleStartPractice = () => {
    const params = new URLSearchParams();
    params.set("count", selectedCount.toString());
    if (selectedTechnique !== "all") {
      params.set("technique", selectedTechnique);
    }
    if (recommendedOnly) {
      params.set("recommended", "true");
    }
    router.push(`/desmos/practice?${params.toString()}`);
  };

  return (
    <AppShell>
      <div className="space-y-6 pb-12">
        {/* Header */}
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <Calculator className="w-5 h-5 text-cyan-400" />
            <h1 className="text-sm uppercase tracking-wider font-bold text-slate-100">
              Desmos Lab
            </h1>
          </div>
          <Link
            href="/"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        {/* Hero Quick Start Banner */}
        <Card variant="gradient" className="p-4 sm:p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" />
              Digital SAT Calculator Mastery
            </span>
            <a
              href="https://www.desmos.com/calculator"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] text-slate-400 hover:text-cyan-300 flex items-center gap-1 underline transition-colors"
            >
              <span>Desmos Official</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            The built-in Desmos graphing calculator is the single greatest competitive edge in
            Digital SAT Math. Learn when to graph, when to regress, and when manual math is faster.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-emerald-500/20 space-y-1">
              <span className="text-emerald-400 font-semibold text-[11px] flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                When to use Desmos:
              </span>
              <p className="text-[11px] text-slate-300">
                Nonlinear systems, quadratic zeros, regressions, visual inequalities, and verifying complex algebra.
              </p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-amber-500/20 space-y-1">
              <span className="text-amber-400 font-semibold text-[11px] flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                When NOT to use:
              </span>
              <p className="text-[11px] text-slate-300">
                Simple one-step equations ($3x = 15$), basic mental arithmetic, or complex numbers ($i$) with no real graph.
              </p>
            </div>
          </div>
        </Card>

        {/* Live Embedded Desmos Graphing Canvas Directly Inside */}
        <Card className="p-4 sm:p-5 bg-slate-900/90 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calculator className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs uppercase tracking-wider font-bold text-slate-200">
                Live Desmos Calculator (Embedded)
              </h2>
            </div>
            <span className="text-[10px] text-cyan-400 bg-cyan-950/40 border border-cyan-500/30 px-2 py-0.5 rounded font-medium">
              Official Bluebook Graphing Engine
            </span>
          </div>

          <div className="w-full h-80 sm:h-96 rounded-xl overflow-hidden border border-cyan-500/30 bg-slate-950 relative">
            <iframe
              src="https://www.desmos.com/calculator"
              title="Official Embedded Desmos Digital SAT Calculator"
              className="w-full h-full border-0"
              sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
              loading="lazy"
            />
          </div>
          <p className="text-[11px] text-slate-400 text-center">
            Test any equation, regression formula (`y1 ~ mx1 + b`), or system of equations directly here!
          </p>
        </Card>

        {/* Quick Launch Practice Card */}
        <Card className="p-4 sm:p-5 bg-slate-900/90 border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Play className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs uppercase tracking-wider font-bold text-slate-200">
                Targeted Desmos Practice
              </h2>
            </div>
            <span className="text-[11px] text-slate-500">
              83 Desmos-Ready Questions
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Technique Filter */}
            <div className="space-y-1.5">
              <label className="text-[11px] text-slate-400 font-medium">Technique</label>
              <select
                value={selectedTechnique}
                onChange={(e) => setSelectedTechnique(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="all">All Techniques (Mixed)</option>
                {techniques.map((t) => (
                  <option key={t.slug} value={t.slug}>
                    {t.title}
                  </option>
                ))}
              </select>
            </div>

            {/* Question Count */}
            <div className="space-y-1.5">
              <label className="text-[11px] text-slate-400 font-medium">Question Count</label>
              <div className="grid grid-cols-3 gap-1.5">
                {[5, 10, 20].map((cnt) => (
                  <button
                    key={cnt}
                    type="button"
                    onClick={() => setSelectedCount(cnt)}
                    className={`text-xs py-2 rounded-lg font-medium transition-colors border ${
                      selectedCount === cnt
                        ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/50"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {cnt} Qs
                  </button>
                ))}
              </div>
            </div>

            {/* Launch Button */}
            <div className="space-y-1.5 flex flex-col justify-end">
              <Button
                variant="primary"
                onClick={handleStartPractice}
                className="w-full h-[38px] text-xs font-bold flex items-center justify-center gap-2"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Launch Practice</span>
              </Button>
            </div>
          </div>
        </Card>

        {/* Telemetry Summary (if user has practiced) */}
        {analyticsData && analyticsData.total_questions_attempted > 0 && (
          <Card className="p-4 bg-slate-900/60 border-slate-800 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-300 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                Your Desmos Telemetry
              </span>
              <span className="text-slate-500 text-[11px]">
                {analyticsData.recommended_count} Recommended • {analyticsData.allowed_count} Allowed
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-base font-bold text-slate-100">
                  {analyticsData.total_questions_attempted}
                </div>
                <div className="text-[10px] text-slate-500 uppercase">Attempted</div>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-base font-bold text-cyan-400">
                  {analyticsData.overall_accuracy}%
                </div>
                <div className="text-[10px] text-slate-500 uppercase">Accuracy</div>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-base font-bold text-slate-100">
                  {analyticsData.avg_time_seconds}s
                </div>
                <div className="text-[10px] text-slate-500 uppercase">Avg Time</div>
              </div>
            </div>
          </Card>
        )}

        {/* Techniques Grid */}
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs uppercase tracking-wider font-bold text-slate-200">
                12 Canonical Desmos Techniques
              </h2>
            </div>
            <span className="text-[11px] text-slate-500">
              Interactive Strategies
            </span>
          </div>

          {loadingTechniques ? (
            <div className="p-8 text-center text-xs text-slate-500">
              Loading Desmos techniques...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {techniques.map((tech) => (
                <TechniqueCard key={tech.slug} technique={tech} />
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
