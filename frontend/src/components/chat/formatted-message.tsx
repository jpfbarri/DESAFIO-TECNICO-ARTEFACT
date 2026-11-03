"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ProductCardGrid, type ParsedProduct } from "./product-card-grid";
import { OrderTrackingCard, type ParsedOrderDetails } from "./order-tracking-card";
import { EscalationCard } from "./policy-callout-card";

const BRL_PRICE_REGEX = /(R\$\s*\d{1,3}(?:[.\s]\d{3})*|\bR\$\s*\d+)([.,]\d{2})\b/g;

export function parseBrlNumber(raw: string): number {
  if (!raw) return 0;
  const clean = raw.trim();
  if (clean.includes(",") && clean.includes(".")) {
    // Formato BR clássico: 11.499,00
    return parseFloat(clean.replace(/\./g, "").replace(",", "."));
  }
  if (clean.includes(",")) {
    // Formato com vírgula: 11499,00
    return parseFloat(clean.replace(",", "."));
  }
  // Formato direto / float string: 11499.00 ou 11499
  const parsed = parseFloat(clean);
  return isNaN(parsed) ? 0 : parsed;
}

export function PriceDisplay({
  amount,
  className = "",
}: {
  amount: number;
  className?: string;
}) {
  const formatted = amount.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return (
    <span className={`inline-baseline font-semibold text-[#111827] ${className}`}>
      R$ {formatted}
    </span>
  );
}

export function renderTextWithGrayCents(text: string): React.ReactNode {
  return text;
}

function processChildrenForCents(children: React.ReactNode): React.ReactNode {
  return children;
}

function tryParseProductList(text: string): { products: ParsedProduct[]; cleanedText: string } {
  const products: ParsedProduct[] = [];
  const lines = text.split("\n");
  const remainingLines: string[] = [];

  // Padrão 1: Catálogo padrão: • [ID 83] Tagima Memphis AC-39 Nylon Natural (Violões) | R$ 429,90 ... | Estoque: 15 un.
  const standardProductRegex = /(?:[•\-*]|\d+\.)?\s*(?:\*\*)?\[ID\s*(\d+)\](?:\*\*)?\s*([^|\(]+)(?:\(([^)]+)\))?\s*\|\s*([^|]+)\|\s*Estoque:\s*(\d+)\s*un\.\s*\|\s*Status:\s*([a-zA-Z_]+)/i;

  // Padrão 2: Promoções ativas: • [Desconto Exclusivo] Ohana CK-20 (ID 121): De R$ 549,00 por R$ 439,20 (20% de desconto) | Estoque: 6 un.
  const promoProductRegex = /(?:[•\-*]|\d+\.)?\s*(?:\*\*)?\[([^\]]+)\](?:\*\*)?\s*([^(\n]+?)\s*\(ID\s*(\d+)\):\s*De\s*(?:\*\*)?R\$\s*([\d\.,]+)(?:\*\*)?\s*por\s*(?:\*\*)?R\$\s*([\d\.,]+)(?:\*\*)?\s*(?:\((?:(\d+)%\s*de desconto)?\))?\s*\|\s*Estoque:\s*(\d+)\s*un\./i;

  for (const line of lines) {
    const matchStandard = line.match(standardProductRegex);
    const matchPromo = line.match(promoProductRegex);

    if (matchStandard) {
      const id = matchStandard[1].trim();
      const name = matchStandard[2].trim();
      const category = (matchStandard[3] || "Instrumento").trim();
      const priceStr = matchStandard[4].trim();
      const stock = parseInt(matchStandard[5].trim(), 10);
      const status = matchStandard[6].trim();

      let originalPrice = 0;
      let finalPrice: number | undefined;
      let pixPrice: number | undefined;
      let discountPercent: number | undefined;

      const promoMatch = priceStr.match(/De R\$\s*([\d\.,]+)\s*por R\$\s*([\d\.,]+)\s*\((\d+)%/i);
      if (promoMatch) {
        originalPrice = parseBrlNumber(promoMatch[1]);
        finalPrice = parseBrlNumber(promoMatch[2]);
        discountPercent = parseInt(promoMatch[3], 10);
      } else {
        const standardMatch = priceStr.match(/R\$\s*([\d\.,]+)(?:\s*\(ou R\$\s*([\d\.,]+))?/i);
        if (standardMatch) {
          originalPrice = parseBrlNumber(standardMatch[1]);
          if (standardMatch[2]) {
            pixPrice = parseBrlNumber(standardMatch[2]);
          }
        }
      }

      products.push({
        id,
        name,
        category,
        originalPrice,
        finalPrice,
        pixPrice,
        discountPercent,
        stock,
        status,
      });
    } else if (matchPromo) {
      const campaign = matchPromo[1].trim();
      const name = matchPromo[2].trim();
      const id = matchPromo[3].trim();
      const origStr = matchPromo[4].trim();
      const finalStr = matchPromo[5].trim();
      const discPercent = matchPromo[6] ? parseInt(matchPromo[6], 10) : undefined;
      const stock = parseInt(matchPromo[7].trim(), 10);

      const originalPrice = parseBrlNumber(origStr);
      const finalPrice = parseBrlNumber(finalStr);

      products.push({
        id,
        name,
        category: "Instrumento",
        originalPrice,
        finalPrice,
        discountPercent: discPercent,
        promoName: campaign,
        stock,
        status: "active",
      });
    } else {
      // Filtrar linhas de introdução técnica antes das listas de produtos/promoções
      if (/^\s*Encontrados\s+\d+\s+instrumento\(s\):?\s*$/i.test(line)) continue;
      if (/^\s*Promoções\s+ATIVAS\s+no\s+sistema\s*\(\d+\s*encontradas\):?\s*$/i.test(line)) continue;
      remainingLines.push(line);
    }
  }

  return {
    products,
    cleanedText: remainingLines.join("\n").trim(),
  };
}

function tryParseOrderDetails(text: string): ParsedOrderDetails | null {
  if (!text.includes("=== Detalhes do Pedido #")) return null;

  try {
    const orderIdMatch = text.match(/=== Detalhes do Pedido #(\d+) ===/);
    const customerMatch = text.match(/Cliente Titular:\s*([^(\n]+)(?:\(([^|\n]+)\|\s*([^)]+)\))?/);
    const dateMatch = text.match(/Data do Pedido:\s*([^\n]+)/);
    const statusMatch = text.match(/Status Atual:\s*([^\n]+)/);
    const totalMatch = text.match(/Valor Total:\s*R\$\s*([\d\.,]+)\s*\|\s*Forma de Pagamento:\s*([^\n]+)/);
    const trackingMatch = text.match(/Código de Rastreamento:\s*([A-Z0-9]+)/);
    const estDeliveryMatch = text.match(/Entrega Estimada\/Realizada:\s*([^\n]+)/);
    const notesMatch = text.match(/Observações \/ Motivo:\s*([^\n]+)/);

    const items: Array<{ quantity: number; name: string; category: string; price: number }> = [];
    const itemLines = text.match(/-\s*(\d+)x\s*([^(]+)\(ID\s*\d+\s*\|\s*([^)]+)\)\s*—\s*R\$\s*([\d\.,]+)/g);
    if (itemLines) {
      for (const il of itemLines) {
        const im = il.match(/-\s*(\d+)x\s*([^(]+)\(ID\s*\d+\s*\|\s*([^)]+)\)\s*—\s*R\$\s*([\d\.,]+)/);
        if (im) {
          items.push({
            quantity: parseInt(im[1], 10),
            name: im[2].trim(),
            category: im[3].trim(),
            price: parseBrlNumber(im[4]),
          });
        }
      }
    }

    if (orderIdMatch && statusMatch) {
      return {
        orderId: parseInt(orderIdMatch[1], 10),
        customerName: customerMatch ? customerMatch[1].trim() : "Cliente",
        customerEmail: customerMatch && customerMatch[2] ? customerMatch[2].trim() : "",
        customerCity: customerMatch && customerMatch[3] ? customerMatch[3].trim() : "",
        orderDate: dateMatch ? dateMatch[1].trim() : "",
        status: statusMatch[1].trim(),
        totalBrl: totalMatch ? parseBrlNumber(totalMatch[1]) : 0,
        paymentMethod: totalMatch ? totalMatch[2].trim() : "",
        trackingCode: trackingMatch && !trackingMatch[1].includes("Ainda") ? trackingMatch[1].trim() : undefined,
        estimatedDelivery: estDeliveryMatch ? estDeliveryMatch[1].trim() : undefined,
        notes: notesMatch ? notesMatch[1].trim() : undefined,
        items,
      };
    }
  } catch {
    return null;
  }
  return null;
}

export function FormattedMessage({
  content,
  onSelectPrompt,
}: {
  content: string;
  onSelectPrompt?: (prompt: string) => void;
}) {
  // Escalation Card
  const escalationMatch = content.match(
    /Protocolo de Atendimento:\s*([A-Z0-9\-]+)[\s\S]*?Cliente:\s*([^\n]+)[\s\S]*?Motivo registrado:\s*([^\n]+)[\s\S]*?Prazo oficial de retorno:\s*([^\n]+)/i
  );

  // Order Details Card
  const parsedOrder = tryParseOrderDetails(content);

  // Product Listings & Promotions
  const { products: parsedProducts, cleanedText } = tryParseProductList(content);

  let markdownContent = cleanedText;

  if (parsedOrder) {
    markdownContent = markdownContent.replace(
      /=== Detalhes do Pedido #[\s\S]*?Valor Total: R\$[\s\S]*?(?=\n\n|$)/,
      ""
    );
  }

  if (escalationMatch) {
    markdownContent = markdownContent.replace(
      /Atendimento escalado com sucesso[\s\S]*?Prazo oficial de retorno: até 24 horas úteis\./,
      ""
    );
  }

  return (
    <div className="space-y-4 text-sm leading-relaxed text-[#111827]">
      {/* Escalation Card */}
      {escalationMatch && (
        <EscalationCard
          protocol={escalationMatch[1].trim()}
          customerName={escalationMatch[2].trim()}
          reason={escalationMatch[3].trim()}
          sla={escalationMatch[4].trim()}
        />
      )}

      {/* Order Tracking Card */}
      {parsedOrder && <OrderTrackingCard order={parsedOrder} />}

      {/* Product Cards Grid */}
      {parsedProducts.length > 0 && (
        <ProductCardGrid
          products={parsedProducts}
          onSelectProduct={(name) =>
            onSelectPrompt &&
            onSelectPrompt(`Quanto custa o ${name} e quais as condições de pagamento e parcelamento?`)
          }
        />
      )}

      {/* Clean Markdown Content with Gray Cents */}
      {markdownContent.trim().length > 0 && (
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => (
              <p className="mb-2.5 last:mb-0 leading-relaxed text-[#1F2937]">
                {processChildrenForCents(children)}
              </p>
            ),
            table: ({ children }) => (
              <div className="my-3 overflow-x-auto rounded-xl border border-slate-200/80 bg-white shadow-xs">
                <table className="w-full text-left text-xs border-collapse">{children}</table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="bg-slate-50 font-semibold text-slate-700 border-b border-slate-200/80">
                {children}
              </thead>
            ),
            tbody: ({ children }) => (
              <tbody className="divide-y divide-slate-100">{children}</tbody>
            ),
            tr: ({ children }) => (
              <tr className="hover:bg-amber-50/30 transition-colors">{children}</tr>
            ),
            th: ({ children }) => (
              <th className="px-3 py-2 font-semibold text-slate-800">{children}</th>
            ),
            td: ({ children }) => (
              <td className="px-3 py-2 text-slate-600 leading-normal">
                {processChildrenForCents(children)}
              </td>
            ),
            ul: ({ children }) => (
              <ul className="mb-3 space-y-1.5 pl-1">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="mb-3 space-y-1.5 pl-4 list-decimal marker:font-semibold marker:text-[#EA580C]">
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li className="ml-4 list-disc marker:text-[#EA580C] text-[#374151]">
                {processChildrenForCents(children)}
              </li>
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-[#111827]">
                {processChildrenForCents(children)}
              </strong>
            ),
            code: ({ children }) => (
              <code className="rounded-md border border-[#E5E7EB] bg-[#F9FAFB] px-1.5 py-0.5 font-mono text-xs text-[#EA580C]">
                {children}
              </code>
            ),
            h3: ({ children }) => (
              <h3 className="mb-2 mt-4 text-sm font-semibold tracking-tight text-[#111827]">
                {children}
              </h3>
            ),
            h4: ({ children }) => (
              <h4 className="mb-1.5 mt-3 text-xs font-semibold uppercase tracking-wider text-[#6B7280]">
                {children}
              </h4>
            ),
          }}
        >
          {markdownContent}
        </ReactMarkdown>
      )}
    </div>
  );
}
