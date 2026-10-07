"use client";

import { use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ChevronRight,
  BrainCircuit,
  PlayCircle,
  Zap,
  Target,
  CheckCircle2,
  AlertCircle,
  Activity,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { api } from "@/lib/api";
import { DomainAnalyticsOut, SkillMastery } from "@/types/math";

const SLUG_TO_DOMAIN: Record<string, string> = {
  algebra: "ALGEBRA",
  "advanced-math": "ADVANCED_MATH",
  "problem-solving": "PROBLEM_SOLVING_DATA_ANALYSIS",
  "geometry-trig": "GEOMETRY_TRIGONOMETRY",
  ALGEBRA: "ALGEBRA",
  ADVANCED_MATH: "ADVANCED_MATH",
  PROBLEM_SOLVING_DATA_ANALYSIS: "PROBLEM_SOLVING_DATA_ANALYSIS",
  GEOMETRY_TRIGONOMETRY: "GEOMETRY_TRIGONOMETRY",
};

export default function DomainDetailPage({
  params,
}: {
  params: Promise<{ domain: string }>;
}) {
  const router = useRouter();
  const resolvedParams = use(params);
  const rawSlug = resolvedParams.domain;
  const canonicalDomain = SLUG_TO_DOMAIN[rawSlug.toLowerCase()] || rawSlug.toUpperCase();

  const {
    data: domainData,
    isLoading,
    isError,
  } = useQuery<DomainAnalyticsOut>({
    queryKey: ["math-domain", canonicalDomain],
    queryFn: () => api.getDomainAnalytics(canonicalDomain),
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

  if (isError) {
    return (
      <AppShell>
        <div className="space-y-4 p-4 text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
          <h2 className="text-base font-bold text-white">Domain Not Found</h2>
          <p className="text-xs text-slate-400">Could not find domain matching &quot;{rawSlug}&quot;</p>
          <Link href="/math">
            <Button variant="outline" size="sm">Back to Math Hub</Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  const badge = domainData ? getMasteryBadge(domainData.mastery_level) : null;

  return (
    <AppShell>
      <div className="space-y-5 pb-8">
        {/* Navigation header */}
        <div className="flex items-center justify-between px-1">
          <Link
            href="/math"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Math Hub</span>
          </Link>
          <span className="text-[11px] text-slate-500 font-mono uppercase">{canonicalDomain}</span>
        </div>

        {/* Domain Overview Card */}
        {isLoading || !domainData ? (
          <Skeleton className="h-40 w-full rounded-2xl" />
        ) : (
          <Card variant="gradient" className="p-4 space-y-3 border border-blue-500/20">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <h1 className="text-lg font-black text-white tracking-tight">{domainData.title}</h1>
                <p className="text-xs text-slate-300 leading-relaxed">{domainData.description}</p>
              </div>
              {badge && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold border shrink-0 ${badge.bg} ${badge.text} ${badge.border}`}
                >
                  {badge.label}
                </span>
              )}
            </div>

            {/* Performance Bar */}
            <div className="space-y-1 pt-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">
                  {domainData.total_attempts} attempts ({domainData.correct_attempts} correct)
                </span>
                <span className="font-bold text-white">{domainData.accuracy}% accuracy</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(0, domainData.accuracy))}%` }}
                />
              </div>
            </div>

            {/* Quick Practice Domain CTA */}
            <div className="pt-2">
              <Button
                onClick={() => router.push(`/math/practice?domain=${canonicalDomain}`)}
                className="w-full h-10 bg-blue-600 hover:bg-blue-500 text-white font-semibold flex items-center justify-center gap-2 rounded-xl text-xs"
              >
                <PlayCircle className="w-4 h-4" />
                <span>Practice All {domainData.title}</span>
              </Button>
            </div>
          </Card>
        )}

        {/* Skills list */}
        <div className="space-y-3 pt-1">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-xs uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5 text-blue-400" />
              <span>Canonical Skills Breakdown</span>
            </h2>
            <span className="text-[11px] text-slate-500">{domainData?.skills.length ?? 0} skills</span>
          </div>

          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Skeleton key={i} className="h-20 w-full rounded-xl" />
              ))}
            </div>
          ) : (
            <div className="space-y-2.5">
              {domainData?.skills.map((skill) => {
                const sBadge = getMasteryBadge(skill.mastery_level);

                return (
                  <Card
                    key={skill.skill}
                    className="p-3.5 bg-slate-900/80 border-slate-800 hover:border-slate-700 transition-all space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <h3 className="text-xs font-bold text-white leading-snug">{skill.skill}</h3>
                        <p className="text-[11px] text-slate-400">
                          {skill.attempts > 0 ? (
                            <span>
                              {skill.attempts} attempts • <span className="text-slate-200 font-semibold">{skill.accuracy}%</span>
                            </span>
                          ) : (
                            <span>No attempts recorded</span>
                          )}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span
                          className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${sBadge.bg} ${sBadge.text} ${sBadge.border}`}
                        >
                          {sBadge.label}
                        </span>

                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            router.push(
                              `/math/practice?domain=${canonicalDomain}&skill=${encodeURIComponent(skill.skill)}`
                            )
                          }
                          className="h-7 px-2 text-[11px] font-semibold border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200"
                        >
                          Train
                        </Button>
                      </div>
                    </div>

                    {/* Accuracy bar */}
                    {skill.attempts > 0 && (
                      <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            skill.accuracy >= 80
                              ? "bg-emerald-500"
                              : skill.accuracy >= 60
                              ? "bg-blue-500"
                              : "bg-amber-500"
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, skill.accuracy))}%` }}
                        />
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
