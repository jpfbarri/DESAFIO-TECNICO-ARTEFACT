"use client";

import React from "react";
import { Sparkles, ArrowUpRight, Tag, Zap } from "lucide-react";
import { PriceDisplay } from "./formatted-message";

export interface ParsedProduct {
  id: string;
  name: string;
  category: string;
  originalPrice: number;
  finalPrice?: number;
  pixPrice?: number;
  discountPercent?: number;
  promoName?: string;
  stock: number;
  status: string;
}

export function ProductCardGrid({
  products,
  onSelectProduct,
}: {
  products: ParsedProduct[];
  onSelectProduct?: (productName: string) => void;
}) {
  if (!products || products.length === 0) return null;

  return (
    <div className="my-5 grid grid-cols-1 gap-3.5 sm:grid-cols-2">
      {products.map((item) => {
        const hasPromo = Boolean(item.finalPrice && item.discountPercent);
        const displayPrice = item.finalPrice || item.originalPrice;

        return (
          <div
            key={item.id}
            className="group relative flex flex-col justify-between rounded-2xl border border-[#E5E7EB] bg-white p-4.5 shadow-[0_1px_3px_rgba(0,0,0,0.02)] transition-all duration-300 hover:-translate-y-0.5 hover:border-[#F97316]/50 hover:shadow-[0_8px_20px_rgba(249,115,22,0.06)]"
          >
            {/* Header: Category & Stock */}
            <div className="flex items-center justify-between gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-[#F3F4F6] px-2.5 py-0.5 text-[11px] font-medium text-[#4B5563]">
                <Tag className="h-3 w-3 text-[#EA580C]" strokeWidth={1.75} />
                {item.category || "Instrumento"}
              </span>

              {item.stock > 0 ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#ECFDF5] px-2.5 py-0.5 text-[10px] font-semibold text-[#065F46] border border-[#A7F3D0]/60">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#10B981] animate-pulse" />
                  {item.stock} em estoque
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#FEF2F2] px-2.5 py-0.5 text-[10px] font-semibold text-[#991B1B] border border-[#FECACA]/60">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#EF4444]" />
                  Esgotado
                </span>
              )}
            </div>

            {/* Title & Code */}
            <div className="mt-3">
              <h4 className="text-sm font-semibold tracking-tight text-[#111827] transition-colors group-hover:text-[#EA580C]">
                {item.name}
              </h4>
              <span className="mt-0.5 block text-[10px] font-mono text-[#9CA3AF]">
                Cód. #{item.id}
              </span>
            </div>

            {/* Price Block */}
            <div className="mt-3.5 border-t border-[#F3F4F6] pt-3">
              {hasPromo ? (
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[#9CA3AF] line-through">
                      R$ {item.originalPrice.toFixed(2).replace(".", ",")}
                    </span>
                    <span className="inline-flex items-center gap-0.5 rounded-full bg-[#FEF3C7] px-2 py-0.5 text-[10px] font-bold text-[#92400E]">
                      <Sparkles className="h-2.5 w-2.5 text-[#D97706]" strokeWidth={2} />
                      -{item.discountPercent}% OFF
                    </span>
                  </div>
                  <div className="mt-1">
                    <PriceDisplay amount={displayPrice} className="text-base font-bold text-[#111827]" />
                  </div>
                </div>
              ) : (
                <div>
                  <PriceDisplay amount={displayPrice} className="text-base font-bold text-[#111827]" />
                  {item.pixPrice && (
                    <div className="mt-1 flex items-center gap-1.5 text-xs text-[#059669]">
                      <Zap className="h-3 w-3 text-[#10B981]" strokeWidth={2} />
                      <span className="font-semibold">
                        R$ {item.pixPrice.toFixed(2).replace(".", ",")}
                      </span>
                      <span className="rounded bg-[#ECFDF5] px-1 py-0.2 text-[10px] font-medium text-[#065F46]">
                        no PIX (5% OFF)
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action Button */}
            {onSelectProduct && (
              <button
                type="button"
                onClick={() => onSelectProduct(item.name)}
                className="mt-4 flex w-full items-center justify-between rounded-xl border border-[#E5E7EB] bg-[#FAFAFA] py-2 px-3 text-xs font-semibold text-[#374151] transition-all hover:border-[#F97316] hover:bg-[#FFF7ED] hover:text-[#EA580C] active:scale-[0.99]"
              >
                <span>Consultar detalhes</span>
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-white shadow-sm text-[#6B7280] transition-colors group-hover:text-[#EA580C]">
                  <ArrowUpRight className="h-3 w-3" strokeWidth={2} />
                </div>
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
