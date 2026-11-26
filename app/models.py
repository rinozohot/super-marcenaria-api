import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean,
    DateTime, Date, ForeignKey, Enum, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class PerfilUsuario(str, enum.Enum):
    CLIENTE = "CLIENTE"
    MARCENEIRO = "MARCENEIRO"

class EstadoClube(str, enum.Enum):
    ATIVA = "ATIVA"
    CANCELADA = "CANCELADA"
    PENDENTE = "PENDENTE"

class StatusPedidoJIT(str, enum.Enum):
    CARRINHO = "CARRINHO"
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    PAGO = "PAGO"
    EM_FABRICACAO = "EM_FABRICACAO"
    EM_ROTA = "EM_ROTA"
    ENTREGUE = "ENTREGUE"

class FormaPagamento(str, enum.Enum):
    PIX = "PIX"
    CARTAO = "CARTAO"

class StatusPagamento(str, enum.Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"

class CanalNotificacao(str, enum.Enum):
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"

class Marcenaria(Base):
    __tablename__ = "marcenarias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_fantasia = Column(String(150), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    cidade = Column(String(100), nullable=False, default="Alto Paraná")
    cep = Column(String(9), nullable=False)
    alvara_funcionamento = Column(String(100), nullable=False)
    ativa = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    produtos = relationship("Produto", back_populates="marcenaria")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marcenaria_id = Column(UUID(as_uuid=True), ForeignKey("marcenarias.id"), nullable=True)
    nome = Column(String(150), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=False)
    endereco = Column(Text, nullable=False)
    perfil = Column(Enum(PerfilUsuario, name="perfil_usuario"), default=PerfilUsuario.CLIENTE)
    criado_em = Column(DateTime, default=datetime.utcnow)

    assinatura = relationship("AssinaturaClube", back_populates="usuario", uselist=False)

class AssinaturaClube(Base):
    __tablename__ = "assinaturas_clube"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False)
    tipo_plano = Column(String(50), default="MENSAL_PRO")
    valor_mensal = Column(Numeric(10, 2), nullable=False)
    percentual_desconto = Column(Numeric(5, 2), default=10.00)
    estado = Column(Enum(EstadoClube, name="estado_clube"), default=EstadoClube.PENDENTE)
    data_renovacao = Column(Date, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="assinatura")

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marcenaria_id = Column(UUID(as_uuid=True), ForeignKey("marcenarias.id"), nullable=False)
    nome = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=True)
    material_base = Column(String(100), nullable=False)
    materiais_opcionais = Column(JSONB, default=list)
    medida_min_cm = Column(Numeric(8, 2), nullable=False)
    medida_max_cm = Column(Numeric(8, 2), nullable=False)
    preco_base = Column(Numeric(10, 2), nullable=False)
    prazo_entrega_dias = Column(Integer, nullable=False)
    curtidas = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)

    marcenaria = relationship("Marcenaria", back_populates="produtos")

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    marcenaria_id = Column(UUID(as_uuid=True), ForeignKey("marcenarias.id"), nullable=False)
    status_jit = Column(Enum(StatusPedidoJIT, name="status_pedido_jit"), default=StatusPedidoJIT.CARRINHO)
    valor_frete = Column(Numeric(10, 2), default=0.00)
    valor_desconto = Column(Numeric(10, 2), default=0.00)
    valor_total = Column(Numeric(10, 2), default=0.00)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    itens = relationship("ItemPedido", back_populates="pedido")

class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(UUID(as_uuid=True), ForeignKey("produtos.id"), nullable=False)
    altura_cm = Column(Numeric(8, 2), nullable=False)
    largura_cm = Column(Numeric(8, 2), nullable=False)
    profundidade_cm = Column(Numeric(8, 2), nullable=False)
    material_escolhido = Column(String(100), nullable=False)
    quantidade = Column(Integer, default=1)
    preco_unitario_calculado = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("Pedido", back_populates="itens")

class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), unique=True, nullable=False)
    gateway_tx_id = Column(String(150), unique=True)
    forma = Column(Enum(FormaPagamento, name="forma_pagamento"), nullable=False)
    status = Column(Enum(StatusPagamento, name="status_pagamento"), default=StatusPagamento.PENDENTE)
    qr_code_copia_cola = Column(Text, nullable=True)
    pago_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False)
    canal = Column(Enum(CanalNotificacao, name="canal_notificacao"), default=CanalNotificacao.WHATSAPP)
    destinatario = Column(String(100), nullable=False)
    mensagem = Column(Text, nullable=False)
    enviada = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)