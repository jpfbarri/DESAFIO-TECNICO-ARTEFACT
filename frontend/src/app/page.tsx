"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Info,
  RotateCcw,
  MapPin,
  Clock,
  Phone,
  X,
  AlertCircle,
  RefreshCw,
  Copy,
  Check,
} from "lucide-react";
import { Mascot } from "@/components/chat/mascot";
import { ToolChip, type ToolChipData } from "@/components/chat/tool-chip";
import { FormattedMessage } from "@/components/chat/formatted-message";
import { motion, AnimatePresence } from "framer-motion";
import ThoughtLine from "@/components/chat/thought-line";
import OnboardingSplash from "@/components/chat/onboarding-splash";

const LOCAL_STORAGE_THREAD_KEY = "emporio_musica_thread_id";
const LOCAL_STORAGE_ONBOARDING_KEY = "emporio_musica_onboarding_completed";

interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  tools: ToolChipData[];
}

interface ActivePromoItem {
  product_id: number;
  name: string;
  price_brl: number;
  discount_percent: number;
  campaign: string;
}

const QUICK_ACTIONS = [
  {
    title: "Encontrar instrumento",
    subtitle: "Violões até R$ 1.000",
    prompt: "Quais opções de violões disponíveis vocês têm custando até R$ 1000?",
    iconSrc: "/icons/instrument.png",
  },
  {
    title: "Consultar preços",
    subtitle: "Takamine GD20 e condições",
    prompt: "Quanto custa o Takamine GD20? Vi que tinha uma promoção de 12%.",
    iconSrc: "/icons/price.png",
  },
  {
    title: "Acompanhar pedido",
    subtitle: "Rastreio com validação LGPD",
    prompt: "Qual o status do meu pedido #1? Meu e-mail é pedro.oliveira@jmail.com",
    iconSrc: "/icons/order.png",
  },
  {
    title: "Trocas e devoluções",
    subtitle: "Direito de arrependimento e frete",
    prompt: "Me arrependi da minha compra pela internet, posso devolver? Quem paga o frete?",
    iconSrc: "/icons/return.png",
  },
];

function createThreadId(): string {
  const randomSuffix = Math.random().toString(36).substring(2, 10);
  return `emp-${randomSuffix}`;
}

function useSmoothTypewriter(rawText: string, isLatestStreaming: boolean) {
  const [displayed, setDisplayed] = useState(rawText);
  const targetRef = useRef(rawText);
  targetRef.current = rawText;

  useEffect(() => {
    if (!isLatestStreaming && displayed.length >= rawText.length) {
      setDisplayed(rawText);
      return;
    }

    const timer = setInterval(() => {
      setDisplayed((prev) => {
        if (prev.length >= targetRef.current.length) {
          clearInterval(timer);
          return targetRef.current;
        }
        const delta = targetRef.current.length - prev.length;
        // Ritmo natural e fluido de digitação: 1 a 2 caracteres por tick (22ms)
        const step = delta > 120 ? 6 : delta > 50 ? 3 : delta > 18 ? 2 : 1;
        return targetRef.current.slice(0, prev.length + step);
      });
    }, 22);

    return () => clearInterval(timer);
  }, [isLatestStreaming, rawText]);

  const isTyping = isLatestStreaming || displayed.length < rawText.length;
  return { displayed: isTyping ? displayed : rawText, isTyping };
}

function getToolStepLabel(tool: string): string {
  switch (tool) {
    case "search_products":
      return "Consultando instrumentos no catálogo...";
    case "get_product_price":
      return "Verificando preços e condições no PIX...";
    case "get_active_promotions":
      return "Consultando campanhas e promoções ativas...";
    case "get_order_status":
      return "Verificando status e rastreamento do pedido...";
    case "search_policies":
      return "Consultando manual de políticas e prazos...";
    case "escalate_to_human":
      return "Acionando protocolo de atendimento humano...";
    default:
      return "Processando dados do sistema...";
  }
}

function AssistantCardContent({
  content,
  isLatestStreaming,
  tools = [],
  onSelectPrompt,
}: {
  content: string;
  isLatestStreaming: boolean;
  tools?: ToolChipData[];
  onSelectPrompt?: (prompt: string) => void;
}) {
  const { displayed, isTyping } = useSmoothTypewriter(content, isLatestStreaming);
  const isWorking = isLatestStreaming && !displayed;

  const traceSteps =
    tools && tools.length > 0
      ? tools.map((t) => getToolStepLabel(t.tool))
      : ["Consultando o sistema da Empório da Música..."];

  return (
    <div className="flex flex-col gap-3">
      {/* ThoughtLine Thinking & Settle Accordion */}
      {(isWorking || (tools && tools.length > 0)) && (
        <div className="border-b border-slate-100/90 pb-2.5 mb-1">
          <ThoughtLine
            working={isWorking}
            steps={traceSteps}
            label="Téo está pensando…"
            doneLabel="Pensou por"
            glyph="sparkle"
            color="#EA580C"
            fontSize={13}
            settleDuration={300}
            collapsible
            collapseOnSettle
            showTimer
          />
        </div>
      )}

      {/* Answer content */}
      {displayed ? (
        <div className="relative">
          <FormattedMessage
            content={displayed}
            onSelectPrompt={onSelectPrompt}
          />
          {isTyping && (
            <span className="inline-block h-3.5 w-1.5 ml-1 translate-y-0.5 rounded-xs bg-amber-500/80" />
          )}
        </div>
      ) : null}
    </div>
  );
}

export default function HomePage() {
  const [threadId, setThreadId] = useState<string>("emp-session");
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [inputText, setInputText] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [promotions, setPromotions] = useState<ActivePromoItem[]>([]);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [toolsDropdownOpen, setToolsDropdownOpen] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onboardingDone = window.localStorage.getItem(LOCAL_STORAGE_ONBOARDING_KEY);
    if (!onboardingDone) {
      setShowOnboarding(true);
    }

    const stored = window.localStorage.getItem(LOCAL_STORAGE_THREAD_KEY);
    const activeId = stored || createThreadId();
    if (!stored) {
      window.localStorage.setItem(LOCAL_STORAGE_THREAD_KEY, activeId);
    }
    setThreadId(activeId);

    if (stored) {
      fetch("/api/chat?thread_id=" + encodeURIComponent(stored))
        .then((res) => res.json())
        .then((data) => {
          if (Array.isArray(data.messages) && data.messages.length > 0) {
            const mapped: ChatMessageItem[] = data.messages
              .filter((m: any) => m.role === "user" || m.role === "assistant")
              .map((m: any, idx: number) => ({
                id: "hist-" + idx + "-" + (m.created_at || idx),
                role: m.role as "user" | "assistant",
                content: m.content || "",
                tools: (m.tool_calls || []).map((tc: any) => ({
                  name: tc.tool || tc.name || "Tool",
                  args: tc.args || {},
                  success: true,
                })),
              }));
            setMessages(mapped);
          }
        })
        .catch(() => {});
    }

    fetch("/api/highlights")
      .then((res) => res.json())
      .then((payload) => {
        if (payload.active_promotions) {
          setPromotions(payload.active_promotions);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleNewConversation = async () => {
    const previousId = threadId;
    const freshId = createThreadId();
    window.localStorage.setItem(LOCAL_STORAGE_THREAD_KEY, freshId);
    setThreadId(freshId);
    setMessages([]);
    setErrorMessage(null);
    setToolsDropdownOpen(false);
    try {
      await fetch(`/api/chat?thread_id=${encodeURIComponent(previousId)}`, {
        method: "DELETE",
      });
    } catch {
      // offline fallback
    }
  };

  const handleCopyMessage = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRegenerate = () => {
    if (isStreaming) return;
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUserMsg) return;
    setMessages((prev) => {
      const copy = [...prev];
      if (copy.length > 0 && copy[copy.length - 1].role === "assistant") {
        copy.pop();
      }
      return copy;
    });
    sendMessage(lastUserMsg.content);
  };

  const sendMessage = async (rawPrompt?: string) => {
    const textToSend = (rawPrompt ?? inputText).trim();
    if (!textToSend || isStreaming) return;

    setInputText("");
    setErrorMessage(null);
    setToolsDropdownOpen(false);

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now() + 1}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: textToSend, tools: [] },
      { id: assistantMsgId, role: "assistant", content: "", tools: [] },
    ]);
    setIsStreaming(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: textToSend, thread_id: threadId }),
      });

      if (!response.ok || !response.body) {
        const errPayload = await response.json().catch(() => ({}));
        throw new Error(
          errPayload.error ||
            "Não foi possível conectar ao servidor FastAPI. Verifique se `python main.py --server` está ativo na porta 8000."
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const rawBlocks = buffer.split("\n\n");
        buffer = rawBlocks.pop() || "";

        for (const block of rawBlocks) {
          const lines = block.split("\n");
          let eventType = "message";
          let dataRaw = "";

          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventType = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
              dataRaw += line.slice(5).trim();
            }
          }

          if (!dataRaw) continue;
          const parsed = JSON.parse(dataRaw);

          if (eventType === "tool_start") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      tools: [
                        ...msg.tools,
                        {
                          tool: parsed.tool,
                          args: parsed.args,
                          status: "running",
                        },
                      ],
                    }
                  : msg
              )
            );
          } else if (eventType === "tool_end") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      tools: msg.tools.map((t) =>
                        t.tool === parsed.tool && t.status === "running"
                          ? {
                              ...t,
                              status: "done",
                              outputPreview: parsed.output_preview,
                            }
                          : t
                      ),
                    }
                  : msg
              )
            );
          } else if (eventType === "token") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, content: msg.content + (parsed.text || "") }
                  : msg
              )
            );
          } else if (eventType === "error") {
            setErrorMessage(parsed.message || "Erro ao processar resposta.");
          }
        }
      }
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : "Erro inesperado de comunicação com o assistente.";
      setErrorMessage(msg);
      setMessages((prev) => prev.filter((m) => m.id !== assistantMsgId || m.content.length > 0));
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="relative flex h-screen w-screen flex-col overflow-hidden bg-[#F8FAFC] font-sans text-slate-800 antialiased selection:bg-amber-100 selection:text-amber-900">
      {/* Botão discreto para voltar ao menu principal quando houver mensagens ativas */}
      {messages.length > 0 && (
        <div className="absolute right-6 top-5 z-20 animate-in fade-in duration-200">
          <button
            type="button"
            onClick={handleNewConversation}
            className="flex items-center gap-1.5 rounded-full border border-slate-200/80 bg-white/95 px-3.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm backdrop-blur-sm transition-all hover:border-amber-400 hover:bg-white hover:text-slate-900 active:scale-95"
            title="Voltar ao menu principal / Nova conversa"
          >
            <RotateCcw className="h-3.5 w-3.5 text-slate-400" />
            <span>Voltar ao início</span>
          </button>
        </div>
      )}

      {/* 2. Main Canvas Area */}
      <main className="relative z-10 flex flex-1 flex-col justify-between overflow-hidden">
        <AnimatePresence mode="wait">
          {messages.length === 0 ? (
            /* Empty State */
            <motion.div
              key="empty-state"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20, scale: 0.98 }}
              transition={{ duration: 0.28, ease: [0.23, 1, 0.32, 1] }}
              className="my-auto flex flex-col items-center justify-center px-4 py-6 text-center max-w-3xl mx-auto w-full"
            >
            {/* Center Mascot */}
            <div className="mb-5 flex items-center justify-center">
              <Mascot size="lg" variant="music" className="w-36 h-28" />
            </div>

            {/* Headline — 1 Linha de Título e 1 Linha de Subtítulo */}
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900">
              Oi, eu sou o Téo! Como posso te ajudar hoje?
            </h1>
            <p className="mt-2 text-sm text-slate-500 max-w-xl">
              Seu especialista da{" "}
              <span className="font-semibold text-slate-700">Empório da Música</span> para
              encontrar o instrumento ideal, conferir preços e tirar dúvidas.
            </p>

            {/* Modern Composer with Orange Gradient Border & 3D Send Icon */}
            <div className="mt-7 w-full">
              <div className="rounded-[28px] p-[1.5px] bg-gradient-to-r from-[#FDBA74] via-[#FB923C] to-[#EA580C] shadow-[0_8px_28px_rgba(234,88,12,0.1)] transition-all focus-within:shadow-[0_12px_36px_rgba(234,88,12,0.18)] focus-within:from-[#FB923C] focus-within:via-[#EA580C] focus-within:to-[#C2410C]">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    sendMessage();
                  }}
                  className="rounded-[26.5px] bg-white px-5 py-3 sm:py-3.5 flex items-center justify-between gap-3 min-h-[58px]"
                >
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Pergunte sobre violões, guitarras, teclados, pedidos ou devoluções..."
                    disabled={isStreaming}
                    className="flex-1 bg-transparent text-sm sm:text-base text-slate-800 placeholder:text-slate-400 focus:outline-none disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={!inputText.trim() || isStreaming}
                    className="flex h-12 w-12 sm:h-13 sm:w-13 items-center justify-center shrink-0 transition-transform duration-200 hover:scale-105 active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
                    title="Enviar pergunta"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/icons/send.png"
                      alt="Enviar"
                      className="h-full w-full object-contain drop-shadow-sm select-none"
                    />
                  </button>
                </form>
              </div>

              {/* Quick Actions Grid with 3D Icons */}
              <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
                {QUICK_ACTIONS.map((action) => {
                  return (
                    <motion.button
                      key={action.title}
                      type="button"
                      whileHover={{ y: -3, scale: 1.015 }}
                      whileTap={{ scale: 0.97 }}
                      transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      onClick={() => sendMessage(action.prompt)}
                      className="flex flex-col items-start rounded-2xl border border-slate-200/80 bg-white/80 hover:bg-white p-3.5 text-left shadow-[0_2px_8px_rgba(0,0,0,0.02)] transition-colors hover:border-amber-400/50 hover:shadow-[0_8px_20px_rgba(249,115,22,0.06)] group"
                    >
                      <div className="flex h-12 w-12 items-center justify-center transition-transform duration-200 group-hover:scale-110 mb-2">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={action.iconSrc}
                          alt={action.title}
                          className="h-full w-full object-contain drop-shadow-sm select-none"
                        />
                      </div>
                      <span className="text-xs font-semibold text-slate-800 group-hover:text-amber-600 transition-colors line-clamp-1">
                        {action.title}
                      </span>
                      <span className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                        {action.subtitle}
                      </span>
                    </motion.button>
                  );
                })}
              </div>
            </div>
          </motion.div>
        ) : (
          /* Active Chat Conversation Feed with Elevated Cards (Image 1) */
          <motion.div
            key="active-chat"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="flex flex-1 flex-col overflow-hidden"
          >
            <div className="flex-1 overflow-y-auto px-4 sm:px-6 pt-16 sm:pt-20 pb-8">
            <div className="mx-auto flex max-w-3xl flex-col gap-6">
              <AnimatePresence initial={false}>
                {messages.map((msg, idx) => (
                  <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.32, ease: "easeOut" }}
                  key={msg.id}
                  className={`flex flex-col ${
                    msg.role === "user" ? "items-end" : "items-start"
                  }`}
                >
                  {msg.role === "user" ? (
                    /* User Bubble */
                    <div className="max-w-[85%] rounded-2xl bg-slate-900 px-5 py-3 text-xs leading-relaxed text-slate-50 shadow-sm">
                      <p>{msg.content}</p>
                    </div>
                  ) : (
                    /* Assistant Elevated Card (Image 1 Style) */
                    <div className="w-full flex flex-col gap-3">
                      <div className="relative w-full rounded-3xl border border-slate-200/80 bg-white p-5 sm:p-6 shadow-[0_8px_30px_rgba(0,0,0,0.04)]">
                        {/* Card Top Bar with Teo */}
                        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                          <div className="flex items-center gap-2">
                            <Mascot
                              size="md"
                              variant={msg.content ? "happy" : "thinking"}
                              className="h-10 w-14 shrink-0"
                            />
                            <span className="text-base font-semibold tracking-tight text-slate-900">
                              Téo - Empório da Música
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5">
                            {msg.content && (
                              <button
                                type="button"
                                onClick={() => handleCopyMessage(msg.id, msg.content)}
                                className="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                                title="Copiar resposta"
                              >
                                {copiedId === msg.id ? (
                                  <Check className="h-3.5 w-3.5 text-emerald-500" />
                                ) : (
                                  <Copy className="h-3.5 w-3.5" />
                                )}
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Content with live typewriter animation & ThoughtLine */}
                        <AssistantCardContent
                          content={msg.content}
                          isLatestStreaming={isStreaming && idx === messages.length - 1}
                          tools={msg.tools}
                          onSelectPrompt={(p) => sendMessage(p)}
                        />
                      </div>

                      {/* Regenerate pill below the card (Image 1 Style) */}
                      {idx === messages.length - 1 && !isStreaming && msg.content && (
                        <div className="flex justify-center w-full mt-1">
                          <button
                            type="button"
                            onClick={handleRegenerate}
                            className="flex items-center gap-1.5 rounded-full border border-slate-200/80 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm hover:border-amber-400 hover:bg-amber-50/50 hover:text-amber-700 transition-all active:scale-95"
                          >
                            <RotateCcw className="h-3 w-3 text-slate-400 group-hover:text-amber-600" />
                            <span>Regenerar resposta</span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ))}
              </AnimatePresence>

              {/* Error Banner */}
              {errorMessage && (
                <div className="my-2 flex items-center justify-between rounded-2xl border border-red-200 bg-red-50 p-4 text-xs text-red-800">
                  <div className="flex items-center gap-2.5">
                    <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
                    <span>{errorMessage}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      const lastUser = [...messages]
                        .reverse()
                        .find((m) => m.role === "user");
                      if (lastUser) sendMessage(lastUser.content);
                    }}
                    className="inline-flex items-center gap-1 rounded-full border border-red-200 bg-white px-3 py-1 font-semibold text-red-800 hover:bg-red-50"
                  >
                    <RefreshCw className="h-3 w-3" />
                    <span>Tentar novamente</span>
                  </button>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
          </motion.div>
        )}
        </AnimatePresence>

        {/* 3. Bottom Composer when conversation is active */}
        <AnimatePresence>
          {messages.length > 0 && (
            <motion.footer
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 24 }}
              transition={{ duration: 0.32, ease: [0.23, 1, 0.32, 1] }}
              className="shrink-0 bg-gradient-to-t from-[#F8FAFC] via-[#F8FAFC]/95 to-transparent px-4 pb-5 pt-3"
            >
            <div className="mx-auto max-w-3xl">
              <div className="rounded-[24px] p-[1.5px] bg-gradient-to-r from-[#FDBA74] via-[#FB923C] to-[#EA580C] shadow-[0_6px_22px_rgba(234,88,12,0.08)] transition-all focus-within:shadow-[0_8px_28px_rgba(234,88,12,0.14)] focus-within:from-[#FB923C] focus-within:via-[#EA580C] focus-within:to-[#C2410C]">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    sendMessage();
                  }}
                  className="flex items-center gap-2 rounded-[22.5px] bg-white px-4 py-2"
                >
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Digite sua dúvida sobre produtos, estoque ou políticas..."
                    disabled={isStreaming}
                    className="flex-1 bg-transparent text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none disabled:opacity-50"
                  />

                  <button
                    type="submit"
                    disabled={!inputText.trim() || isStreaming}
                    className="flex h-10 w-10 sm:h-11 sm:w-11 items-center justify-center shrink-0 transition-transform hover:scale-105 active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
                    title="Enviar mensagem"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/icons/send.png"
                      alt="Enviar"
                      className="h-full w-full object-contain drop-shadow-sm select-none"
                    />
                  </button>
                </form>
              </div>

              <p className="mt-2 text-center text-[11px] text-slate-400">
                Empório da Música • Atendimento Oficial • Campo Grande/MS
              </p>
            </div>
          </motion.footer>
        )}
        </AnimatePresence>

        {/* 4. Slide-over Drawer for Store Details & Promos (triggered by (i) icon) */}
        {drawerOpen && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/20 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="flex h-full w-full max-w-sm flex-col justify-between border-l border-slate-200 bg-white p-6 shadow-2xl animate-in slide-in-from-right duration-200">
              <div className="flex flex-col gap-5 overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-2.5">
                    <Mascot size="sm" variant="music" className="h-7 w-7" />
                    <div>
                      <h2 className="text-sm font-semibold text-slate-900">
                        Empório da Música
                      </h2>
                      <span className="text-[11px] text-slate-500">
                        Campo Grande / MS
                      </span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setDrawerOpen(false)}
                    className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-800"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Session Actions: Voltar ao Início / Nova Conversa */}
                <button
                  type="button"
                  onClick={() => {
                    handleNewConversation();
                    setDrawerOpen(false);
                  }}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 py-2.5 text-xs font-semibold text-white shadow-sm transition-all hover:bg-slate-800 active:scale-98"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span>Voltar ao Menu Principal / Nova Conversa</span>
                </button>

                {/* Active Promotions Highlights */}
                {promotions.length > 0 && (
                  <div className="mt-2 flex flex-col gap-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Ofertas Ativas
                      </span>
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800">
                        {promotions.length} ativas
                      </span>
                    </div>

                    <div className="flex flex-col gap-2">
                      {promotions.map((p) => {
                        const discounted = p.price_brl * (1 - p.discount_percent / 100);
                        return (
                          <button
                            key={p.product_id}
                            type="button"
                            onClick={() => {
                              setDrawerOpen(false);
                              sendMessage(`Quanto custa o ${p.name}?`);
                            }}
                            className="group flex flex-col rounded-xl border border-slate-200 p-3 text-left transition-all hover:border-amber-400 hover:bg-amber-50/50"
                          >
                            <div className="flex items-start justify-between gap-1">
                              <span className="line-clamp-1 text-xs font-medium text-slate-800 group-hover:text-amber-600">
                                {p.name}
                              </span>
                              <span className="shrink-0 text-[10px] font-bold text-amber-600">
                                -{p.discount_percent}%
                              </span>
                            </div>
                            <div className="mt-1 flex items-baseline justify-between text-xs">
                              <span className="text-[10px] text-slate-400 line-through">
                                R$ {p.price_brl.toFixed(0)}
                              </span>
                              <span className="font-semibold text-slate-900">
                                R$ {discounted.toFixed(2).replace(".", ",")}
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Physical Store Info */}
                <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600">
                  <h4 className="font-semibold text-slate-900">Loja Física Campo Grande</h4>
                  <div className="mt-2.5 flex items-start gap-2">
                    <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" />
                    <span>Rua 14 de Maio, 3200 — Centro, Campo Grande/MS</span>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 shrink-0 text-amber-600" />
                    <span>Seg–Sex 09h às 18h • Sáb 09h às 13h</span>
                  </div>
                  <a
                    href="https://wa.me/556733214500"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white py-2 text-xs font-semibold text-slate-800 transition-all hover:bg-amber-50 hover:border-amber-400"
                  >
                    <Phone className="h-3.5 w-3.5 text-amber-600" />
                    <span>WhatsApp: (67) 3321-4500</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Onboarding Splash Carousel */}
      <AnimatePresence>
        {showOnboarding && (
          <OnboardingSplash
            onComplete={() => {
              window.localStorage.setItem(LOCAL_STORAGE_ONBOARDING_KEY, "true");
              setShowOnboarding(false);
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
