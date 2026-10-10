import React from "react";
import { ShieldCheck } from "lucide-react";

interface VerificationBadgeProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export default function VerificationBadge({
  className = "",
  size = "md",
}: VerificationBadgeProps) {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-[10px] gap-1",
    md: "px-2.5 py-1 text-xs gap-1.5",
    lg: "px-3 py-1.5 text-sm gap-2",
  };

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5",
    lg: "w-4 h-4",
  };

  return (
    <span
      className={`inline-flex items-center font-bold tracking-tight rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 backdrop-blur-sm select-none ${sizeClasses[size]} ${className}`}
      title="Verified Designer — Authenticated brand on AI Fashion Marketplace"
    >
      <ShieldCheck className={`${iconSizes[size]} text-emerald-400 shrink-0`} />
      <span>Maison Certifiée</span>
    </span>
  );
}
