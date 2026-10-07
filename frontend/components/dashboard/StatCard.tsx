import { ReactNode } from "react";
import { Card } from "@/components/ui/Card";

export interface StatCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  icon?: ReactNode;
}

export function StatCard({ label, value, sublabel, icon }: StatCardProps) {
  return (
    <Card className="p-3 bg-slate-900/60 border-slate-800/70 hover:border-slate-700/80 transition flex flex-col justify-between">
      <div className="flex items-center justify-between text-slate-400 mb-1">
        <span className="text-[11px] font-medium uppercase tracking-wider">{label}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <div>
        <p className="text-xl font-bold text-slate-100 tracking-tight">{value}</p>
        {sublabel && <p className="text-[10px] text-slate-400 mt-0.5">{sublabel}</p>}
      </div>
    </Card>
  );
}
