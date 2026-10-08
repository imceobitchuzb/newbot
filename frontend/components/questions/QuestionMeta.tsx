import { Clock, LineChart } from "lucide-react";
import { Question } from "@/types/question";

export interface QuestionMetaProps {
  question: Question;
}

export function QuestionMeta({ question }: QuestionMetaProps) {
  const isMath = question.subject === "MATH";

  const diffColors = {
    EASY: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    MEDIUM: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    HARD: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  };

  const domainLabels: Record<string, string> = {
    ALGEBRA: "Algebra",
    ADVANCED_MATH: "Advanced Math",
    PROBLEM_SOLVING_DATA_ANALYSIS: "Data Analysis",
    GEOMETRY_TRIGONOMETRY: "Geometry & Trig",
    INFORMATION_IDEAS: "Information & Ideas",
    CRAFT_STRUCTURE: "Craft & Structure",
    EXPRESSION_IDEAS: "Expression of Ideas",
    STANDARD_ENGLISH_CONVENTIONS: "Standard English",
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] pb-2 border-b border-slate-800/80">
      <div className="flex items-center gap-1.5 flex-wrap">
        {/* Subject */}
        <span
          className={`px-2 py-0.5 rounded-full font-semibold border ${
            isMath
              ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
          }`}
        >
          {isMath ? "Math" : "Reading & Writing"}
        </span>

        {/* Domain */}
        <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-medium">
          {domainLabels[question.domain] || question.domain}
        </span>

        {/* Difficulty */}
        <span
          className={`px-2 py-0.5 rounded-full font-medium border capitalize ${
            diffColors[question.difficulty] || "text-slate-400"
          }`}
        >
          {question.difficulty.toLowerCase()}
        </span>
      </div>

      <div className="flex items-center gap-2 text-slate-400">
        {isMath && question.desmos_allowed && (
          <span
            title="Desmos Graphing Calculator permitted"
            className="flex items-center gap-1 text-[10px] text-cyan-400 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/40"
          >
            <LineChart className="w-3 h-3" />
            <span>Desmos</span>
          </span>
        )}
        <span className="flex items-center gap-1 text-[10px]">
          <Clock className="w-3 h-3" />
          <span>{question.estimated_time_seconds}s</span>
        </span>
      </div>
    </div>
  );
}
