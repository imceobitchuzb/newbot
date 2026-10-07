"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Calculator,
  ArrowLeft,
  ChevronRight,
  Target,
  Sparkles,
  TrendingUp,
  BrainCircuit,
  Zap,
  PlayCircle,
  BarChart3,
  Award,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { api } from "@/lib/api";
import { useAuth } from "@/features/auth/AuthContext";
import { MathAnalyticsResponse, SkillMastery } from "@/types/math";

const DOMAIN_SLUGS: Record<string, string> = {
  ALGEBRA: "algebra",
  ADVANCED_MATH: "advanced-math",
  PROBLEM_SOLVING_DATA_ANALYSIS: "problem-solving",
  GEOMETRY_TRIGONOMETRY: "geometry-trig",
};

export default function MathPage() {
  const router = useRouter();
  const { user } = useAuth();

  const {
    data: analytics,
    isLoading,
    isError,
  } = useQuery<MathAnalyticsResponse>({
    queryKey: ["math-analytics"],
    queryFn: () => api.getMathAnalytics(),
  });

  const getMasteryBadge = (level: SkillMastery) => {
    switch (level) {
      case "STRONG":
        return { label: "Strong", bg: "bg-emerald-500/15", text: "text-emerald-400", border: "border-emerald-500/30" };
      case "PRACTICING":
        return { label: "Practicing", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30" };
      case "LEARNING":
        return { label: "Learning", bg: "bg-amber-500/15", text: "text-amber-400", border: "border-amber-500/30" };
      default:
        return { label: "Not Started", bg: "bg-slate-800", text: "text-slate-400", border: "border-slate-700" };
    }
  };

  return (
    <AppShell>
      <div className="space-y-5 pb-8">
        {/* Top Header */}
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
              <Calculator className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">SAT Math Master</h1>
              <p className="text-[11px] text-slate-400">Target 750+ with real Digital SAT skills</p>
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

        {/* Estimated Score & Diagnostic Banner */}
        <Card variant="gradient" className="p-4 relative overflow-hidden border border-blue-500/20">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-wider text-blue-400 font-bold flex items-center gap-1">
                <Target className="w-3 h-3" /> Baseline Estimate
              </span>
              <div className="text-2xl font-black text-white">
                {user?.profile?.diagnostic_status === "completed" && analytics?.estimated_score_range ? (
                  <span>{analytics.estimated_score_range}</span>
                ) : (
                  <span>360–420 <span className="text-xs font-normal text-slate-400">(Pre-Diagnostic)</span></span>
                )}
              </div>
              <p className="text-xs text-slate-300">
                {user?.profile?.diagnostic_status === "completed"
                  ? "Based on diagnostic performance. Train specific skills to reach 750+."
                  : "Complete diagnostic test for calibrated score ranges."}
              </p>
            </div>

            <div className="text-right">
              {user?.profile?.diagnostic_status !== "completed" && (
                <Link href="/diagnostic">
                  <Button size="sm" variant="outline" className="text-xs border-blue-500/40 text-blue-300">
                    Take Diagnostic
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </Card>

        {/* Action Hero Button */}
        <div className="grid grid-cols-2 gap-3">
          <Button
            onClick={() => router.push("/math/practice")}
            className="w-full h-12 bg-blue-600 hover:bg-blue-500 text-white font-semibold flex items-center justify-center gap-2 rounded-xl shadow-lg shadow-blue-500/20"
          >
            <PlayCircle className="w-5 h-5" />
            <span>Start Practice</span>
          </Button>

          <Button
            onClick={() => {
              if (analytics?.recommended_focus_skill && analytics?.recommended_focus_domain) {
                router.push(
                  `/math/practice?domain=${analytics.recommended_focus_domain}&skill=${encodeURIComponent(
                    analytics.recommended_focus_skill
                  )}`
                );
              } else {
                router.push("/math/practice");
              }
            }}
            variant="outline"
            className="w-full h-12 border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-200 font-semibold flex items-center justify-center gap-2 rounded-xl"
          >
            <Zap className="w-5 h-5 text-amber-400" />
            <span>Focus Weak Area</span>
          </Button>
        </div>

        {/* Recommended Focus Card */}
        {analytics?.recommended_focus_skill && (
          <Card className="p-3.5 bg-gradient-to-r from-amber-500/10 via-slate-900 to-slate-900 border border-amber-500/30 flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-400">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Priority Focus Recommendation</span>
              </div>
              <p className="text-xs font-medium text-slate-200">{analytics.recommended_focus_skill}</p>
            </div>
            <Button
              size="sm"
              onClick={() =>
                router.push(
                  `/math/practice?domain=${analytics.recommended_focus_domain}&skill=${encodeURIComponent(
                    analytics.recommended_focus_skill!
                  )}`
                )
              }
              className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs h-8"
            >
              Train
            </Button>
          </Card>
        )}

        {/* Overall Math Performance Metrics */}
        <div className="grid grid-cols-2 gap-2.5">
          <Card className="p-3 bg-slate-900/80 border-slate-800 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <div className="text-base font-bold text-white">
                {isLoading ? <Skeleton className="w-8 h-4" /> : analytics?.total_attempts ?? 0}
              </div>
              <div className="text-[11px] text-slate-400">Questions Answered</div>
            </div>
          </Card>

          <Card className="p-3 bg-slate-900/80 border-slate-800 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <div className="text-base font-bold text-white">
                {isLoading ? <Skeleton className="w-8 h-4" /> : `${analytics?.overall_accuracy ?? 0}%`}
              </div>
              <div className="text-[11px] text-slate-400">Overall Accuracy</div>
            </div>
          </Card>
        </div>

        {/* 4 Canonical Math Domains */}
        <div className="space-y-3 pt-1">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-xs uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5 text-blue-400" />
              <span>Digital SAT Math Domains</span>
            </h2>
            <span className="text-[11px] text-slate-500">4 Domains</span>
          </div>

          {isLoading ? (
            <div className="space-y-2.5">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-28 w-full rounded-xl" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {analytics?.domains.map((dom) => {
                const badge = getMasteryBadge(dom.mastery_level);
                const slug = DOMAIN_SLUGS[dom.domain] || dom.domain.toLowerCase();

                return (
                  <Link key={dom.domain} href={`/math/${slug}`} className="block group">
                    <Card className="p-4 bg-slate-900/80 border-slate-800 hover:border-slate-700 hover:bg-slate-900 transition-all space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <h3 className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors">
                            {dom.title}
                          </h3>
                          <p className="text-xs text-slate-400 line-clamp-1">{dom.description}</p>
                        </div>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${badge.bg} ${badge.text} ${badge.border}`}
                        >
                          {badge.label}
                        </span>
                      </div>

                      {/* Progress & Accuracy bar */}
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">
                            {dom.total_attempts} solved ({dom.correct_attempts} correct)
                          </span>
                          <span className="font-semibold text-slate-200">{dom.accuracy}% accuracy</span>
                        </div>
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-blue-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, Math.max(0, dom.accuracy))}%` }}
                          />
                        </div>
                      </div>

                      {/* Skills count & link */}
                      <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/80 text-slate-400">
                        <span>{dom.skills.length} canonical skills</span>
                        <div className="flex items-center gap-1 text-blue-400 font-semibold group-hover:translate-x-0.5 transition-transform">
                          <span>View skills</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </div>
                      </div>
                    </Card>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
