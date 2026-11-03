import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "amber" | "neutral" | "success" | "danger";
}

export function Badge({
  className,
  variant = "neutral",
  ...props
}: BadgeProps) {
  const variantStyles: Record<NonNullable<BadgeProps["variant"]>, string> = {
    amber: "bg-[#FEF3C7] text-[#92400E] border-[#FDE68A]",
    neutral: "bg-[#F3EFE6] text-[#57534E] border-[#E7E2D8]",
    success: "bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]",
    danger: "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
}

