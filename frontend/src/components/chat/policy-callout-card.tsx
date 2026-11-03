"use client";

import React from "react";
import { BookOpen, ShieldCheck, Clock, CheckCircle2 } from "lucide-react";

export function PolicyCalloutCard({
  title,
  content,
}: {
  title: string;
  content: string;
}) {
  return (
    <div className="my-4 rounded-3xl border border-[#FDE68A] bg-[#FEF3C7]/40 p-1.5 shadow-[0_2px_8px_rgba(217,119,6,0.03)]">
      <div className="rounded-[calc(1.5rem-0.375rem)] bg-white p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.95)]">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#92400E]">
          <BookOpen className="h-4 w-4 text-[#D97706]" strokeWidth={1.5} />
          <span>Manual de Políticas • {title}</span>
        </div>
        <div className="mt-2 text-xs leading-relaxed text-[#57534E]">
          {content}
        </div>
      </div>
    </div>
  );
}

export function EscalationCard({
  protocol,
  customerName,
  reason,
  sla,
}: {
  protocol: string;
  customerName: string;
  reason: string;
  sla: string;
}) {
  return (
    <div className="my-4 rounded-3xl border border-[#A7F3D0] bg-[#ECFDF5]/50 p-1.5 shadow-[0_2px_12px_rgba(16,185,129,0.04)]">
      <div className="rounded-[calc(1.5rem-0.375rem)] bg-white p-4.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.95)]">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#ECFDF5] text-[#059669]">
              <ShieldCheck className="h-4 w-4" strokeWidth={1.5} />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-[#065F46]">
                Atendimento Escalado para Equipe Humana
              </h4>
              <span className="text-[11px] text-[#059669]">
                Prioridade da gerência em Campo Grande/MS
              </span>
            </div>
          </div>
          <span className="rounded-full bg-[#ECFDF5] px-3 py-1 font-mono text-xs font-bold text-[#065F46] border border-[#A7F3D0]">
            {protocol}
          </span>
        </div>

        <div className="mt-3 rounded-2xl border border-[#E7E2D8] bg-[#FAF8F5] p-3 text-xs text-[#57534E]">
          <div className="font-semibold text-[#1C1917]">Motivo:</div>
          <p className="mt-0.5">{reason}</p>
        </div>

        <div className="mt-3 flex flex-wrap gap-4 text-xs text-[#065F46]">
          <div>
            <span className="text-[#059669]/70 font-medium">Cliente:</span>{" "}
            <span className="font-semibold text-[#065F46]">{customerName}</span>
          </div>
          <div>
            <span className="text-[#059669]/70 font-medium">Prazo Oficial:</span>{" "}
            <span className="font-semibold text-[#065F46]">{sla}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
