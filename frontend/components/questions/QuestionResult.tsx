import { CheckCircle2, XCircle, Zap, Lightbulb, Clock } from "lucide-react";
import { MathText } from "@/components/ui/MathText";
import { Card } from "@/components/ui/Card";
import { AttemptResult } from "@/types/question";

export interface QuestionResultProps {
  result: AttemptResult;
}

export function QuestionResult({ result }: QuestionResultProps) {
  const isCorrect = result.is_correct;

  return (
    <div className="space-y-3 pt-2">
      {/* Banner */}
      <div
        className={`p-3.5 rounded-xl border flex items-center justify-between ${
          isCorrect
            ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
            : "bg-rose-950/40 border-rose-500/40 text-rose-300"
        }`}
      >
        <div className="flex items-center gap-2">
          {isCorrect ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <XCircle className="w-5 h-5 text-rose-400" />
          )}
          <div>
            <p className="text-xs font-bold">
              {isCorrect ? "Correct! +10 XP" : "Incorrect"}
            </p>
            <p className="text-[11px] opacity-80">
              {isCorrect
                ? "Skill concept reinforced successfully."
                : "Review the step-by-step resolution below."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 text-[11px] opacity-75">
          <Clock className="w-3.5 h-3.5" />
          <span>{result.time_spent_seconds}s</span>
        </div>
      </div>

      {/* Detailed Step-by-Step Explanation */}
      <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <span>Explanation</span>
        </h4>
        <div className="text-xs text-slate-200">
          <MathText content={result.explanation} />
        </div>
      </Card>

      {/* SAT Shortcut Card if present */}
      {result.sat_shortcut && (
        <Card className="p-3.5 bg-blue-950/30 border-blue-800/40 space-y-1.5">
          <div className="flex items-center gap-1.5 text-cyan-400 text-xs font-semibold">
            <Zap className="w-3.5 h-3.5" />
            <span>SAT Shortcut</span>
          </div>
          <div className="text-xs text-cyan-200 leading-relaxed">
            <MathText content={result.sat_shortcut} />
          </div>
        </Card>
      )}

      {/* Socratic Hint if present */}
      {result.hint && (
        <Card className="p-3 bg-slate-950/60 border-slate-800/80 space-y-1">
          <div className="flex items-center gap-1.5 text-amber-400 text-xs font-medium">
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Key Takeaway</span>
          </div>
          <div className="text-xs text-slate-300">
            <MathText content={result.hint} />
          </div>
        </Card>
      )}
    </div>
  );
}
