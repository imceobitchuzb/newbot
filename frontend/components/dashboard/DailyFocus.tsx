import Link from "next/link";
import { Compass, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { User } from "@/types/user";

export interface DailyFocusProps {
  user: User;
}

export function DailyFocus({ user }: DailyFocusProps) {
  const diagnosticStatus = user.profile?.diagnostic_status || "not_started";

  return (
    <Card className="p-4 bg-slate-900/70 border-slate-800 space-y-2.5">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
          <Compass className="w-4 h-4" />
          <span>Today&apos;s Focus</span>
        </div>
        <span className="text-[10px] text-slate-400">Step 1 of 4-Month Plan</span>
      </div>

      <p className="text-xs text-slate-300 leading-relaxed">
        {diagnosticStatus === "not_started"
          ? "Complete the baseline diagnostic to reveal high-yield topics and initiate adaptive question routing."
          : "Adaptive daily drills will be prioritized automatically as questions are solved."}
      </p>

      {diagnosticStatus === "not_started" && (
        <Link
          href="/diagnostic"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition pt-1"
        >
          <span>Take 30-min Diagnostic</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      )}
    </Card>
  );
}
