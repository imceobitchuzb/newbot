import Link from "next/link";
import { Calculator, BookOpen, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function SubjectCards() {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
          Core Domains
        </h2>
        <span className="text-[10px] text-slate-400">8 SAT Domains</span>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {/* Math Subject Card */}
        <Card className="p-4 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-blue-600/15 border border-blue-500/20 flex items-center justify-center text-blue-400 shadow-sm">
                <Calculator className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">Math</h3>
                <p className="text-[10px] text-slate-400">Target: 720+ (Current ~360)</p>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-medium border border-blue-500/20">
              4 Domains
            </span>
          </div>

          <ul className="text-xs text-slate-300 space-y-1.5 pl-1">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              <span>Algebra (Linear equations, graphs, systems)</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              <span>Advanced Math (Quadratics, polynomials, exponents)</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              <span>Problem-Solving & Data Analysis (Percentages, ratios)</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              <span>Geometry & Trigonometry (Triangles, circles, trig)</span>
            </li>
          </ul>

          <Link href="/math" className="block pt-1">
            <Button variant="secondary" size="sm" className="w-full justify-between">
              <span>Practice Math</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </Button>
          </Link>
        </Card>

        {/* Reading & Writing Subject Card */}
        <Card className="p-4 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-emerald-600/15 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-sm">
                <BookOpen className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">Reading & Writing</h3>
                <p className="text-[10px] text-slate-400">Target: 680+ (Current ~340)</p>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-medium border border-emerald-500/20">
              4 Domains
            </span>
          </div>

          <ul className="text-xs text-slate-300 space-y-1.5 pl-1">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Information & Ideas (Central claim, inference, evidence)</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Craft & Structure (Words in context, text structure)</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Expression of Ideas (Transitions, rhetorical synthesis)</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Standard English Conventions (Boundaries, grammar rules)</span>
            </li>
          </ul>

          <Link href="/reading-writing" className="block pt-1">
            <Button variant="secondary" size="sm" className="w-full justify-between">
              <span>Practice Reading & Writing</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </Button>
          </Link>
        </Card>
      </div>
    </div>
  );
}
