"use client";

import { useEffect, useState } from "react";
import { ArrowRight, BookOpen, Clock } from "lucide-react";
import { MathText } from "@/components/ui/MathText";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { AnswerOption } from "@/components/questions/AnswerOption";
import { QuestionMeta } from "@/components/questions/QuestionMeta";
import { QuestionResult } from "@/components/questions/QuestionResult";
import { api } from "@/lib/api";
import { AttemptResult, Question } from "@/types/question";

export interface QuestionCardProps {
  question: Question;
  onNextQuestion?: () => void;
}

export function QuestionCard({ question, onNextQuestion }: QuestionCardProps) {
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  // Per-question timer
  useEffect(() => {
    if (result) return; // Stop timer upon answer submission

    const interval = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [result]);

  const handleSubmit = async () => {
    if (!selectedOptionId || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const attemptResult = await api.submitAttempt(question.id, {
        selected_option_id: selectedOptionId,
        time_spent_seconds: secondsElapsed,
      });
      setResult(attemptResult);
    } catch (err: any) {
      console.error("Failed to submit attempt:", err);
      alert(err.message || "Could not submit answer.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="p-4 space-y-4 bg-slate-900/90 border-slate-800 shadow-xl">
      {/* Question metadata header */}
      <QuestionMeta question={question} />

      {/* Reading Passage if attached */}
      {question.passage && (
        <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300 space-y-2 max-h-60 overflow-y-auto">
          <div className="flex items-center gap-1.5 text-slate-400 font-semibold text-[11px]">
            <BookOpen className="w-3.5 h-3.5" />
            <span>{question.passage.title || "Passage"}</span>
          </div>
          <p className="leading-relaxed whitespace-pre-wrap">{question.passage.passage_text}</p>
        </div>
      )}

      {/* Question Text */}
      <div className="text-sm text-slate-100 font-medium py-1">
        <MathText content={question.question_text} />
      </div>

      {/* Answer Options */}
      <div className="space-y-2 pt-1">
        {question.options.map((option) => (
          <AnswerOption
            key={option.id}
            option={option}
            isSelected={selectedOptionId === option.id}
            onSelect={(id) => setSelectedOptionId(id)}
            isSubmitted={!!result}
            isCorrect={result?.is_correct}
            isAnswerKey={result?.correct_option_id === option.id}
          />
        ))}
      </div>

      {/* Action footer */}
      {!result ? (
        <div className="pt-2 flex items-center justify-between">
          <div className="flex items-center gap-1 text-slate-400 text-xs font-mono">
            <Clock className="w-3.5 h-3.5" />
            <span>{secondsElapsed}s</span>
          </div>

          <Button
            size="md"
            variant="primary"
            disabled={!selectedOptionId || isSubmitting}
            isLoading={isSubmitting}
            onClick={handleSubmit}
            className="px-6"
          >
            <span>Submit Answer</span>
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <QuestionResult result={result} />

          {onNextQuestion && (
            <div className="pt-2">
              <Button
                size="md"
                variant="primary"
                onClick={onNextQuestion}
                className="w-full justify-center"
              >
                <span>Next Question</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
