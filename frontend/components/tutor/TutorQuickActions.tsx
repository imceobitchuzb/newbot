import React from "react";
import {
  BookOpen,
  Calculator,
  Compass,
  GraduationCap,
  RotateCcw,
  Sparkles,
  Zap,
} from "lucide-react";
import { QuickPromptType } from "@/types/tutor";

interface TutorQuickActionsProps {
  onSelectPrompt: (promptType: QuickPromptType) => void;
  disabled?: boolean;
}

export const TutorQuickActions: React.FC<TutorQuickActionsProps> = ({
  onSelectPrompt,
  disabled,
}) => {
  const actions: { type: QuickPromptType; label: string; icon: React.ReactNode }[] = [
    {
      type: "WEAKEST_SKILL",
      label: "Explain my weakest skill",
      icon: <Sparkles className="w-3 h-3 text-cyan-400" />,
    },
    {
      type: "MISTAKE_REVIEW",
      label: "Review my mistake patterns",
      icon: <RotateCcw className="w-3 h-3 text-rose-400" />,
    },
    {
      type: "DESMOS_GUIDE",
      label: "How to master Desmos",
      icon: <Calculator className="w-3 h-3 text-emerald-400" />,
    },
    {
      type: "DIAGNOSTIC_ANALYSIS",
      label: "Analyze my diagnostic",
      icon: <Compass className="w-3 h-3 text-amber-400" />,
    },
    {
      type: "SAT_MATH_STRATEGY",
      label: "Math 700+ Speed Tactics",
      icon: <Zap className="w-3 h-3 text-indigo-400" />,
    },
    {
      type: "STUDY_PLAN",
      label: "Generate 1400+ weekly plan",
      icon: <GraduationCap className="w-3 h-3 text-fuchsia-400" />,
    },
  ];

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
      {actions.map((act) => (
        <button
          key={act.type}
          onClick={() => onSelectPrompt(act.type)}
          disabled={disabled}
          className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 hover:border-slate-700 active:scale-95 text-xs text-slate-300 font-medium transition-all disabled:opacity-50 disabled:pointer-events-none"
        >
          {act.icon}
          <span>{act.label}</span>
        </button>
      ))}
    </div>
  );
};
