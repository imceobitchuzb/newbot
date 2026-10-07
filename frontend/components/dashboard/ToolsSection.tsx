import Link from "next/link";
import { LineChart, ClipboardCheck, Clock, ChevronRight, BookOpen } from "lucide-react";
import { Card } from "@/components/ui/Card";

export function ToolsSection() {
  const tools = [
    {
      title: "Mistake Book",
      description: "Deliberately remediate errors and reach 1400+ mastery.",
      icon: BookOpen,
      href: "/mistakes",
      iconColor: "text-rose-400",
      bgColor: "bg-rose-600/15",
      borderColor: "border-rose-500/20",
      badge: "Remediation",
    },
    {
      title: "Desmos Lab",
      description: "Master SAT calculator strategies, regressions & visual intersections.",
      icon: LineChart,
      href: "/desmos",
      iconColor: "text-cyan-400",
      bgColor: "bg-cyan-600/15",
      borderColor: "border-cyan-500/20",
      badge: "Strategies",
    },
    {
      title: "Diagnostic",
      description: "Find your current level and discover weak areas.",
      icon: ClipboardCheck,
      href: "/diagnostic",
      iconColor: "text-blue-400",
      bgColor: "bg-blue-600/15",
      borderColor: "border-blue-500/20",
      badge: "Baseline",
    },
    {
      title: "Full SAT",
      description: "Simulate the complete Digital SAT experience.",
      icon: Clock,
      href: "/full-sat",
      iconColor: "text-purple-400",
      bgColor: "bg-purple-600/15",
      borderColor: "border-purple-500/20",
      badge: "Simulation",
    },
  ];

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
          SAT Tools
        </h2>
        <span className="text-[10px] text-slate-400">Preparation Suite</span>
      </div>

      <div className="grid grid-cols-1 gap-2.5">
        {tools.map((tool) => {
          const Icon = tool.icon;
          return (
            <Link key={tool.title} href={tool.href} className="block group">
              <Card
                variant="interactive"
                className="p-3.5 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-9 h-9 rounded-xl ${tool.bgColor} border ${tool.borderColor} flex items-center justify-center ${tool.iconColor}`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-slate-100 group-hover:text-cyan-300 transition">
                        {tool.title}
                      </h3>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-medium">
                        {tool.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">{tool.description}</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-slate-300 group-hover:translate-x-0.5 transition" />
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
