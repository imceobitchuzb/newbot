"use client";

import Link from "next/link";
import { LineChart, ArrowLeft, Zap } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";

export default function DesmosPage() {
  const tricks = [
    { title: "Find Intersections & Systems", desc: "Type two equations and click intersection points directly." },
    { title: "Find Roots & Zeros", desc: "Inspect points on the x-axis for instantaneous quadratic solutions." },
    { title: "Vertex & Maximums", desc: "Click parabolas directly to read coordinate vertices without completing the square." },
    { title: "Linear Regression (y1 ~ m x1 + b)", desc: "Plug in (x, y) table points to instantly obtain slope and intercept." },
    { title: "Sliders for Constants (a, b, c)", desc: "Visually test parameters when equations have unknown constants." },
  ];

  return (
    <AppShell>
      <div className="space-y-5">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <h1 className="text-sm uppercase tracking-wider font-semibold text-slate-200">
              Desmos Lab
            </h1>
          </div>
          <Link href="/" className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>

        <Card variant="gradient" className="p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-cyan-400 font-semibold">SAT Calculator Weapon</span>
            <span className="text-slate-400">Desmos 101</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The built-in Desmos graphing calculator is the single greatest competitive advantage in Digital SAT Math. Over 60% of algebra and polynomial questions can be solved visually in under 30 seconds.
          </p>
          <div className="pt-1">
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-medium">
              Scheduled for Phase 9 — Interactive Desmos Lab
            </span>
          </div>
        </Card>

        <div className="space-y-2.5">
          <h2 className="text-xs uppercase tracking-wider text-slate-400 font-semibold px-1">
            Core Desmos Tricks
          </h2>

          <div className="space-y-2">
            {tricks.map((trick) => (
              <Card key={trick.title} className="p-3 bg-slate-900/70 border-slate-800 space-y-1">
                <div className="flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-cyan-400" />
                  <h3 className="text-xs font-bold text-slate-200">{trick.title}</h3>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed pl-5.5">
                  {trick.desc}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
