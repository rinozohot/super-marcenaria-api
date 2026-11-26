from decimal import Decimal
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models import StatusPedidoJIT, FormaPagamento

# --- MARCENARIA ---
class MarcenariaCreate(BaseModel):
    nome_fantasia: str
    cnpj: str
    cidade: str = "Alto Paraná"
    cep: str
    alvara_funcionamento: str

class MarcenariaResponse(MarcenariaCreate):
    id: UUID
    ativa: bool

    class Config:
        from_attributes = True

# --- PRODUTO ---
class ProdutoCreate(BaseModel):
    marcenaria_id: UUID
    nome: str
    descricao: Optional[str] = None
    material_base: str
    materiais_opcionais: List[str] = []
    medida_min_cm: Decimal = Field(..., gt=0)
    medida_max_cm: Decimal = Field(..., gt=0)
    preco_base: Decimal = Field(..., ge=0)
    prazo_entrega_dias: int = Field(..., gt=0)

class ProdutoResponse(ProdutoCreate):
    id: UUID
    curtidas: int

    class Config:
        from_attributes = True

# --- PEDIDO E CHECKOUT ---
class AdicionarItemRequest(BaseModel):
    usuario_id: UUID
    produto_id: UUID
    altura_cm: Decimal
    largura_cm: Decimal
    profundidade_cm: Decimal
    material_escolhido: str
    adicional_material: Decimal = Decimal("0.00")
    quantidade: int = Field(default=1, gt=0)

class CheckoutRequest(BaseModel):
    forma_pagamento: FormaPagamento
    cidade_destino: str = "Alto Paraná"

class AtualizarStatusJITRequest(BaseModel):
    novo_status: StatusPedidoJIT