import { CheckCircle2, XCircle } from "lucide-react";
import { twMerge } from "tailwind-merge";
import { MathText } from "@/components/ui/MathText";
import { QuestionOption } from "@/types/question";

export interface AnswerOptionProps {
  option: QuestionOption;
  isSelected: boolean;
  onSelect: (optionId: string) => void;
  isSubmitted: boolean;
  isCorrect?: boolean; // defined after submission for the selected or correct option
  isAnswerKey?: boolean; // true if this option was the correct answer
}

export function AnswerOption({
  option,
  isSelected,
  onSelect,
  isSubmitted,
  isCorrect,
  isAnswerKey,
}: AnswerOptionProps) {
  let stateStyles =
    "bg-slate-900/70 border-slate-800 text-slate-200 hover:border-slate-700 hover:bg-slate-850";
  let badgeStyles = "bg-slate-800 text-slate-300 border-slate-700";

  if (!isSubmitted && isSelected) {
    stateStyles =
      "bg-blue-600/15 border-blue-500 text-blue-100 shadow-md shadow-blue-500/10 ring-1 ring-blue-500";
    badgeStyles = "bg-blue-600 text-white border-blue-500";
  } else if (isSubmitted) {
    if (isAnswerKey) {
      stateStyles =
        "bg-emerald-500/15 border-emerald-500 text-emerald-100 ring-1 ring-emerald-500";
      badgeStyles = "bg-emerald-600 text-white border-emerald-500";
    } else if (isSelected && !isCorrect) {
      stateStyles =
        "bg-rose-500/15 border-rose-500 text-rose-100 ring-1 ring-rose-500";
      badgeStyles = "bg-rose-600 text-white border-rose-500";
    } else {
      stateStyles = "bg-slate-950/40 border-slate-900 text-slate-500 opacity-60";
      badgeStyles = "bg-slate-900 text-slate-500 border-slate-800";
    }
  }

  return (
    <button
      type="button"
      disabled={isSubmitted}
      onClick={() => onSelect(option.id)}
      className={twMerge(
        "w-full text-left p-3.5 rounded-xl border transition-all flex items-start gap-3 select-none active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
        stateStyles
      )}
    >
      <div
        className={twMerge(
          "w-6 h-6 rounded-lg font-bold text-xs flex items-center justify-center shrink-0 border mt-0.5",
          badgeStyles
        )}
      >
        {option.label}
      </div>

      <div className="flex-1 text-xs leading-relaxed pt-0.5">
        <MathText content={option.text} />
      </div>

      {isSubmitted && isAnswerKey && (
        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
      )}
      {isSubmitted && isSelected && !isCorrect && (
        <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
      )}
    </button>
  );
}
