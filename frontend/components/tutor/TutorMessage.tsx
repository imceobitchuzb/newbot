import React from "react";
import { Bot, User as UserIcon, Zap } from "lucide-react";
import { MathText } from "@/components/ui/MathText";
import { Badge } from "@/components/ui/Badge";
import { TutorActionCard } from "@/components/tutor/TutorActionCard";
import { TutorMessage as TutorMessageType } from "@/types/tutor";

interface TutorMessageProps {
  message: TutorMessageType;
}

export const TutorMessage: React.FC<TutorMessageProps> = ({ message }) => {
  const isUser = message.role === "USER";

  const getModeBadge = (mode?: string | null) => {
    if (!mode) return null;
    switch (mode) {
      case "HINT":
        return <Badge variant="warning">HINT</Badge>;
      case "EXPLANATION":
        return <Badge variant="primary">EXPLANATION</Badge>;
      case "SOLUTION":
        return <Badge variant="success">SOLUTION</Badge>;
      case "DESMOS_HELP":
        return <Badge variant="default">DESMOS</Badge>;
      case "CONCEPT":
        return <Badge variant="outline">CONCEPT</Badge>;
      default:
        return null;
    }
  };

  if (isUser) {
    return (
      <div className="flex justify-end gap-2 my-3">
        <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl rounded-tr-sm bg-gradient-to-br from-indigo-600 to-cyan-600 text-white p-3.5 shadow-md shadow-indigo-950/20">
          <div className="text-xs sm:text-sm whitespace-pre-wrap leading-relaxed font-sans">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start gap-2.5 my-3">
      <div className="w-7 h-7 rounded-full bg-slate-900 border border-cyan-500/30 flex items-center justify-center shrink-0 mt-0.5">
        <Bot className="w-4 h-4 text-cyan-400" />
      </div>

      <div className="max-w-[88%] sm:max-w-[80%] space-y-2.5">
        <div className="rounded-2xl rounded-tl-sm bg-slate-900/90 border border-slate-800/80 p-4 shadow-sm">
          <div className="flex items-center justify-between gap-2 mb-2 pb-1.5 border-b border-slate-800/50">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-bold text-cyan-400">SAT MASTER AI</span>
              {getModeBadge(message.mode)}
            </div>
            <span className="text-[10px] text-slate-500">
              {new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>

          <div className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans space-y-2">
            <MathText text={message.content} />
          </div>
        </div>

        {/* Action cards if present */}
        {message.actions && message.actions.length > 0 && (
          <div className="space-y-1.5 pt-0.5">
            <div className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
              <Zap className="w-3 h-3 text-cyan-400" />
              <span>Recommended Next Steps:</span>
            </div>
            {message.actions.map((action, idx) => (
              <TutorActionCard key={idx} action={action} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
