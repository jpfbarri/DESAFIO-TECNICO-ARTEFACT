"use client";

import React, { useState } from "react";
import {
  Search,
  Tag,
  Sparkles,
  PackageCheck,
  BookOpen,
  UserCheck,
  CheckCircle2,
  Loader2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export interface ToolChipData {
  tool: string;
  args?: Record<string, unknown>;
  status: "running" | "done";
  outputPreview?: string;
}

const TOOL_HUMAN_LABELS: Record<string, { running: string; done: string; icon: React.ComponentType<{ className?: string; strokeWidth?: number }> }> = {
  search_products: {
    running: "Buscando instrumentos no catálogo...",
    done: "Catálogo de instrumentos consultado",
    icon: Search,
  },
  get_product_price: {
    running: "Verificando preço, PIX e estoque...",
    done: "Preço e estoque confirmados",
    icon: Tag,
  },
  get_active_promotions: {
    running: "Verificando promoções vigentes...",
    done: "Promoções ativas verificadas",
    icon: Sparkles,
  },
  get_order_status: {
    running: "Localizando pedido e rastreio (LGPD)...",
    done: "Status do pedido verificado",
    icon: PackageCheck,
  },
  search_policies: {
    running: "Consultando políticas oficiais da loja...",
    done: "Manual de políticas consultado",
    icon: BookOpen,
  },
  escalate_to_human: {
    running: "Gerando protocolo de atendimento...",
    done: "Atendimento encaminhado para especialista",
    icon: UserCheck,
  },
};

export function ToolChip({ item }: { item: ToolChipData }) {
  const [expanded, setExpanded] = useState(false);
  const meta = TOOL_HUMAN_LABELS[item.tool] || {
    running: `Executando ${item.tool}...`,
    done: `${item.tool} concluído`,
    icon: Search,
  };
  const IconComponent = meta.icon;

  return (
    <div className="inline-flex flex-col">
      <button
        type="button"
        onClick={() => item.outputPreview && setExpanded((prev) => !prev)}
        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium transition-all duration-200 ${
          item.status === "running"
            ? "border-[#FDE68A] bg-[#FEF3C7]/90 text-[#92400E] shadow-sm animate-pulse"
            : "border-[#E7E2D8] bg-[#FAF8F5] text-[#57534E] hover:border-[#D97706]/40 hover:bg-[#FEF3C7]/30 hover:text-[#1C1917]"
        }`}
      >
        {item.status === "running" ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin text-[#D97706]" strokeWidth={1.5} />
        ) : (
          <CheckCircle2 className="h-3.5 w-3.5 text-[#059669]" strokeWidth={1.5} />
        )}
        <span>{item.status === "running" ? meta.running : meta.done}</span>

        {item.outputPreview &&
          (expanded ? (
            <ChevronUp className="h-3 w-3 text-[#A8A29E]" strokeWidth={1.5} />
          ) : (
            <ChevronDown className="h-3 w-3 text-[#A8A29E]" strokeWidth={1.5} />
          ))}
      </button>

      {expanded && item.outputPreview && (
        <div className="mt-1.5 max-w-xl overflow-hidden rounded-xl border border-[#E7E2D8] bg-white p-3 shadow-sm">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-[#A8A29E]">
            Dados do Sistema ({item.tool})
          </div>
          <pre className="mt-1 max-h-48 overflow-y-auto whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-[#57534E]">
            {item.outputPreview}
          </pre>
        </div>
      )}
    </div>
  );
}
