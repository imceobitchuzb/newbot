"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Target, BarChart3, Sparkles, User } from "lucide-react";
import { twMerge } from "tailwind-merge";

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/practice", label: "Practice", icon: Target },
  { href: "/progress", label: "Progress", icon: BarChart3 },
  { href: "/tutor", label: "Tutor", icon: Sparkles },
  { href: "/profile", label: "Profile", icon: User },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Bottom Navigation"
      className="fixed bottom-0 left-0 right-0 z-40 bg-slate-950/90 backdrop-blur-lg border-t border-slate-800/80 px-2 py-1 max-w-md mx-auto"
    >
      <ul className="flex items-center justify-around">
        {navItems.map((item) => {
          const isActive =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <li key={item.href} className="flex-1">
              <Link
                href={item.href}
                className={twMerge(
                  "flex flex-col items-center justify-center min-h-[48px] py-1 px-2 rounded-xl text-[10px] font-medium transition-all",
                  isActive
                    ? "text-cyan-400 font-semibold"
                    : "text-slate-400 hover:text-slate-200"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <div
                  className={twMerge(
                    "p-1 rounded-lg transition-all",
                    isActive ? "bg-cyan-500/15 text-cyan-400 scale-110 shadow-sm" : ""
                  )}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <span className="mt-0.5">{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
