import { HTMLAttributes, forwardRef } from "react";
import { twMerge } from "tailwind-merge";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "interactive" | "gradient";
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", children, ...props }, ref) => {
    const variantStyles = {
      default: "bg-slate-900/80 border border-slate-800/80 shadow-md",
      elevated: "bg-slate-900/90 border border-slate-800 shadow-xl backdrop-blur-sm",
      interactive:
        "bg-slate-900/70 border border-slate-800/80 hover:border-slate-700/90 hover:bg-slate-900 transition-all active:scale-[0.99] cursor-pointer",
      gradient:
        "bg-gradient-to-b from-slate-900/95 to-slate-900/60 border border-slate-800/90 shadow-xl",
    };

    return (
      <div
        ref={ref}
        className={twMerge("rounded-2xl p-4 text-slate-100", variantStyles[variant], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";
