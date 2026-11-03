import re
from datetime import date
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator
import json

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Category(BaseModel):
    category_id: int = Field(..., description="ID único da categoria")
    name: str = Field(..., min_length=1, description="Nome da categoria")
    description: str = Field(..., description="Descrição da categoria")


class Customer(BaseModel):
    customer_id: int = Field(..., description="ID único do cliente")
    name: str = Field(..., min_length=2, description="Nome completo do cliente")
    phone: str = Field(..., description="Telefone com DDD")
    email: str = Field(..., description="E-mail de contato do cliente")
    city: str = Field(..., description="Cidade do cliente")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean_email = value.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError(f"Formato de e-mail inválido: {value}")
        return clean_email


class Product(BaseModel):
    product_id: int = Field(..., description="ID único do produto")
    price_brl: float = Field(..., gt=0, description="Preço em reais (R$)")
    name: str = Field(..., min_length=2, description="Nome do instrumento")
    category_id: int = Field(..., description="ID da categoria associada")
    description: str = Field(..., description="Descrição detalhada do instrumento")
    stock_quantity: int = Field(..., ge=0, description="Quantidade em estoque")
    status: str = Field(..., description="Status do produto: active, inactive, etc.")
    specs: Union[Dict[str, Any], str] = Field(default_factory=dict, description="Especificações técnicas")
    created_at: date = Field(..., description="Data de cadastro do produto")

    @field_validator("specs", mode="before")
    @classmethod
    def parse_specs(cls, value: Any) -> Dict[str, Any]:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return {"raw": value}
        if isinstance(value, dict):
            return value
        return {}


class Order(BaseModel):
    order_id: int = Field(..., description="ID único do pedido")
    customer_id: int = Field(..., description="ID do cliente solicitante")
    order_date: date = Field(..., description="Data de criação do pedido")
    status: str = Field(..., description="Status: pending, confirmed, shipped, delivered, cancelled")
    total_brl: float = Field(..., ge=0, description="Valor total do pedido em R$")
    payment_method: str = Field(..., description="Forma de pagamento (pix, boleto, credit_Nx)")
    tracking_code: Optional[str] = Field(None, description="Código de rastreamento (PAC, SEDEX, Jadlog)")
    estimated_delivery: Optional[date] = Field(None, description="Previsão de entrega")
    notes: Optional[str] = Field(None, description="Observações ou motivo de cancelamento")


class OrderItem(BaseModel):
    order_id: int = Field(..., description="ID do pedido")
    quantity: int = Field(..., ge=1, description="Quantidade do produto")
    product_id: int = Field(..., description="ID do produto comprado")


class Promotion(BaseModel):
    promotion_id: int = Field(..., description="ID da promoção")
    product_id: int = Field(..., description="ID do produto contemplado")
    discount_percent: float = Field(..., ge=0, le=100, description="Percentual de desconto")
    description: str = Field(..., description="Campanha ou descrição da promoção")
    is_active: bool = Field(..., description="Se a promoção está atualmente em vigor")

    @field_validator("is_active", mode="before")
    @classmethod
    def parse_is_active(cls, value: Any) -> bool:
        if isinstance(value, (int, float)):
            return bool(int(value))
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "sim", "yes", "active")
        return bool(value)
