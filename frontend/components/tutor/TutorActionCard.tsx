import React from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, Calculator, RotateCcw, Sparkles, Target } from "lucide-react";
import { TutorActionItem } from "@/types/tutor";

interface TutorActionCardProps {
  action: TutorActionItem;
}

export const TutorActionCard: React.FC<TutorActionCardProps> = ({ action }) => {
  const getIcon = () => {
    switch (action.type) {
      case "PRACTICE_SKILL":
        return <Target className="w-3.5 h-3.5 text-cyan-400" />;
      case "REVIEW_MISTAKE":
        return <RotateCcw className="w-3.5 h-3.5 text-rose-400" />;
      case "OPEN_DESMOS":
        return <Calculator className="w-3.5 h-3.5 text-emerald-400" />;
      case "PRACTICE_ADAPTIVE":
        return <Sparkles className="w-3.5 h-3.5 text-purple-400" />;
      default:
        return <BookOpen className="w-3.5 h-3.5 text-blue-400" />;
    }
  };

  const getBorderColor = () => {
    switch (action.type) {
      case "PRACTICE_SKILL":
        return "border-cyan-500/30 hover:border-cyan-500/60 bg-cyan-950/20";
      case "REVIEW_MISTAKE":
        return "border-rose-500/30 hover:border-rose-500/60 bg-rose-950/20";
      case "OPEN_DESMOS":
        return "border-emerald-500/30 hover:border-emerald-500/60 bg-emerald-950/20";
      case "PRACTICE_ADAPTIVE":
        return "border-purple-500/30 hover:border-purple-500/60 bg-purple-950/20";
      default:
        return "border-slate-800 hover:border-slate-700 bg-slate-900/60";
    }
  };

  const url = action.url || "/";

  return (
    <Link
      href={url}
      className={`block p-2.5 rounded-lg border transition-all ${getBorderColor()}`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1 rounded bg-slate-900 border border-slate-800 shrink-0">
            {getIcon()}
          </div>
          <div className="min-w-0">
            <div className="text-xs font-semibold text-slate-200 truncate">
              {action.title}
            </div>
            {action.description && (
              <div className="text-[10px] text-slate-400 truncate">
                {action.description}
              </div>
            )}
          </div>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
      </div>
    </Link>
  );
};
