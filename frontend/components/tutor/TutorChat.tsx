import React, { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Bot,
  ChevronDown,
  Loader2,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { TutorContextBadge } from "@/components/tutor/TutorContextBadge";
import { TutorMessage } from "@/components/tutor/TutorMessage";
import { TutorQuickActions } from "@/components/tutor/TutorQuickActions";
import { api } from "@/lib/api";
import {
  QuickPromptType,
  TutorConversationDetail,
  TutorConversationSummary,
  TutorMode,
} from "@/types/tutor";

interface TutorChatProps {
  initialContextType?: string;
  initialContextId?: string;
}

export const TutorChat: React.FC<TutorChatProps> = ({
  initialContextType = "GENERAL",
  initialContextId,
}) => {
  const [conversations, setConversations] = useState<TutorConversationSummary[]>([]);
  const [activeConversation, setActiveConversation] = useState<TutorConversationDetail | null>(null);
  const [selectedMode, setSelectedMode] = useState<TutorMode>("HINT");
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showDrawer, setShowDrawer] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages, isLoading]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadConversations = async () => {
    try {
      const convList = await api.getTutorConversations();
      setConversations(convList);

      if (convList.length > 0) {
        // If there's an active one matching initialContext, pick it, else pick the first
        const match = convList.find(
          (c) => c.context_type === initialContextType && (!initialContextId || c.context_id === initialContextId)
        );
        const targetId = match ? match.id : convList[0].id;
        loadConversationDetail(targetId);
      } else {
        // Create new conversation
        handleNewConversation();
      }
    } catch (err: any) {
      console.error("Failed to load conversations:", err);
      setErrorMessage("AI Tutor is temporarily unavailable.");
    }
  };

  const loadConversationDetail = async (id: string) => {
    try {
      setErrorMessage(null);
      const detail = await api.getTutorConversation(id);
      setActiveConversation(detail);
      setShowDrawer(false);
    } catch (err) {
      console.error("Failed to load conversation detail:", err);
      setErrorMessage("Could not load conversation history.");
    }
  };

  const handleNewConversation = async () => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      const newConv = await api.createTutorConversation({
        context_type: initialContextType as any,
        context_id: initialContextId,
      });
      setActiveConversation(newConv);
      const list = await api.getTutorConversations();
      setConversations(list);
      setShowDrawer(false);
    } catch (err: any) {
      console.error("Failed to create conversation:", err);
      setErrorMessage("AI Tutor is temporarily unavailable.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteTutorConversation(id);
      const remaining = conversations.filter((c) => c.id !== id);
      setConversations(remaining);
      if (activeConversation?.id === id) {
        if (remaining.length > 0) {
          loadConversationDetail(remaining[0].id);
        } else {
          handleNewConversation();
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  const handleSendMessage = async (textToSend?: string, quickPrompt?: QuickPromptType) => {
    const text = textToSend || inputText;
    if ((!text.trim() && !quickPrompt) || isLoading || !activeConversation) return;

    setInputText("");
    setIsLoading(true);
    setErrorMessage(null);

    // Optimistic user message preview
    const tempUserMsg = {
      id: "temp-" + Date.now(),
      conversation_id: activeConversation.id,
      role: "USER",
      content: quickPrompt ? `[Selected Quick Action: ${quickPrompt}]` : text,
      mode: selectedMode,
      actions: [],
      created_at: new Date().toISOString(),
    };

    setActiveConversation((prev) =>
      prev ? { ...prev, messages: [...prev.messages, tempUserMsg] } : null
    );

    try {
      const assistantMsg = await api.sendTutorMessage(activeConversation.id, {
        content: text,
        mode: selectedMode,
        quick_prompt: quickPrompt,
      });

      // Reload fresh conversation to synchronize IDs and timestamps
      await loadConversationDetail(activeConversation.id);
      // Refresh list to update previews
      api.getTutorConversations().then(setConversations).catch(() => {});
    } catch (err: any) {
      console.error("Failed to send message:", err);
      setErrorMessage(
        err.detail || "AI Tutor is temporarily unavailable. Your progress is safe."
      );
      // Reload active conversation to discard temporary optimistic message on failure
      loadConversationDetail(activeConversation.id);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] max-w-3xl mx-auto">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowDrawer(!showDrawer)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-200 transition-colors"
          >
            <MessageSquare className="w-3.5 h-3.5 text-cyan-400" />
            <span className="truncate max-w-[140px] sm:max-w-[200px]">
              {activeConversation?.title || "New Chat"}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {activeConversation && (
            <TutorContextBadge
              contextType={activeConversation.context_type}
              contextId={activeConversation.context_id}
              subject={activeConversation.subject}
            />
          )}
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={handleNewConversation}
          className="h-8 px-2.5 text-xs flex items-center gap-1 border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-200"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Chat</span>
        </Button>
      </div>

      {/* Conversations Drawer Modal */}
      {showDrawer && (
        <div className="p-3 my-2 rounded-xl bg-slate-900 border border-slate-800 space-y-2 shadow-xl z-20">
          <div className="flex items-center justify-between text-xs font-bold text-slate-400 px-1">
            <span>Recent Conversations</span>
            <span className="text-[10px]">{conversations.length} total</span>
          </div>
          <div className="max-h-48 overflow-y-auto space-y-1 scrollbar-thin">
            {conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => loadConversationDetail(c.id)}
                className={`flex items-center justify-between p-2 rounded-lg text-xs cursor-pointer transition-colors ${
                  activeConversation?.id === c.id
                    ? "bg-cyan-950/40 border border-cyan-500/40 text-cyan-300 font-medium"
                    : "hover:bg-slate-800/60 text-slate-300"
                }`}
              >
                <div className="min-w-0 pr-2">
                  <div className="truncate font-semibold">{c.title || "Conversation"}</div>
                  {c.last_message_preview && (
                    <div className="text-[10px] text-slate-500 truncate">
                      {c.last_message_preview}
                    </div>
                  )}
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(c.id, e)}
                  className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Alert Banner */}
      {errorMessage && (
        <div className="my-2 p-3 rounded-xl bg-rose-950/30 border border-rose-500/40 flex items-start gap-2.5 text-xs text-rose-300">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 font-medium">{errorMessage}</div>
        </div>
      )}

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto py-3 space-y-1 scrollbar-thin">
        {(!activeConversation || activeConversation.messages.length === 0) && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-center">
              <Bot className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">SAT MASTER AI Coach</h3>
              <p className="text-xs text-slate-400 max-w-sm mt-1">
                Ask questions about Math, Reading & Writing, Desmos strategies, or request a customized 1400+ study schedule.
              </p>
            </div>
          </div>
        )}

        {activeConversation?.messages.map((msg) => (
          <TutorMessage key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="flex items-center gap-2.5 my-3 text-slate-400 text-xs">
            <div className="w-7 h-7 rounded-full bg-slate-900 border border-cyan-500/30 flex items-center justify-center">
              <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
            </div>
            <span className="italic">AI Coach is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Bar: Mode Selector, Quick Actions, Input */}
      <div className="pt-2 border-t border-slate-800 space-y-2 bg-slate-950">
        <TutorQuickActions
          onSelectPrompt={(promptType) => handleSendMessage("", promptType)}
          disabled={isLoading}
        />

        {/* Mode Selector Chips */}
        <div className="flex items-center gap-1.5 text-[11px]">
          <span className="text-slate-500 font-semibold px-1">Mode:</span>
          {(["HINT", "EXPLANATION", "CONCEPT", "DESMOS_HELP"] as TutorMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setSelectedMode(mode)}
              className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                selectedMode === mode
                  ? "bg-cyan-500 text-slate-950 shadow-sm shadow-cyan-500/30"
                  : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>

        {/* Text Input Row */}
        <div className="relative flex items-end gap-2 p-1.5 rounded-xl bg-slate-900/90 border border-slate-800 focus-within:border-cyan-500/50 transition-all">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask your SAT question or enter equation (e.g. 2x + 3 = 11)..."
            rows={1}
            maxLength={4000}
            className="flex-1 bg-transparent text-xs sm:text-sm text-slate-100 placeholder-slate-500 p-2 focus:outline-none resize-none max-h-24 scrollbar-none"
          />

          <Button
            size="sm"
            onClick={() => handleSendMessage()}
            disabled={!inputText.trim() || isLoading}
            className="h-9 w-9 p-0 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-500 hover:from-cyan-400 hover:to-indigo-400 text-slate-950 font-bold shrink-0 flex items-center justify-center shadow-md disabled:opacity-40"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
            ) : (
              <Send className="w-4 h-4 text-slate-950" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
