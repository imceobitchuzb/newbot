import React from "react";
import { AlertCircle, Calculator, HelpCircle, Layers, RotateCcw, Sparkles } from "lucide-react";
import { TutorContextType } from "@/types/tutor";

interface TutorContextBadgeProps {
  contextType: TutorContextType | string;
  contextId?: string | null;
  subject?: string | null;
}

export const TutorContextBadge: React.FC<TutorContextBadgeProps> = ({
  contextType,
  contextId,
  subject,
}) => {
  const getLabel = () => {
    switch (contextType) {
      case "QUESTION":
        return `Question Context ${contextId ? `#${contextId.slice(0, 6)}` : ""}`;
      case "MISTAKE":
        return "Mistake Remediation";
      case "DESMOS":
        return `Desmos Strategy: ${contextId || "General"}`;
      case "DIAGNOSTIC":
        return "Diagnostic Analysis";
      case "ADAPTIVE":
        return "Adaptive Learning";
      case "SKILL":
        return `Topic: ${contextId || "Skill"}`;
      default:
        return "General SAT Coaching";
    }
  };

  const getIcon = () => {
    switch (contextType) {
      case "QUESTION":
        return <HelpCircle className="w-3 h-3 text-cyan-400" />;
      case "MISTAKE":
        return <RotateCcw className="w-3 h-3 text-rose-400" />;
      case "DESMOS":
        return <Calculator className="w-3 h-3 text-emerald-400" />;
      case "DIAGNOSTIC":
        return <AlertCircle className="w-3 h-3 text-amber-400" />;
      case "ADAPTIVE":
        return <Sparkles className="w-3 h-3 text-purple-400" />;
      default:
        return <Layers className="w-3 h-3 text-blue-400" />;
    }
  };

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-medium text-slate-300">
      {getIcon()}
      <span>{getLabel()}</span>
      {subject && (
        <span className="text-[10px] text-slate-500 font-mono">[{subject}]</span>
      )}
    </div>
  );
};
