"use client";

import React, { useState } from "react";
import {
  PackageCheck,
  Truck,
  CheckCircle2,
  Clock,
  XCircle,
  Copy,
  Check,
  Calendar,
  CreditCard,
  User,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { PriceDisplay } from "./formatted-message";

export interface ParsedOrderDetails {
  orderId: number;
  customerName: string;
  customerEmail: string;
  customerCity: string;
  orderDate: string;
  status: "pending" | "confirmed" | "shipped" | "delivered" | "cancelled" | string;
  totalBrl: number;
  paymentMethod: string;
  trackingCode?: string;
  estimatedDelivery?: string;
  notes?: string;
  items: Array<{
    quantity: number;
    name: string;
    category: string;
    price: number;
  }>;
}

const STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  delivered: {
    label: "Entregue ao Destinatário",
    bg: "bg-[#ECFDF5]",
    text: "text-[#065F46]",
    border: "border-[#A7F3D0]",
    icon: CheckCircle2,
  },
  shipped: {
    label: "Em Transporte (Despachado)",
    bg: "bg-[#EFF6FF]",
    text: "text-[#1E40AF]",
    border: "border-[#BFDBFE]",
    icon: Truck,
  },
  confirmed: {
    label: "Pagamento Confirmado",
    bg: "bg-[#FEF3C7]",
    text: "text-[#92400E]",
    border: "border-[#FDE68A]",
    icon: Clock,
  },
  pending: {
    label: "Aguardando Pagamento",
    bg: "bg-[#FFFBEB]",
    text: "text-[#B45309]",
    border: "border-[#FDE68A]",
    icon: Clock,
  },
  cancelled: {
    label: "Pedido Cancelado",
    bg: "bg-[#FEF2F2]",
    text: "text-[#991B1B]",
    border: "border-[#FECACA]",
    icon: XCircle,
  },
};

export function OrderTrackingCard({ order }: { order: ParsedOrderDetails }) {
  const [copied, setCopied] = useState(false);
  const statusMeta = STATUS_CONFIG[order.status.toLowerCase()] || {
    label: order.status.toUpperCase(),
    bg: "bg-[#F3EFE6]",
    text: "text-[#57534E]",
    border: "border-[#E7E2D8]",
    icon: Clock,
  };
  const StatusIcon = statusMeta.icon;

  const copyTracking = () => {
    if (order.trackingCode) {
      navigator.clipboard.writeText(order.trackingCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    /* Outer Shell: Double-Bezel Hardware Enclosure */
    <div className="my-5 rounded-3xl border border-[#E7E2D8] bg-[#FAF8F5]/80 p-1.5 shadow-[0_2px_12px_rgba(28,25,23,0.03)]">
      {/* Inner Core */}
      <div className="overflow-hidden rounded-[calc(1.5rem-0.375rem)] bg-white shadow-[inset_0_1px_0_rgba(255,255,255,0.95)]">
        {/* Header Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#F3EFE6] bg-[#FAF8F5]/50 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-[#1C1917] text-[#D97706] shadow-sm ring-1 ring-black/5">
              <PackageCheck className="h-4 w-4" strokeWidth={1.5} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold tracking-tight text-[#1C1917]">
                  Pedido #{order.orderId}
                </h4>
                <span className="rounded-full bg-[#FAF8F5] px-2 py-0.2 text-[10px] font-medium text-[#78716C] border border-[#E7E2D8]">
                  Oficial
                </span>
              </div>
              <span className="text-[11px] text-[#78716C]">
                {order.customerName} {order.customerCity ? `• ${order.customerCity}` : ""}
              </span>
            </div>
          </div>

          {/* Status Badge */}
          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${statusMeta.bg} ${statusMeta.text} ${statusMeta.border}`}
          >
            <StatusIcon className="h-3.5 w-3.5" />
            <span>{statusMeta.label}</span>
          </span>
        </div>

        {/* Content Body */}
        <div className="p-5">
          {/* Tracking Code Island if available */}
          {order.trackingCode && (
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#E7E2D8] bg-[#FAF8F5] p-4">
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[#78716C]">
                  Código de Rastreamento (Correios / Transportadora)
                </span>
                <div className="mt-1 flex items-center gap-3">
                  <span className="font-mono text-sm font-bold tracking-wider text-[#1C1917]">
                    {order.trackingCode}
                  </span>
                  <button
                    type="button"
                    onClick={copyTracking}
                    className="inline-flex items-center gap-1.5 rounded-full border border-[#E7E2D8] bg-white px-2.5 py-0.5 text-[11px] font-medium text-[#57534E] shadow-sm transition-all hover:bg-[#FAF8F5] hover:text-[#1C1917]"
                    title="Copiar código de rastreamento"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3 w-3 text-[#059669]" />
                        <span className="text-[#059669] font-semibold">Copiado</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" />
                        <span>Copiar</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {order.estimatedDelivery && (
                <div className="text-right">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[#78716C]">
                    Previsão de Entrega
                  </span>
                  <p className="mt-0.5 text-xs font-semibold text-[#1C1917]">
                    {order.estimatedDelivery}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Notes / Justification if present */}
          {order.notes && (
            <div className="mb-4 rounded-xl border border-[#FECACA] bg-[#FEF2F2] p-3 text-xs text-[#991B1B]">
              <span className="font-semibold">Observação do Atendimento:</span> {order.notes}
            </div>
          )}

          {/* Items Breakdown */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#78716C]">
              Itens Confirmados ({order.items.length})
            </span>
            <div className="divide-y divide-[#F3EFE6] rounded-2xl border border-[#E7E2D8]">
              {order.items.map((it, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3.5 text-xs"
                >
                  <div>
                    <span className="font-semibold text-[#1C1917]">
                      {it.quantity}x {it.name}
                    </span>
                    <span className="ml-2 font-normal text-[#A8A29E]">
                      ({it.category})
                    </span>
                  </div>
                  <PriceDisplay amount={it.price * it.quantity} className="text-xs" />
                </div>
              ))}
            </div>
          </div>

          {/* Meta Footer */}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#F3EFE6] pt-3.5 text-xs text-[#78716C]">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-[#A8A29E]" />
                {order.orderDate}
              </span>
              <span className="flex items-center gap-1.5">
                <CreditCard className="h-3.5 w-3.5 text-[#A8A29E]" />
                {order.paymentMethod.toUpperCase()}
              </span>
            </div>

            <div className="flex items-center gap-2 font-medium">
              <span className="text-[#78716C]">Total Pago:</span>
              <PriceDisplay amount={order.totalBrl} className="text-sm font-bold text-[#1C1917]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
