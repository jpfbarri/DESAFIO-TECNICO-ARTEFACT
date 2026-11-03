"use client";

import React from "react";
import {
  Plus,
  Sparkles,
  MapPin,
  Clock,
  Phone,
  ArrowUpRight,
  MessageCircle,
  Disc3,
  ShieldCheck,
} from "lucide-react";
import { PriceDisplay } from "@/components/chat/formatted-message";

export interface ActivePromoItem {
  product_id: number;
  name: string;
  price_brl: number;
  discount_percent: number;
  campaign: string;
}

interface SidebarProps {
  threadId: string;
  promotions: ActivePromoItem[];
  onNewConversation: () => void;
  onSelectPrompt: (prompt: string) => void;
}

export function Sidebar({
  threadId,
  promotions,
  onNewConversation,
  onSelectPrompt,
}: SidebarProps) {
  return (
    <aside className="flex h-full w-[310px] shrink-0 flex-col justify-between border-r border-[#E7E2D8] bg-[#F7F4EE] p-5">
      <div className="flex flex-col gap-5 overflow-y-auto pr-1">
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-1 pt-1">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[#1C1917] text-white shadow-sm ring-1 ring-black/5">
            <Disc3 className="h-5 w-5 text-[#D97706]" strokeWidth={1.75} />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-[#1C1917]">
              Empório da Música
            </h1>
            <p className="text-[11px] text-[#57534E]">
              Instrumentos Musicais • Desde 2008
            </p>
          </div>
        </div>

        {/* CTA: Nova Conversa (Nested Island Button Architecture) */}
        <button
          type="button"
          onClick={onNewConversation}
          className="group relative flex w-full items-center justify-between rounded-full bg-[#1C1917] py-2 pl-4 pr-2 text-xs font-semibold text-[#FAF8F5] shadow-sm transition-all duration-300 hover:bg-[#292524] active:scale-[0.98]"
        >
          <span>Nova Conversa</span>
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white/10 text-white transition-all duration-300 group-hover:bg-[#D97706] group-hover:scale-105">
            <Plus className="h-4 w-4" strokeWidth={2} />
          </div>
        </button>

        {/* Active Promotions Showcase */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-[#57534E]">
              <Sparkles className="h-3 w-3 text-[#D97706]" strokeWidth={1.5} />
              <span>Ofertas da Semana</span>
            </div>
            <span className="rounded-full bg-[#FAF8F5] px-2 py-0.5 text-[10px] font-medium text-[#57534E] border border-[#E7E2D8]">
              {promotions.length} ativas
            </span>
          </div>

          <div className="flex flex-col gap-2">
            {promotions.map((promo) => {
              const discounted =
                promo.price_brl * (1 - promo.discount_percent / 100);
              return (
                <button
                  key={promo.product_id}
                  type="button"
                  onClick={() =>
                    onSelectPrompt(
                      `Quanto custa o ${promo.name} e quais as condições de pagamento e parcelamento?`
                    )
                  }
                  className="group relative flex flex-col justify-between rounded-xl border border-[#E7E2D8] bg-white p-3 text-left shadow-[0_1px_4px_rgba(28,25,23,0.02)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D97706]/60 hover:shadow-sm"
                >
                  <div className="flex items-start justify-between gap-1.5">
                    <span className="line-clamp-1 text-xs font-medium text-[#1C1917] transition-colors group-hover:text-[#D97706]">
                      {promo.name}
                    </span>
                    <span className="shrink-0 rounded-full bg-[#FEF3C7] px-1.5 py-0.5 text-[10px] font-bold text-[#92400E]">
                      -{promo.discount_percent}%
                    </span>
                  </div>

                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="text-[11px] text-[#A8A29E] line-through">
                      R$ {promo.price_brl.toFixed(0)}
                    </span>
                    <PriceDisplay amount={discounted} className="text-xs" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Store Location & Hours (Double-Bezel Hardware aesthetic) */}
      <div className="mt-4 rounded-2xl border border-[#E7E2D8] bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-2.5 text-xs text-[#57534E]">
          <div className="flex items-center justify-between border-b border-[#F3EFE6] pb-2">
            <span className="text-[11px] font-semibold text-[#1C1917]">
              Loja Física Campo Grande
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-[#ECFDF5] px-2 py-0.5 text-[10px] font-medium text-[#065F46]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#10B981] animate-pulse" />
              Aberto hoje
            </span>
          </div>

          <div className="flex items-start gap-2">
            <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#D97706]" strokeWidth={1.5} />
            <span className="leading-tight">Rua 14 de Maio, 3200 — Centro</span>
          </div>

          <div className="flex items-center gap-2">
            <Clock className="h-3.5 w-3.5 shrink-0 text-[#D97706]" strokeWidth={1.5} />
            <span>Seg–Sex 09h–18h • Sáb 09h–13h</span>
          </div>

          <a
            href="https://wa.me/556733214500"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 inline-flex w-full items-center justify-center gap-1.5 rounded-xl border border-[#E7E2D8] bg-[#FAF8F5] py-2 text-xs font-semibold text-[#1C1917] transition-all hover:bg-[#FEF3C7]/40 hover:border-[#D97706]/40 hover:text-[#92400E]"
          >
            <Phone className="h-3 w-3 text-[#D97706]" strokeWidth={1.5} />
            <span>WhatsApp: (67) 3321-4500</span>
          </a>
        </div>
      </div>
    </aside>
  );
}
