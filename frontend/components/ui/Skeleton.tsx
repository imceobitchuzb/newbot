import { HTMLAttributes } from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={twMerge(
        "animate-pulse rounded-lg bg-slate-800/70 border border-slate-700/30",
        className
      )}
      {...props}
    />
  );
}
