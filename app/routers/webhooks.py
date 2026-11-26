from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Pedido, Pagamento, Notificacao, Marcenaria,
    StatusPedidoJIT, StatusPagamento, CanalNotificacao
)

router = APIRouter(prefix="/webhooks", tags=["Webhooks e Automação"])

class WebhookPagamentoPayload(BaseModel):
    gateway_tx_id: str
    status: str  # "approved"

@router.post("/pagamento")
def webhook_confirmacao_pagamento(payload: WebhookPagamentoPayload, db: Session = Depends(get_db)):
    pagamento = db.query(Pagamento).filter(
        Pagamento.gateway_tx_id == payload.gateway_tx_id
    ).first()

    if not pagamento:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")

    if payload.status == "approved" and pagamento.status != StatusPagamento.APROVADO:
        pagamento.status = StatusPagamento.APROVADO
        pagamento.pago_em = datetime.utcnow()

        pedido = db.query(Pedido).filter(Pedido.id == pagamento.pedido_id).first()
        pedido.status_jit = StatusPedidoJIT.PAGO

        marcenaria = db.query(Marcenaria).filter(Marcenaria.id == pedido.marcenaria_id).first()

        # RF09: Registra notificação automática para a marcenaria iniciar o corte JIT
        notificacao = Notificacao(
            pedido_id=pedido.id,
            canal=CanalNotificacao.WHATSAPP,
            destinatario=marcenaria.nome_fantasia if marcenaria else "Marcenaria",
            mensagem=f"NOVO PEDIDO PAGO ({pagamento.gateway_tx_id})! Valor: R$ {pedido.valor_total}. Liberado para produção JIT.",
            enviada=True
        )
        db.add(notificacao)
        db.commit()

        return {
            "mensagem": "Pagamento aprovado via Webhook. Pedido liberado para produção e marcenaria notificada.",
            "pedido_id": pedido.id,
            "status_jit": pedido.status_jit
        }

    return {"mensagem": "Evento ignorado ou já processado."}