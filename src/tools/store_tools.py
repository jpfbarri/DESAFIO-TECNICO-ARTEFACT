import hashlib
import json
import re
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.database.connection import get_db_connection
from src.rag.policy_retriever import normalize_text, search_store_policies

PIX_DISCOUNT_RATE = 0.05
MIN_INSTALLMENT_3X_BRL = 50.0
MIN_INSTALLMENT_6X_BRL = 80.0
MIN_INSTALLMENT_12X_BRL = 100.0
MAX_SEARCH_RESULTS = 10
MAX_SIMILAR_ALTERNATIVES = 3
SLA_COMPLAINT_HOURS = 24
WHATSAPP_SUPPORT_NUMBER = "(67) 3321-4500"

CATEGORY_SYNONYM_MAP: Dict[str, str] = {
    "violao": "violoes",
    "violoes": "violoes",
    "guitarra": "guitarras",
    "baixo": "baixos",
    "contrabaixo": "baixos",
    "bateria": "baterias",
    "percussao": "baterias",
    "teclado": "teclados",
    "piano": "teclados",
    "sintetizador": "teclados",
    "sopro": "sopro",
    "flauta": "madeiras",
    "saxofone": "madeiras",
    "clarinete": "madeiras",
    "trompete": "metais",
    "trombone": "metais",
    "violino": "orquestrais",
    "violoncelo": "orquestrais",
    "ukulele": "ukuleles",
}


def _register_sqlite_normalizer(conn: sqlite3.Connection) -> None:
    conn.create_function("NORM", 1, lambda val: normalize_text(str(val)) if val else "")


def calculate_installments_summary(amount_brl: float) -> str:
    max_installments = 1
    for n_inst in range(12, 0, -1):
        installment_val = amount_brl / n_inst
        if n_inst >= 7 and installment_val >= MIN_INSTALLMENT_12X_BRL:
            max_installments = n_inst
            break
        if 4 <= n_inst <= 6 and installment_val >= MIN_INSTALLMENT_6X_BRL:
            max_installments = n_inst
            break
        if 1 <= n_inst <= 3 and installment_val >= MIN_INSTALLMENT_3X_BRL:
            max_installments = n_inst
            break
    if max_installments <= 1:
        return f"À vista R$ {amount_brl:.2f} (valor abaixo do mínimo de R$ 50,00 para parcelamento)"
    per_month = amount_brl / max_installments
    return f"Até {max_installments}x sem juros de R$ {per_month:.2f} no cartão de crédito"


def search_products(
    query: str = "",
    category: Optional[str] = None,
    max_price_brl: Optional[float] = None,
    min_price_brl: Optional[float] = None,
    only_available: bool = True,
) -> str:
    """Busca instrumentos musicais no catálogo por termo, categoria e faixa de preço."""
    with get_db_connection() as conn:
        _register_sqlite_normalizer(conn)
        rows = _execute_product_search_query(
            conn, query, category, max_price_brl, min_price_brl, only_available
        )
        if not rows:
            return _format_empty_product_search(
                conn, query, category, max_price_brl, min_price_brl
            )
        return _format_product_search_results(rows)


def _execute_product_search_query(
    conn: sqlite3.Connection,
    query: str,
    category: Optional[str],
    max_price_brl: Optional[float],
    min_price_brl: Optional[float],
    only_available: bool,
) -> List[sqlite3.Row]:
    sql = """
        SELECT p.product_id, p.name, p.price_brl, p.stock_quantity, p.status,
               p.description, p.specs, c.name AS category_name,
               pr.discount_percent AS active_discount, pr.description AS promo_name
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN promotions pr ON p.product_id = pr.product_id AND pr.is_active = 1
        WHERE 1=1
    """
    params: List[Any] = []
    if only_available:
        sql += " AND p.status = 'active' AND p.stock_quantity > 0"
    if category and category.strip():
        norm_cat = normalize_text(category).strip()
        mapped_cat = CATEGORY_SYNONYM_MAP.get(norm_cat, norm_cat)
        sql += " AND NORM(c.name) LIKE ?"
        params.append(f"%{mapped_cat}%")
    if query and query.strip():
        tokens = [
            t for t in normalize_text(query).split()
            if len(t) > 1 and t not in ("ate", "de", "para", "com", "reais", "brl", "opcoes", "disponiveis")
        ]
        for token in tokens:
            mapped_token = CATEGORY_SYNONYM_MAP.get(token, token)
            sql += " AND (NORM(p.name) LIKE ? OR NORM(p.description) LIKE ? OR NORM(c.name) LIKE ? OR NORM(p.specs) LIKE ?)"
            params.extend([f"%{token}%", f"%{token}%", f"%{mapped_token}%", f"%{token}%"])
    if max_price_brl is not None:
        sql += " AND p.price_brl <= ?"
        params.append(float(max_price_brl))
    if min_price_brl is not None:
        sql += " AND p.price_brl >= ?"
        params.append(float(min_price_brl))
    sql += f" ORDER BY p.price_brl ASC LIMIT {MAX_SEARCH_RESULTS}"
    return conn.execute(sql, params).fetchall()


def _format_empty_product_search(
    conn: sqlite3.Connection,
    query: str,
    category: Optional[str],
    max_price_brl: Optional[float],
    min_price_brl: Optional[float],
) -> str:
    unavailable = _execute_product_search_query(
        conn, query, category, max_price_brl, min_price_brl, only_available=False
    )
    if unavailable:
        items_desc = ", ".join(
            f"{r['name']} (status: {r['status']}, estoque: {r['stock_quantity']})"
            for r in unavailable
        )
        return (
            f"Nenhum produto disponível em estoque para os filtros informados. "
            f"Itens encontrados mas indisponíveis no momento: {items_desc}."
        )
    return "Nenhum instrumento encontrado no catálogo com os critérios especificados."


def _format_product_search_results(rows: List[sqlite3.Row]) -> str:
    lines = [f"Encontrados {len(rows)} instrumento(s):"]
    for row in rows:
        price = float(row["price_brl"])
        promo_disc = row["active_discount"]
        if promo_disc:
            final_price = price * (1.0 - float(promo_disc) / 100.0)
            price_str = (
                f"De R$ {price:.2f} por R$ {final_price:.2f} "
                f"({promo_disc:.0f}% OFF - {row['promo_name']} | não cumulativo com PIX)"
            )
        else:
            pix_price = price * (1.0 - PIX_DISCOUNT_RATE)
            price_str = f"R$ {price:.2f} (ou R$ {pix_price:.2f} à vista no PIX com 5% OFF)"
        lines.append(
            f"- [ID {row['product_id']}] {row['name']} ({row['category_name']}) | "
            f"{price_str} | Estoque: {row['stock_quantity']} un. | Status: {row['status']}"
        )
    return "\n".join(lines)


def get_product_price(product_query: str) -> str:
    """Consulta preço detalhado, descontos ativos/expirados, PIX, parcelamento e estoque de um produto."""
    if not product_query or not str(product_query).strip():
        return "Informe o nome ou ID do instrumento que deseja consultar."
    with get_db_connection() as conn:
        _register_sqlite_normalizer(conn)
        product = _find_single_product(conn, str(product_query).strip())
        if not product:
            return f"Produto '{product_query}' não encontrado no catálogo da Empório da Música."
        promotions = conn.execute(
            "SELECT discount_percent, description, is_active FROM promotions WHERE product_id = ?",
            (product["product_id"],),
        ).fetchall()
        alternatives = _find_similar_alternatives(conn, product)
        return _format_detailed_product_price(product, promotions, alternatives)


def _find_single_product(conn: sqlite3.Connection, product_query: str) -> Optional[sqlite3.Row]:
    base_sql = """
        SELECT p.*, c.name AS category_name
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
    """
    if product_query.isdigit():
        row = conn.execute(f"{base_sql} WHERE p.product_id = ?", (int(product_query),)).fetchone()
        if row:
            return row
    norm_q = normalize_text(product_query).strip()
    row = conn.execute(f"{base_sql} WHERE NORM(p.name) LIKE ?", (f"%{norm_q}%",)).fetchone()
    if row:
        return row
    tokens = [t for t in norm_q.split() if len(t) > 1]
    if not tokens:
        return None
    conditions = " AND ".join(["NORM(p.name) LIKE ?"] * len(tokens))
    params = [f"%{t}%" for t in tokens]
    return conn.execute(f"{base_sql} WHERE {conditions}", params).fetchone()


def _find_similar_alternatives(
    conn: sqlite3.Connection, product: sqlite3.Row
) -> List[sqlite3.Row]:
    if product["status"] == "active" and int(product["stock_quantity"]) > 0:
        return []
    return conn.execute(
        """
        SELECT product_id, name, price_brl, stock_quantity
        FROM products
        WHERE category_id = ? AND product_id != ? AND status = 'active' AND stock_quantity > 0
        ORDER BY ABS(price_brl - ?) ASC
        LIMIT ?
        """,
        (product["category_id"], product["product_id"], product["price_brl"], MAX_SIMILAR_ALTERNATIVES),
    ).fetchall()


def _format_detailed_product_price(
    product: sqlite3.Row,
    promotions: List[sqlite3.Row],
    alternatives: List[sqlite3.Row],
) -> str:
    price = float(product["price_brl"])
    active_promos = [p for p in promotions if int(p["is_active"]) == 1]
    expired_promos = [p for p in promotions if int(p["is_active"]) == 0]

    lines = [
        f"Instrumento: {product['name']} (ID: {product['product_id']} | Categoria: {product['category_name']})",
        f"Status no Catálogo: {product['status']} | Quantidade em Estoque: {product['stock_quantity']} unidade(s)",
        f"Preço de Tabela: R$ {price:.2f}",
    ]
    if active_promos:
        promo = active_promos[0]
        disc = float(promo["discount_percent"])
        promo_price = price * (1.0 - disc / 100.0)
        lines.append(
            f"Promoção Ativa: {promo['description']} ({disc:.0f}% OFF) -> Preço Promocional: R$ {promo_price:.2f}"
        )
        lines.append(
            "Regra de Cumulatividade: O desconto de 5% do PIX NÃO se aplica sobre preços já promocionais."
        )
        lines.append(f"Parcelamento: {calculate_installments_summary(promo_price)}")
    else:
        pix_price = price * (1.0 - PIX_DISCOUNT_RATE)
        lines.append(f"Preço à vista no PIX (5% de desconto): R$ {pix_price:.2f}")
        lines.append(f"Parcelamento: {calculate_installments_summary(price)}")

    if expired_promos:
        exp_names = ", ".join(
            f"{p['description']} ({p['discount_percent']:.0f}% OFF - EXPIRADA/INATIVA)"
            for p in expired_promos
        )
        lines.append(f"Histórico de Promoções Encerradas (não vigentes): {exp_names}")

    lines.append(f"Descrição: {product['description']}")
    lines.append(f"Especificações: {product['specs']}")

    if alternatives:
        alt_str = "; ".join(
            f"{a['name']} (R$ {float(a['price_brl']):.2f}, estoque: {a['stock_quantity']})"
            for a in alternatives
        )
        lines.append(f"Alternativas disponíveis na mesma categoria: {alt_str}")
    return "\n".join(lines)


def get_active_promotions(campaign_query: Optional[str] = None) -> str:
    """Lista todas as promoções ativas no momento (e verifica se alguma campanha consultada expirou)."""
    with get_db_connection() as conn:
        _register_sqlite_normalizer(conn)
        active_rows = conn.execute(
            """
            SELECT pr.promotion_id, pr.discount_percent, pr.description AS campaign,
                   p.product_id, p.name AS product_name, p.price_brl, p.stock_quantity, p.status
            FROM promotions pr
            JOIN products p ON pr.product_id = p.product_id
            WHERE pr.is_active = 1
            ORDER BY pr.discount_percent DESC
            """
        ).fetchall()
        expired_notice = _check_expired_campaign(conn, campaign_query)
        return _format_promotions_response(active_rows, expired_notice)


def _check_expired_campaign(
    conn: sqlite3.Connection, campaign_query: Optional[str]
) -> Optional[str]:
    if not campaign_query or not campaign_query.strip():
        return None
    norm_camp = normalize_text(campaign_query).strip()
    expired = conn.execute(
        """
        SELECT pr.description, pr.discount_percent, p.name, p.price_brl
        FROM promotions pr
        JOIN products p ON pr.product_id = p.product_id
        WHERE pr.is_active = 0 AND (NORM(pr.description) LIKE ? OR NORM(p.name) LIKE ?)
        """,
        (f"%{norm_camp}%", f"%{norm_camp}%"),
    ).fetchall()
    if not expired:
        return None
    items = ", ".join(
        f"{r['name']} (campanha '{r['description']}' de {r['discount_percent']:.0f}% OFF está EXPIRADA; preço atual: R$ {float(r['price_brl']):.2f})"
        for r in expired
    )
    return f"Atenção — Promoções expiradas/encerradas encontradas para '{campaign_query}': {items}"


def _format_promotions_response(
    active_rows: List[sqlite3.Row], expired_notice: Optional[str]
) -> str:
    lines: List[str] = []
    if expired_notice:
        lines.append(expired_notice)
        lines.append("")
    if not active_rows:
        lines.append("Não há promoções ativas no sistema neste momento.")
        return "\n".join(lines)
    lines.append(f"Promoções ATIVAS no sistema ({len(active_rows)} encontradas):")
    for r in active_rows:
        orig = float(r["price_brl"])
        disc = float(r["discount_percent"])
        final = orig * (1.0 - disc / 100.0)
        lines.append(
            f"- [{r['campaign']}] {r['product_name']} (ID {r['product_id']}): "
            f"De R$ {orig:.2f} por R$ {final:.2f} ({disc:.0f}% de desconto) | "
            f"Estoque: {r['stock_quantity']} un. (Nota: não cumulativo com 5% do PIX)"
        )
    return "\n".join(lines)


def get_order_status(order_id: int, customer_identifier: str) -> str:
    """Consulta o status, rastreio e itens de um pedido mediante confirmação de identidade (e-mail, telefone ou nome)."""
    if not customer_identifier or len(str(customer_identifier).strip()) < 3:
        return (
            "Verificação de segurança necessária (LGPD): Para consultar o status do pedido, "
            "solicite ao cliente o e-mail cadastrado, telefone ou nome completo."
        )
    with get_db_connection() as conn:
        _register_sqlite_normalizer(conn)
        order = conn.execute(
            """
            SELECT o.*, c.name AS customer_name, c.email AS customer_email,
                   c.phone AS customer_phone, c.city AS customer_city
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = ?
            """,
            (int(order_id),),
        ).fetchone()
        if not order:
            return f"Pedido #{order_id} não encontrado no sistema."
        if not _verify_customer_identity(order, str(customer_identifier)):
            return (
                f"Verificação de identidade recusada para o pedido #{order_id}. "
                "O identificador informado não corresponde ao titular do pedido. "
                "Por segurança (LGPD), confirme o e-mail ou telefone exato utilizado na compra."
            )
        items = conn.execute(
            """
            SELECT oi.quantity, p.product_id, p.name, p.price_brl, c.name AS category_name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE oi.order_id = ?
            """,
            (int(order_id),),
        ).fetchall()
        return _format_order_details(order, items)


def _verify_customer_identity(order: sqlite3.Row, identifier: str) -> bool:
    clean_id = identifier.strip().lower()
    if clean_id == str(order["customer_email"]).strip().lower():
        return True
    id_digits = re.sub(r"\D", "", clean_id)
    phone_digits = re.sub(r"\D", "", str(order["customer_phone"]))
    if len(id_digits) >= 8 and (id_digits in phone_digits or phone_digits in id_digits):
        return True
    norm_id = normalize_text(clean_id).strip()
    norm_name = normalize_text(str(order["customer_name"])).strip()
    id_parts = norm_id.split()
    if len(id_parts) >= 2 and all(part in norm_name.split() for part in id_parts):
        return True
    return False


def _format_order_details(order: sqlite3.Row, items: List[sqlite3.Row]) -> str:
    lines = [
        f"=== Detalhes do Pedido #{order['order_id']} ===",
        f"Cliente Titular: {order['customer_name']} ({order['customer_email']} | {order['customer_city']})",
        f"Data do Pedido: {order['order_date']}",
        f"Status Atual: {order['status'].upper()}",
        f"Valor Total: R$ {float(order['total_brl']):.2f} | Forma de Pagamento: {order['payment_method']}",
    ]
    if order["tracking_code"]:
        lines.append(
            f"Código de Rastreamento: {order['tracking_code']} | "
            f"Entrega Estimada/Realizada: {order['estimated_delivery']}"
        )
    else:
        lines.append("Código de Rastreamento: Ainda não disponível (pedido não despachado ou cancelado).")
    if order["notes"]:
        lines.append(f"Observações / Motivo: {order['notes']}")
    lines.append("Itens do Pedido:")
    for item in items:
        lines.append(
            f"  - {item['quantity']}x {item['name']} (ID {item['product_id']} | "
            f"{item['category_name']}) — R$ {float(item['price_brl']):.2f}/un."
        )
    return "\n".join(lines)


def escalate_to_human(
    customer_name: str,
    customer_contact: str,
    reason: str,
    order_id: Optional[int] = None,
) -> str:
    """Registra reclamação ou dúvida complexa e encaminha o atendimento para um especialista humano."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    digest = hashlib.sha256(f"{customer_name}{customer_contact}{reason}".encode("utf-8")).hexdigest()[:4].upper()
    protocol = f"EMP-{timestamp}-{digest}"
    order_ref = f" | Pedido #{order_id}" if order_id else ""
    return (
        f"Atendimento escalado com sucesso para a equipe humana da Empório da Música.\n"
        f"Protocolo de Atendimento: {protocol}{order_ref}\n"
        f"Cliente: {customer_name} ({customer_contact})\n"
        f"Motivo registrado: {reason}\n"
        f"Prazo oficial de retorno: até {SLA_COMPLAINT_HOURS} horas úteis.\n"
        f"Canal direto WhatsApp: {WHATSAPP_SUPPORT_NUMBER} (Seg a Sex 09h às 18h, Sáb 09h às 13h)."
    )


def search_policies(query: str) -> str:
    """Consulta o manual oficial de políticas da Empório da Música (trocas, devoluções, frete, pagamento, garantia, horários e LGPD)."""
    return search_store_policies(query=query)

