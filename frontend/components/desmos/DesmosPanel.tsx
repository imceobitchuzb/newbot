"use client";

import React, { useState } from "react";
import {
  Calculator,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Eye,
  EyeOff,
  Lightbulb,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface DesmosPanelProps {
  status: "RECOMMENDED" | "ALLOWED" | "FORBIDDEN";
  reason: string;
  techniqueTitle?: string | null;
  techniqueSlug?: string | null;
  desmosUsed?: boolean;
  onToggleDesmosUsed?: (used: boolean) => void;
}

export const DesmosPanel: React.FC<DesmosPanelProps> = ({
  status,
  reason,
  techniqueTitle,
  techniqueSlug,
  desmosUsed = true,
  onToggleDesmosUsed,
}) => {
  const [showCalculator, setShowCalculator] = useState(false);

  const badgeVariant =
    status === "RECOMMENDED"
      ? "success"
      : status === "ALLOWED"
      ? "warning"
      : "error";

  const badgeText =
    status === "RECOMMENDED"
      ? "Desmos Recommended"
      : status === "ALLOWED"
      ? "Desmos Allowed"
      : "No Desmos";

  const openExternalCalculator = () => {
    window.open("https://www.desmos.com/calculator", "_blank", "noopener,noreferrer");
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-3">
      {/* Header & Badges */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Desmos Strategy
          </span>
          <Badge variant={badgeVariant} className="text-[10px] font-bold">
            {badgeText}
          </Badge>
        </div>

        {techniqueTitle && (
          <span className="text-[11px] text-cyan-400 font-medium hidden sm:inline">
            {techniqueTitle}
          </span>
        )}
      </div>

      {/* Rationale */}
      <p className="text-xs text-slate-300 leading-relaxed">
        {reason}
      </p>

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={openExternalCalculator}
            className="text-xs border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 flex items-center gap-1.5 h-8"
          >
            <Calculator className="w-3.5 h-3.5 text-cyan-400" />
            <span>Open Desmos Calculator</span>
            <ExternalLink className="w-3 h-3 opacity-70" />
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowCalculator(!showCalculator)}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 h-8"
          >
            {showCalculator ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{showCalculator ? "Hide Embed" : "Embed View"}</span>
          </Button>
        </div>

        {onToggleDesmosUsed && (
          <button
            type="button"
            onClick={() => onToggleDesmosUsed(!desmosUsed)}
            className={`text-[11px] px-2.5 py-1 rounded transition-colors flex items-center gap-1.5 font-medium ${
              desmosUsed
                ? "bg-slate-800 text-slate-400 hover:text-slate-200"
                : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
            }`}
          >
            {desmosUsed ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
            <span>{desmosUsed ? "Try Without Desmos" : "Manual Mode Active"}</span>
          </button>
        )}
      </div>

      {/* Embedded Calculator iFrame (safe toggle) */}
      {showCalculator && (
        <div className="mt-2 pt-2 border-t border-slate-800/80">
          <div className="w-full h-80 rounded-lg overflow-hidden border border-slate-800 bg-slate-950 relative">
            <iframe
              src="https://www.desmos.com/calculator"
              title="Desmos Graphing Calculator"
              className="w-full h-full border-0"
              sandbox="allow-scripts allow-same-origin allow-popups"
            />
          </div>
          <p className="text-[10px] text-slate-500 mt-1 text-center">
            Official Desmos Graphing Calculator • Same tool embedded in Bluebook Digital SAT
          </p>
        </div>
      )}
    </div>
  );
};
