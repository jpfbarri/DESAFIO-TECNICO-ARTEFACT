import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "pill-dark" | "amber" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "pill-dark", size = "md", ...props }, ref) => {
    const variantStyles: Record<NonNullable<ButtonProps["variant"]>, string> = {
      "pill-dark":
        "bg-[#1C1917] text-[#FAF8F5] hover:bg-[#292524] active:scale-[0.98] shadow-sm",
      amber:
        "bg-[#D97706] text-white hover:bg-[#B45309] active:scale-[0.98] shadow-sm",
      outline:
        "border border-[#E7E2D8] bg-white text-[#1C1917] hover:bg-[#FAF8F5] hover:border-[#D97706]/50",
      ghost:
        "bg-transparent text-[#57534E] hover:bg-[#E7E2D8]/50 hover:text-[#1C1917]",
    };

    const sizeStyles: Record<NonNullable<ButtonProps["size"]>, string> = {
      sm: "h-8 px-3.5 text-xs",
      md: "h-10 px-5 text-sm",
      lg: "h-11 px-6 text-sm",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-full font-medium transition-all disabled:pointer-events-none disabled:opacity-45",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

