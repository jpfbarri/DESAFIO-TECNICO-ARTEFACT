"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface OnboardingSplashProps {
  onComplete: () => void;
}

const ONBOARDING_STEPS = [
  {
    image: "/teo5.png",
    alt: "Téo com fones de estúdio",
    title: "Encontre o instrumento ideal",
    description:
      "Recomendações personalizadas para o seu estilo musical, nível técnico e orçamento.",
    buttonText: "Continuar",
  },
  {
    image: "/teo3.png",
    alt: "Téo com ideia e ofertas",
    title: "Preços e estoque em tempo real",
    description:
      "Consulte disponibilidade imediata, simule valores à vista e confira promoções ativas.",
    buttonText: "Continuar",
  },
  {
    image: "/teo2.png",
    alt: "Téo sorrindo feliz",
    title: "Suporte do início ao fim",
    description:
      "Rastreamento ágil de pedidos, dúvidas sobre garantia e atendimento humano integrado.",
    buttonText: "Começar",
  },
];

export function OnboardingSplash({ onComplete }: OnboardingSplashProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      onComplete();
    }
  };

  const step = ONBOARDING_STEPS[currentStep];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.35, ease: "easeInOut" }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white px-6 py-8 font-sans select-none overflow-hidden"
    >
      {/* Center Carousel Content - Truly Centered Vertically & Horizontally */}
      <div className="relative z-10 w-full max-w-2xl flex flex-col items-center text-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -14 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="flex flex-col items-center text-center w-full"
          >
            {/* 3D Mascot with gentle float, crisp, zero aura, zero shadow */}
            <motion.div
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
              className="relative h-64 w-64 sm:h-80 sm:w-80 md:h-96 md:w-96 lg:h-[380px] lg:w-[380px] flex items-center justify-center mb-6 sm:mb-8"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={step.image}
                alt={step.alt}
                className="h-full w-full object-contain pointer-events-none"
              />
            </motion.div>

            {/* Pagination Dots */}
            <div className="flex items-center gap-2 mb-6">
              {ONBOARDING_STEPS.map((_, idx) => {
                const isActive = idx === currentStep;
                return (
                  <motion.span
                    key={idx}
                    layout
                    transition={{ duration: 0.25 }}
                    className={`h-2 rounded-full transition-all duration-300 ${
                      isActive
                        ? "w-8 bg-[#EA580C]"
                        : "w-2 bg-slate-200"
                    }`}
                  />
                );
              })}
            </div>

            {/* Title (Calibrated Poppins Semibold) */}
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight text-slate-900 leading-tight">
              {step.title}
            </h2>

            {/* Description (Poppins Regular, 1 concise sentence) */}
            <p className="mt-3 text-sm sm:text-base text-slate-500 leading-relaxed max-w-md mx-auto">
              {step.description}
            </p>

            {/* Action Pill Button */}
            <div className="w-full max-w-xs sm:max-w-sm mt-8 sm:mt-10">
              <button
                type="button"
                onClick={handleNext}
                className="w-full h-13 sm:h-14 py-3.5 rounded-full bg-gradient-to-r from-[#FB923C] to-[#EA580C] hover:from-[#EA580C] hover:to-[#C2410C] text-white font-medium text-base tracking-wide shadow-[0_8px_25px_rgba(234,88,12,0.22)] hover:shadow-[0_12px_30px_rgba(234,88,12,0.3)] active:scale-[0.98] transition-all flex items-center justify-center cursor-pointer"
              >
                {step.buttonText}
              </button>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

export default OnboardingSplash;
