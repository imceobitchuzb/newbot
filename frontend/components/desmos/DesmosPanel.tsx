"use client";

import React, { useState } from "react";
import {
  Calculator,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
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
  defaultOpen?: boolean;
}

export const DesmosPanel: React.FC<DesmosPanelProps> = ({
  status,
  reason,
  techniqueTitle,
  techniqueSlug,
  desmosUsed = true,
  onToggleDesmosUsed,
  defaultOpen = true,
}) => {
  // Desmos is embedded directly inside by default!
  const [showCalculator, setShowCalculator] = useState(defaultOpen);
  const [isExpanded, setIsExpanded] = useState(false);

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

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-3">
      {/* Header & Badges */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Desmos Digital SAT Engine
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

      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowCalculator(!showCalculator)}
            className="text-xs border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 flex items-center gap-1.5 h-8 font-semibold"
          >
            <Calculator className="w-3.5 h-3.5 text-cyan-400" />
            <span>{showCalculator ? "Hide Calculator" : "Show Calculator"}</span>
            {showCalculator ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </Button>

          {showCalculator && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 h-8"
            >
              {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
              <span>{isExpanded ? "Compact" : "Expand"}</span>
            </Button>
          )}
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
            <span>{desmosUsed ? "Desmos Active" : "Manual Mode"}</span>
          </button>
        )}
      </div>

      {/* Official Embedded Calculator — Directly INSIDE the app */}
      {showCalculator && (
        <div className="mt-2 pt-2 border-t border-slate-800/80 space-y-1.5">
          <div
            className={`w-full rounded-xl overflow-hidden border border-cyan-500/30 bg-slate-950 relative transition-all duration-200 ${
              isExpanded ? "h-[500px]" : "h-80 sm:h-96"
            }`}
          >
            <iframe
              src="https://www.desmos.com/calculator"
              title="Official Desmos Digital SAT Calculator"
              className="w-full h-full border-0"
              sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
              loading="lazy"
            />
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-500 px-1">
            <span>Official Embedded Calculator (Same engine as College Board Bluebook)</span>
            <span className="text-cyan-400/80 font-mono">Real-time Graphing</span>
          </div>
        </div>
      )}
    </div>
  );
};
