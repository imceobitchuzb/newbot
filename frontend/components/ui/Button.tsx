import { ButtonHTMLAttributes, forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { twMerge } from "tailwind-merge";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "amber";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-all rounded-xl active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500";

    const variantStyles = {
      primary:
        "bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-md shadow-blue-600/20",
      secondary:
        "bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700/80",
      outline:
        "border border-slate-700 hover:border-slate-600 bg-transparent text-slate-200 hover:bg-slate-800/40",
      ghost: "bg-transparent hover:bg-slate-800/60 text-slate-300 hover:text-white",
      amber:
        "bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300",
    };

    const sizeStyles = {
      sm: "text-xs py-2 px-3 gap-1.5 min-h-[36px]",
      md: "text-sm py-2.5 px-4 gap-2 min-h-[44px]",
      lg: "text-base py-3.5 px-5 gap-2.5 min-h-[50px]",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={twMerge(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="w-4 h-4 animate-spin text-current" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
