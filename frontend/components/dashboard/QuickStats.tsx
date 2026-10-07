import { CheckCircle2, Flame, Award, HelpCircle } from "lucide-react";
import { StatCard } from "@/components/dashboard/StatCard";
import { User } from "@/types/user";

export interface QuickStatsProps {
  user: User;
}

export function QuickStats({ user }: QuickStatsProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
          Performance Overview
        </h2>
        <span className="text-[10px] text-slate-400">Live Telemetry</span>
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        <StatCard
          label="Questions"
          value={0}
          sublabel="Solved so far"
          icon={<HelpCircle className="w-3.5 h-3.5 text-blue-400" />}
        />
        <StatCard
          label="Accuracy"
          value="—"
          sublabel="Calibrates on practice"
          icon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
        />
        <StatCard
          label="Study Streak"
          value="0 days"
          sublabel="Daily habit"
          icon={<Flame className="w-3.5 h-3.5 text-amber-400" />}
        />
        <StatCard
          label="XP Earned"
          value={user.xp || 0}
          sublabel={`Level ${user.level || 1}`}
          icon={<Award className="w-3.5 h-3.5 text-purple-400" />}
        />
      </div>
    </div>
  );
}
