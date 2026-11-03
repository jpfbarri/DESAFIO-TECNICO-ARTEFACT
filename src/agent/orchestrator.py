import json
import logging
import os
import re
from typing import Any, Dict, Generator, List, Optional, Tuple
from pydantic import BaseModel, Field

from src.agent.llm_client import (
    call_gemini_rest_api,
    get_configured_provider_and_model,
    has_active_api_key,
)
from src.agent.memory_checkpointer import ChatMessageRecord, SQLiteConversationCheckpointer
from src.rag.policy_retriever import normalize_text
from src.tools.mcp_server import execute_store_tool

logger = logging.getLogger(__name__)

OUT_OF_SCOPE_TOPICS = (
    "receita", "bolo", "culinaria", "futebol", "flamengo", "corinthians",
    "palmeiras", "politica", "eleicao", "presidente", "programacao",
    "javascript", "codigo python", "equacao", "derivada", "integral",
    "previsao do tempo", "chover", "horoscopo", "signo", "criptomoeda", "bitcoin",
)

ACCESSORY_KEYWORDS = (
    "encordoamento", "corda avulsa", "cordas para", "jogo de cordas",
    "palheta", "palhetas", "cabo p10", "cabos", "pedal", "pedais",
    "pedaleira", "amplificador", "amplificadores", "cubo de guitarra",
    "case", "cases", "capa para", "bag para", "correia", "afinador",
    "baqueta", "baquetas", "suporte de", "estante de partitura",
)

KNOWN_BRANDS_AND_MODELS = (
    "takamine", "gd20", "gc5ce", "gn51ce", "gc1ce", "yamaha", "c40", "c70",
    "f310", "fg800", "ntx1", "apx600", "cg162s", "tagima", "memphis", "ac-39",
    "dallas", "woodstock", "vegas", "tw-7", "giannini", "gn-15", "gf-1r",
    "gf-3d", "gnf-3", "gwne-7", "rozini", "rc-104", "rv-174", "rv-175",
    "shelby", "sn-100", "sgd-195e", "sn-7c", "crafter", "ht-100", "d-8",
    "ce-15", "martin", "d-28", "d-28e", "taylor", "110e", "214ce", "kalani",
    "kal-700t", "ohana", "ck-20", "kala", "ka-abp-ctg", "ibanez", "fender",
    "gibson", "epiphone", "squier", "casio", "roland", "korg", "pearl",
    "mapex", "michael", "eagle", "jupiter", "weril",
)

CATEGORY_KEYWORDS_MAP: Dict[str, str] = {
    "violao": "Violões",
    "violoes": "Violões",
    "guitarra": "Guitarras",
    "guitarras": "Guitarras",
    "baixo": "Baixos",
    "baixos": "Baixos",
    "contrabaixo": "Baixos",
    "bateria": "Baterias e Percussão",
    "baterias": "Baterias e Percussão",
    "percussao": "Baterias e Percussão",
    "teclado": "Teclados e Pianos",
    "teclados": "Teclados e Pianos",
    "piano": "Teclados e Pianos",
    "pianos": "Teclados e Pianos",
    "sintetizador": "Teclados e Pianos",
    "flauta": "Instrumentos de Sopro (Madeiras)",
    "saxofone": "Instrumentos de Sopro (Madeiras)",
    "clarinete": "Instrumentos de Sopro (Madeiras)",
    "oboe": "Instrumentos de Sopro (Madeiras)",
    "trompete": "Instrumentos de Sopro (Metais)",
    "trombone": "Instrumentos de Sopro (Metais)",
    "tuba": "Instrumentos de Sopro (Metais)",
    "violino": "Cordas Orquestrais",
    "viola de arco": "Cordas Orquestrais",
    "violoncelo": "Cordas Orquestrais",
    "ukulele": "Ukuleles",
    "ukuleles": "Ukuleles",
}


class ToolExecutionStep(BaseModel):
    tool_name: str = Field(..., description="Nome da tool acionada")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos enviados")
    output: str = Field(..., description="Saída textual retornada pela tool")


class AgentTurnResponse(BaseModel):
    thread_id: str
    reply: str
    tool_calls: List[ToolExecutionStep] = Field(default_factory=list)
    provider: str
    model: str


class EmporioMusicAgent:
    """Agente ReAct da Empório da Música com memória SQLite, MCP tools e resiliência 429."""

    def __init__(self, checkpointer: Optional[SQLiteConversationCheckpointer] = None) -> None:
        self.checkpointer = checkpointer or SQLiteConversationCheckpointer()

    def run_turn(self, user_message: str, thread_id: str = "default") -> AgentTurnResponse:
        provider, model = get_configured_provider_and_model()
        history = self.checkpointer.get_history(thread_id)
        self.checkpointer.save_message(thread_id=thread_id, role="user", content=user_message)

        tool_steps, reply_text = self._execute_react_cycle(user_message, history)

        serialized_calls = [step.model_dump() for step in tool_steps]
        self.checkpointer.save_message(
            thread_id=thread_id,
            role="assistant",
            content=reply_text,
            tool_calls=serialized_calls,
        )
        return AgentTurnResponse(
            thread_id=thread_id,
            reply=reply_text,
            tool_calls=tool_steps,
            provider=provider,
            model=model,
        )

    def stream_turn_sse(
        self, user_message: str, thread_id: str = "default"
    ) -> Generator[Dict[str, Any], None, None]:
        """Gera eventos SSE: tool_start, tool_end, token, done e error."""
        try:
            history = self.checkpointer.get_history(thread_id)
            self.checkpointer.save_message(thread_id=thread_id, role="user", content=user_message)

            planned_calls = self._plan_tool_calls(user_message, history)
            tool_steps: List[ToolExecutionStep] = []

            for tool_name, tool_args in planned_calls:
                yield {"event": "tool_start", "data": {"tool": tool_name, "args": tool_args}}
                output = execute_store_tool(tool_name, tool_args)
                step = ToolExecutionStep(tool_name=tool_name, arguments=tool_args, output=output)
                tool_steps.append(step)
                yield {
                    "event": "tool_end",
                    "data": {"tool": tool_name, "output_preview": output[:220]},
                }

            reply_text = self._generate_final_reply(user_message, history, tool_steps)
            for token_chunk in self._chunk_text_for_streaming(reply_text):
                yield {"event": "token", "data": {"text": token_chunk}}

            self.checkpointer.save_message(
                thread_id=thread_id,
                role="assistant",
                content=reply_text,
                tool_calls=[s.model_dump() for s in tool_steps],
            )
            yield {
                "event": "done",
                "data": {
                    "thread_id": thread_id,
                    "tools_used": [s.tool_name for s in tool_steps],
                },
            }
        except Exception as err:
            logger.exception("Erro durante streaming do agente:")
            yield {"event": "error", "data": {"message": str(err)}}

    def _execute_react_cycle(
        self, user_message: str, history: List[ChatMessageRecord]
    ) -> Tuple[List[ToolExecutionStep], str]:
        planned_calls = self._plan_tool_calls(user_message, history)
        tool_steps: List[ToolExecutionStep] = []
        for tool_name, tool_args in planned_calls:
            output = execute_store_tool(tool_name, tool_args)
            tool_steps.append(
                ToolExecutionStep(tool_name=tool_name, arguments=tool_args, output=output)
            )
        reply_text = self._generate_final_reply(user_message, history, tool_steps)
        return tool_steps, reply_text

    def _plan_tool_calls(
        self, user_message: str, history: List[ChatMessageRecord]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        norm_msg = normalize_text(user_message)
        if self._is_general_out_of_scope(norm_msg):
            return []
        if self._is_accessory_request(norm_msg):
            return [("search_policies", {"query": "escopo exclusivo instrumentos musicais acessórios"})]

        calls: List[Tuple[str, Dict[str, Any]]] = []
        order_id = self._extract_order_id(user_message, history)
        customer_id_str = self._extract_customer_identifier(user_message, history)

        is_return_or_exchange = any(
            w in norm_msg
            for w in ("arrependi", "devolver", "devolucao", "trocar", "troca", "reembolso", "defeito")
        )
        is_order_query = any(
            w in norm_msg
            for w in ("pedido", "rastreio", "rastreamento", "status", "entrega do meu", "comprei")
        ) or (order_id is not None and customer_id_str != "")

        if is_return_or_exchange:
            calls.append(("search_policies", {"query": user_message}))

        if (is_order_query or is_return_or_exchange) and order_id is not None:
            calls.append(
                ("get_order_status", {"order_id": order_id, "customer_identifier": customer_id_str})
            )

        if self._is_escalation_or_complaint(norm_msg):
            calls.append(
                (
                    "escalate_to_human",
                    {
                        "customer_name": customer_id_str or "Cliente Empório",
                        "customer_contact": customer_id_str or "Não informado",
                        "reason": user_message[:150],
                        "order_id": order_id,
                    },
                )
            )

        if any(w in norm_msg for w in ("promocao", "promocoes", "black friday", "queima de estoque", "liquidacao", "oferta")):
            campaign_q = self._extract_campaign_query(norm_msg)
            calls.append(("get_active_promotions", {"campaign_query": campaign_q}))

        specific_model = self._extract_specific_model_query(user_message, norm_msg)
        if specific_model and not is_order_query:
            calls.append(("get_product_price", {"product_query": specific_model}))
        elif self._is_catalog_search(norm_msg):
            search_args = self._build_search_products_args(norm_msg)
            calls.append(("search_products", search_args))

        if self._is_policy_question(norm_msg) and not any(c[0] == "search_policies" for c in calls):
            calls.append(("search_policies", {"query": user_message}))

        return calls

    def _is_general_out_of_scope(self, norm_msg: str) -> bool:
        return any(topic in norm_msg for topic in OUT_OF_SCOPE_TOPICS)

    def _is_accessory_request(self, norm_msg: str) -> bool:
        if "7 cordas" in norm_msg or "cordas orquestrais" in norm_msg or "cordas de nylon" in norm_msg:
            return False
        return any(acc in norm_msg for acc in ACCESSORY_KEYWORDS)

    def _is_escalation_or_complaint(self, norm_msg: str) -> bool:
        return any(
            w in norm_msg
            for w in (
                "reclamacao", "reclamar", "atendente humano", "falar com humano",
                "falar com atendente", "gerente", "gerencia", "procon", "avaria no transporte",
            )
        )

    def _is_policy_question(self, norm_msg: str) -> bool:
        policy_terms = (
            "horario", "funcionamento", "abre", "fecha", "sabado", "domingo", "feriado",
            "endereco", "onde fica", "localizacao", "campo grande", "telefone", "whatsapp",
            "contato", "pagamento", "pix", "parcela", "parcelamento", "cartao", "boleto",
            "frete", "motoboy", "sedex", "pac", "jadlog", "garantia", "lgpd", "privacidade",
            "boquilha", "personalizado", "regulagem", "venda final",
        )
        return any(term in norm_msg for term in policy_terms)

    def _is_catalog_search(self, norm_msg: str) -> bool:
        if any(cat_key in norm_msg for cat_key in CATEGORY_KEYWORDS_MAP):
            return True
        return any(
            w in norm_msg
            for w in ("instrumentos", "catalogo", "opcoes", "disponiveis", "ate r", "barato", "iniciante")
        )

    def _extract_specific_model_query(self, raw_msg: str, norm_msg: str) -> Optional[str]:
        tokens = norm_msg.split()
        matched_brands = [b for b in KNOWN_BRANDS_AND_MODELS if b in tokens or b in norm_msg]
        if not matched_brands:
            return None
        # Se o usuário pede "opções de violões até R$1000" sem citar marca/modelo, é busca de catálogo
        model_pattern = re.search(
            r"((?:takamine|yamaha|tagima|giannini|rozini|shelby|crafter|martin|taylor|kalani|ohana|kala|ibanez|fender|gibson|roland|casio)\s*[a-z0-9\-]*)",
            norm_msg,
        )
        if model_pattern:
            extracted = model_pattern.group(1).strip()
            if len(extracted.split()) >= 2 or any(ch.isdigit() for ch in extracted):
                return extracted
        for token in raw_msg.split():
            clean_tok = re.sub(r"[^\w\-]", "", token)
            if any(ch.isdigit() for ch in clean_tok) and any(ch.isalpha() for ch in clean_tok):
                if not clean_tok.lower().startswith("r$"):
                    return clean_tok
        return matched_brands[0] if "quanto custa" in norm_msg or "preco" in norm_msg else None

    def _build_search_products_args(self, norm_msg: str) -> Dict[str, Any]:
        category = None
        for key, cat_name in CATEGORY_KEYWORDS_MAP.items():
            if key in norm_msg:
                category = cat_name
                break
        max_price = None
        price_match = re.search(r"(?:ate|menos de|abaixo de|maximo|no maximo)\s*(?:r\$\s*)?(\d+(?:[\.,]\d+)?)", norm_msg)
        if not price_match:
            price_match = re.search(r"r\$\s*(\d+(?:[\.,]\d+)?)", norm_msg)
        if price_match:
            val_str = price_match.group(1).replace(".", "").replace(",", ".")
            max_price = float(val_str)

        query_terms = []
        for feature in ("nylon", "aco", "folk", "dreadnought", "7 cordas", "eletrico", "estudante", "iniciante", "tenor", "concert", "soprano"):
            if feature in norm_msg:
                query_terms.append(feature)

        args: Dict[str, Any] = {"only_available": True}
        if category:
            args["category"] = category
        if query_terms:
            args["query"] = " ".join(query_terms)
        if max_price is not None:
            args["max_price_brl"] = max_price
        return args

    def _extract_campaign_query(self, norm_msg: str) -> Optional[str]:
        for camp in ("black friday", "inverno", "queima de estoque", "oferta especial", "aniversario", "volta as aulas"):
            if camp in norm_msg:
                return camp
        return None

    def _extract_order_id(
        self, user_message: str, history: List[ChatMessageRecord]
    ) -> Optional[int]:
        patterns = [
            r"pedido\s*(?:n[ºo°]?|#|:)?\s*(\d{1,3})\b",
            r"#(\d{1,3})\b",
            r"\border\s*(\d{1,3})\b",
        ]
        for pat in patterns:
            match = re.search(pat, user_message.lower())
            if match:
                return int(match.group(1))
        for past in reversed(history):
            for pat in patterns:
                match = re.search(pat, past.content.lower())
                if match:
                    return int(match.group(1))
        return None

    def _extract_customer_identifier(
        self, user_message: str, history: List[ChatMessageRecord]
    ) -> str:
        combined_texts = [user_message] + [m.content for m in reversed(history) if m.role == "user"]
        for text in combined_texts:
            email_match = re.search(r"[\w\.\-]+@[\w\.\-]+\.\w+", text)
            if email_match:
                return email_match.group(0)
            phone_match = re.search(r"(?:\(?\d{2}\)?\s*)?\d{4,5}[\-\s]?\d{4}", text)
            if phone_match:
                return phone_match.group(0)
            name_match = re.search(
                r"(?:meu nome [eé]|sou o|sou a|cliente|titular)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç]+)+)",
                text,
                re.IGNORECASE,
            )
            if name_match:
                return name_match.group(1).strip()
        return ""

    def _generate_final_reply(
        self,
        user_message: str,
        history: List[ChatMessageRecord],
        tool_steps: List[ToolExecutionStep],
    ) -> str:
        if has_active_api_key():
            llm_reply = self._try_call_live_llm(user_message, history, tool_steps)
            if llm_reply:
                return llm_reply
        return self._synthesize_grounded_response(user_message, tool_steps)

    def _try_call_live_llm(
        self,
        user_message: str,
        history: List[ChatMessageRecord],
        tool_steps: List[ToolExecutionStep],
    ) -> Optional[str]:
        try:
            provider, model = get_configured_provider_and_model()
            if provider != "google":
                return None
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
            context_blocks = "\n\n".join(
                f"[Resultado da Tool `{step.tool_name}`]:\n{step.output}" for step in tool_steps
            )
            augmented_prompt = (
                f"Mensagem do cliente: {user_message}\n\n"
                f"Dados consultados no sistema da Empório da Música:\n{context_blocks}\n\n"
                "Responda ao cliente seguindo rigorosamente a persona e os dados acima."
            )
            messages = [{"role": m.role, "content": m.content} for m in history[-6:]]
            messages.append({"role": "user", "content": augmented_prompt})
            resp = call_gemini_rest_api(messages=messages, model=model, api_key=api_key, enable_tools=False)
            candidates = resp.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    return text
        except Exception as err:
            logger.warning("Fallback para sintetizador determinístico após erro na API LLM: %s", err)
        return None

    def _synthesize_grounded_response(
        self, user_message: str, tool_steps: List[ToolExecutionStep]
    ) -> str:
        norm_msg = normalize_text(user_message)
        if not tool_steps:
            if self._is_general_out_of_scope(norm_msg):
                return (
                    "Olá! Aqui é da **Empório da Música** 🎸. Adoraria bater um papo, mas meu foco "
                    "é exclusivamente ajudar você com **instrumentos musicais**, preços, estoque, "
                    "pedidos e políticas da nossa loja em Campo Grande/MS.\n\n"
                    "Se estiver procurando um violão, guitarra, teclado, bateria ou quiser consultar "
                    "um pedido, é só me chamar!"
                )
            if any(w in norm_msg for w in ("pedido", "rastreio", "rastreamento", "status")):
                return (
                    "Claro! Para eu consultar o status e o código de rastreamento do seu pedido com "
                    "segurança (seguindo a LGPD), me informe por favor:\n"
                    "1. O **número do pedido** (ex: `#1`, `#4`, `#8`);\n"
                    "2. O **e-mail**, **telefone** ou **nome completo** cadastrado na compra."
                )
            return (
                "Olá! Bem-vindo(a) à **Empório da Música** — *Sua música começa aqui!* 🎶\n\n"
                "Como posso te ajudar hoje? Posso consultar nosso catálogo de instrumentos "
                "(violões, guitarras, baixos, baterias, teclados, sopro e ukuleles), verificar "
                "preços e descontos no PIX, acompanhar seu pedido ou tirar dúvidas sobre frete, "
                "trocas e garantia!"
            )

        if self._is_accessory_request(norm_msg):
            return (
                "Poxa, que pena! Aqui na **Empório da Música** nós trabalhamos **exclusivamente com "
                "instrumentos musicais** (violões, guitarras, baixos, baterias, teclados, sopro, "
                "cordas orquestrais e ukuleles).\n\n"
                "Conforme nossa política de atendimento, **não comercializamos acessórios** como "
                "cordas avulsas/encordoamentos, palhetas, cabos, cases, pedais ou amplificadores. "
                "Recomendo procurar lojas parceiras especializadas em acessórios musicais na região. "
                "Mas se quiser conhecer algum instrumento novo do nosso catálogo, estou à disposição!"
            )

        sections = [
            "Olá! Aqui está o que consultei para você no sistema da **Empório da Música**:",
        ]
        for step in tool_steps:
            sections.append(step.output)

        if any(s.tool_name == "search_policies" for s in tool_steps) and any(
            w in norm_msg for w in ("arrependi", "devolver", "devolucao")
        ) and not any(s.tool_name == "get_order_status" for s in tool_steps):
            sections.append(
                "💡 **Como proceder com a sua devolução:**\n"
                "- Para **compras online (Direito de Arrependimento - CDC)**, você pode devolver em até **7 (sete) dias corridos após o recebimento**, sem precisar de justificativa, desde que o instrumento esteja na embalagem original, sem sinais de uso e com os manuais.\n"
                "- O **frete de devolução é por conta da loja** e o reembolso ocorre em até **10 dias úteis** na mesma forma de pagamento.\n"
                "- Se quiser que eu verifique a elegibilidade do seu pedido agora mesmo, me informe o **número do pedido** e o seu **e-mail cadastrado**!"
            )

        sections.append("Posso te ajudar com mais alguma dúvida ou detalhe sobre algum instrumento?")
        return "\n\n".join(sections)

    def _chunk_text_for_streaming(self, text: str, words_per_chunk: int = 5) -> List[str]:
        tokens = re.split(r"(\s+)", text)
        chunks: List[str] = []
        current: List[str] = []
        word_count = 0
        for tok in tokens:
            current.append(tok)
            if tok.strip():
                word_count += 1
            if word_count >= words_per_chunk:
                chunks.append("".join(current))
                current = []
                word_count = 0
        if current:
            chunks.append("".join(current))
        return chunks

