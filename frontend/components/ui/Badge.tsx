import React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline" | "success" | "warning" | "error" | "primary";
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  className = "",
  variant = "default",
  ...props
}) => {
  const baseClasses =
    "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium transition-colors";

  const variantClasses = {
    default: "bg-slate-800 text-slate-300 border border-slate-700",
    outline: "bg-transparent text-slate-400 border border-slate-800",
    success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30",
    warning: "bg-amber-500/10 text-amber-400 border border-amber-500/30",
    error: "bg-rose-500/10 text-rose-400 border border-rose-500/30",
    primary: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30",
  }[variant];

  return (
    <span className={`${baseClasses} ${variantClasses} ${className}`} {...props}>
      {children}
    </span>
  );
};
