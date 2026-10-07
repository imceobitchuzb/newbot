"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { TutorChat } from "@/components/tutor/TutorChat";

function TutorPageContent() {
  const searchParams = useSearchParams();
  const contextType = searchParams.get("context") || "GENERAL";
  const contextId = searchParams.get("id") || undefined;

  return (
    <AppShell>
      <TutorChat
        initialContextType={contextType}
        initialContextId={contextId}
      />
    </AppShell>
  );
}

export default function TutorPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-4">
          <div className="text-center space-y-3">
            <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mx-auto" />
            <p className="text-xs text-slate-400">Loading AI SAT Tutor...</p>
          </div>
        </div>
      }
    >
      <TutorPageContent />
    </Suspense>
  );
}
