import Link from "next/link";
import { Sparkles, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { User } from "@/types/user";

export interface DashboardHeroProps {
  user: User;
}

export function DashboardHero({ user }: DashboardHeroProps) {
  const diagnosticStatus = user.profile?.diagnostic_status || "not_started";
  const targetScore = user.profile?.target_score || 1400;

  return (
    <Card variant="gradient" className="p-5 relative overflow-hidden space-y-4">
      {/* Top greeting badge */}
      <div className="flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-medium text-slate-200">
            Welcome back, {user.first_name}
          </span>
        </div>
        <span className="px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-semibold">
          Target: {targetScore}+
        </span>
      </div>

      {/* Trajectory score display */}
      <div className="flex items-baseline justify-between pt-1">
        <div>
          <p className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
            {diagnosticStatus === "completed" ? "Calibrated Baseline" : "Estimated Baseline"}
          </p>
          <p className="text-3xl font-extrabold text-slate-300">
            {diagnosticStatus === "completed" && (user.profile?.math_estimate || user.profile?.rw_estimate)
              ? (user.profile.math_estimate || 350) + (user.profile.rw_estimate || 350)
              : 700}
          </p>
          <p className="text-[10px] text-slate-400">
            {diagnosticStatus === "completed" && user.profile?.math_estimate
              ? `M: ~${user.profile.math_estimate} | RW: ~${user.profile.rw_estimate}`
              : "M: ~360 | RW: ~340"}
          </p>
        </div>

        <div className="text-slate-400 font-light text-2xl">➔</div>

        <div className="text-right">
          <p className="text-[11px] uppercase tracking-wider text-cyan-400 font-medium">
            Goal Score
          </p>
          <p className="text-3xl font-extrabold bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            {targetScore}+
          </p>
          <p className="text-[10px] text-slate-400">4-Month Horizon</p>
        </div>
      </div>

      {/* Diagnostic Context & Action */}
      <div className="pt-3 border-t border-slate-800/80 space-y-3">
        {diagnosticStatus === "not_started" && (
          <>
            <p className="text-xs text-slate-300 leading-relaxed">
              Your SAT journey starts here. Take the diagnostic test to uncover your exact algebra, grammar, and pacing weaknesses.
            </p>
            <Link href="/diagnostic" className="block">
              <Button size="md" className="w-full">
                <span>Start Diagnostic</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </>
        )}

        {diagnosticStatus === "in_progress" && (
          <>
            <p className="text-xs text-amber-200 leading-relaxed">
              You have an active diagnostic in progress. Complete it to unlock your personalized study path.
            </p>
            <Link href="/diagnostic" className="block">
              <Button size="md" variant="amber" className="w-full">
                <span>Continue Diagnostic</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </>
        )}

        {diagnosticStatus === "completed" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-300">Diagnostic Calibrated</span>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[11px] font-medium">
                Completed
              </span>
            </div>
            <Link href="/diagnostic/result" className="block">
              <Button size="sm" variant="secondary" className="w-full justify-center text-xs">
                <span>View Diagnostic Report</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </Link>
          </div>
        )}
      </div>
    </Card>
  );
}
