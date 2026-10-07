"use client";

import { useAuth } from "@/features/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardHero } from "@/components/dashboard/DashboardHero";
import { DailyFocus } from "@/components/dashboard/DailyFocus";
import { QuickStats } from "@/components/dashboard/QuickStats";
import { SubjectCards } from "@/components/dashboard/SubjectCard";
import { ToolsSection } from "@/components/dashboard/ToolsSection";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <AppShell>
      {user && (
        <div className="space-y-6">
          <DashboardHero user={user} />
          <DailyFocus user={user} />
          <QuickStats user={user} />
          <SubjectCards />
          <ToolsSection />
        </div>
      )}
    </AppShell>
  );
}
