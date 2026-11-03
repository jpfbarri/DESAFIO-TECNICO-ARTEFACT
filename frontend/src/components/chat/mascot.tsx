"use client";

import React, { useState } from "react";

export type MascotVariant =
  | "default"   // teo1: neutro, olhos abertos
  | "happy"     // teo2: feliz, olhinhos fechados sorrindo
  | "idea"      // teo3: eureka, raios sonoros
  | "question"  // teo4: dúvida, ponto de interrogação
  | "music"     // teo5: com fone de ouvido de estúdio
  | "thinking"  // teo6: digitando, três pontinhos (...)
  | "sleep";    // teo7: dormindo, Zzz

const VARIANT_MAP: Record<MascotVariant, string> = {
  default: "/teo1.png",
  happy: "/teo2.png",
  idea: "/teo3.png",
  question: "/teo4.png",
  music: "/teo5.png",
  thinking: "/teo6.png",
  sleep: "/teo7.png",
};

interface MascotProps {
  className?: string;
  size?: "xs" | "sm" | "md" | "lg";
  variant?: MascotVariant;
}

export function Mascot({
  className = "",
  size = "lg",
  variant = "music",
}: MascotProps) {
  const [imageError, setImageError] = useState(false);

  const dimensionClasses = {
    xs: "w-6 h-6",
    sm: "w-8 h-8",
    md: "w-14 h-10",
    lg: "w-32 h-24",
  }[size];

  const src = VARIANT_MAP[variant] || "/teo1.png";

  if (!imageError) {
    return (
      <div
        className={`relative flex items-center justify-center select-none ${dimensionClasses} ${className}`}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt={`Teo Mascote Empório da Música - ${variant}`}
          className="h-full w-full object-contain transition-all duration-300 hover:scale-105"
          onError={() => setImageError(true)}
        />
      </div>
    );
  }

  // Fallback SVG se a imagem não carregar
  return (
    <div
      className={`relative flex items-center justify-center overflow-visible ${dimensionClasses} ${className}`}
    >
      <div className="h-full w-full rounded-2xl bg-gradient-to-br from-[#FB923C] to-[#EA580C] shadow-sm flex items-center justify-center text-white font-bold text-xs">
        Teo
      </div>
    </div>
  );
}
