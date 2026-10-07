"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, Calculator, Play, Zap } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { DesmosTechnique } from "@/types/desmos";

interface TechniqueCardProps {
  technique: DesmosTechnique;
  onPractice?: (slug: string) => void;
}

export const TechniqueCard: React.FC<TechniqueCardProps> = ({
  technique,
  onPractice,
}) => {
  const diffBadgeVariant =
    technique.difficulty === "EASY"
      ? "success"
      : technique.difficulty === "MEDIUM"
      ? "warning"
      : "error";

  return (
    <Card className="p-4 bg-slate-900/80 border-slate-800 hover:border-cyan-500/40 transition-all flex flex-col justify-between space-y-3">
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <Badge variant={diffBadgeVariant} className="text-[10px] uppercase font-bold tracking-wider">
            {technique.difficulty}
          </Badge>
          <span className="text-[10px] text-slate-500 font-mono uppercase">
            {technique.technique_type.replace(/_/g, " ")}
          </span>
        </div>

        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span>{technique.title}</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed line-clamp-2">
            {technique.description}
          </p>
        </div>
      </div>

      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
        <div className="text-[11px] text-slate-400 flex items-center gap-2">
          <span>{technique.question_count} SAT Questions</span>
          {technique.practiced_count > 0 && (
            <span className="text-cyan-400 font-semibold">
              • {technique.accuracy_percent}% Acc ({technique.practiced_count})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/desmos/${technique.slug}`}
            className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium px-2 py-1 rounded hover:bg-cyan-500/10 transition-colors"
          >
            <BookOpen className="w-3 h-3" />
            <span>Learn</span>
          </Link>
          <Link
            href={`/desmos/practice?technique=${technique.slug}`}
            className="text-xs bg-cyan-600 hover:bg-cyan-500 text-white font-medium px-2.5 py-1 rounded flex items-center gap-1 transition-colors shadow-sm"
          >
            <Play className="w-3 h-3 fill-white" />
            <span>Drill</span>
          </Link>
        </div>
      </div>
    </Card>
  );
};
