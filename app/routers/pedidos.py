import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Produto, Pedido, ItemPedido, Pagamento, Usuario,
    EstadoClube, StatusPedidoJIT, StatusPagamento
)
from app.schemas import AdicionarItemRequest, CheckoutRequest, AtualizarStatusJITRequest
from app.services.precificacao import calcular_preco_parametrico

router = APIRouter(prefix="/pedidos", tags=["Carrinho, Checkout e Produção JIT"])

@router.post("/carrinho/adicionar")
def adicionar_ao_carrinho(dados: AdicionarItemRequest, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == dados.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    usuario = db.query(Usuario).filter(Usuario.id == dados.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    is_assinante = (
        usuario.assinatura is not None and
        usuario.assinatura.estado == EstadoClube.ATIVA
    )

    preco_unitario = calcular_preco_parametrico(
        preco_base=produto.preco_base,
        medida_min=produto.medida_min_cm,
        medida_max=produto.medida_max_cm,
        largura_escolhida=dados.largura_cm,
        adicional_material=dados.adicional_material,
        is_assinante_clube=is_assinante
    )

    # Busca carrinho aberto para a mesma marcenaria ou cria um novo
    pedido = db.query(Pedido).filter(
        Pedido.usuario_id == usuario.id,
        Pedido.marcenaria_id == produto.marcenaria_id,
        Pedido.status_jit == StatusPedidoJIT.CARRINHO
    ).first()

    if not pedido:
        pedido = Pedido(
            usuario_id=usuario.id,
            marcenaria_id=produto.marcenaria_id,
            status_jit=StatusPedidoJIT.CARRINHO
        )
        db.add(pedido)
        db.flush()

    item = ItemPedido(
        pedido_id=pedido.id,
        produto_id=produto.id,
        altura_cm=dados.altura_cm,
        largura_cm=dados.largura_cm,
        profundidade_cm=dados.profundidade_cm,
        material_escolhido=dados.material_escolhido,
        quantidade=dados.quantidade,
        preco_unitario_calculado=preco_unitario
    )
    db.add(item)

    pedido.valor_total = Decimal(pedido.valor_total or 0) + (preco_unitario * dados.quantidade)
    db.commit()
    db.refresh(pedido)

    return {
        "pedido_id": pedido.id,
        "desconto_clube_aplicado": is_assinante,
        "preco_unitario_calculado": preco_unitario,
        "valor_total_carrinho": pedido.valor_total
    }

@router.post("/{pedido_id}/checkout")
def finalizar_checkout(pedido_id: uuid.UUID, dados: CheckoutRequest, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido or pedido.status_jit != StatusPedidoJIT.CARRINHO:
        raise HTTPException(status_code=400, detail="Carrinho inválido ou já finalizado.")

    # Regra de frete regional (RN07)
    frete = Decimal("50.00") if dados.cidade_destino.lower() == "alto paraná" else Decimal("120.00")
    pedido.valor_frete = frete
    pedido.valor_total = Decimal(pedido.valor_total) + frete
    pedido.status_jit = StatusPedidoJIT.AGUARDANDO_PAGAMENTO

    tx_id = f"SMARC-{uuid.uuid4().hex[:10].upper()}"
    pagamento = Pagamento(
        pedido_id=pedido.id,
        gateway_tx_id=tx_id,
        forma=dados.forma_pagamento,
        status=StatusPagamento.PENDENTE,
        qr_code_copia_cola=f"00020126580014BR.GOV.BCB.PIX0136{tx_id}520400005303986"
    )
    db.add(pagamento)
    db.commit()

    return {
        "pedido_id": pedido.id,
        "status_jit": pedido.status_jit,
        "valor_frete": pedido.valor_frete,
        "valor_total": pedido.valor_total,
        "gateway_tx_id": tx_id,
        "qr_code_copia_cola": pagamento.qr_code_copia_cola
    }

@router.patch("/{pedido_id}/status-jit")
def avancar_status_producao(pedido_id: uuid.UUID, dados: AtualizarStatusJITRequest, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    # RN02: Bloqueia entrada na fábrica se não estiver pago
    if pedido.status_jit in [StatusPedidoJIT.CARRINHO, StatusPedidoJIT.AGUARDANDO_PAGAMENTO]:
        raise HTTPException(
            status_code=403,
            detail="Regra RN02: O pedido precisa ter o pagamento aprovado antes de entrar em produção."
        )

    pedido.status_jit = dados.novo_status
    db.commit()
    return {"pedido_id": pedido.id, "novo_status_jit": pedido.status_jit}