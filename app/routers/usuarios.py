import os
from uuid import UUID
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

from app.database import get_db
from app.models import Usuario, AssinaturaClube, EstadoClube
from app.schemas import UsuarioCreate, UsuarioResponse, LoginRequest, AssinarClubeRequest

router = APIRouter(prefix="/usuarios", tags=["Usuários e Clube S-Marc"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "chave_padrao_dev")
ALGORITHM = "HS256"

@router.post("/cadastro", response_model=UsuarioResponse, status_code=201)
def cadastrar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter((Usuario.email == dados.email) | (Usuario.cpf == dados.cpf)).first():
        raise HTTPException(status_code=400, detail="E-mail ou CPF já cadastrado.")

    novo = Usuario(
        nome=dados.nome,
        cpf=dados.cpf,
        email=dados.email,
        senha_hash=pwd_context.hash(dados.senha),
        telefone=dados.telefone,
        endereco=dados.endereco
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.post("/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not usuario or not pwd_context.verify(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")

    expira = datetime.utcnow() + timedelta(hours=12)
    token = jwt.encode({"sub": str(usuario.id), "exp": expira}, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario_id": usuario.id,
        "nome": usuario.nome
    }

@router.post("/{usuario_id}/assinar-clube")
def assinar_clube_smarc(usuario_id: UUID, dados: AssinarClubeRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    assinatura = db.query(AssinaturaClube).filter(AssinaturaClube.usuario_id == usuario_id).first()
    renovacao = date.today() + timedelta(days=30)

    if assinatura:
        assinatura.estado = EstadoClube.ATIVA
        assinatura.tipo_plano = dados.tipo_plano
        assinatura.valor_mensal = dados.valor_mensal
        assinatura.data_renovacao = renovacao
    else:
        assinatura = AssinaturaClube(
            usuario_id=usuario_id,
            tipo_plano=dados.tipo_plano,
            valor_mensal=dados.valor_mensal,
            percentual_desconto=10.00,
            estado=EstadoClube.ATIVA,
            data_renovacao=renovacao
        )
        db.add(assinatura)

    db.commit()
    return {
        "mensagem": "Assinatura Clube S-Marc ATIVA! Desconto automático de 10% habilitado no carrinho.",
        "usuario_id": usuario_id,
        "data_renovacao": renovacao
    }

@router.post("/{usuario_id}/cancelar-clube")
def cancelar_clube_smarc(usuario_id: UUID, db: Session = Depends(get_db)):
    assinatura = db.query(AssinaturaClube).filter(AssinaturaClube.usuario_id == usuario_id).first()
    if not assinatura or assinatura.estado != EstadoClube.ATIVA:
        raise HTTPException(status_code=400, detail="Usuário não possui assinatura ativa.")

    assinatura.estado = EstadoClube.CANCELADA
    db.commit()
    return {"mensagem": "Assinatura do Clube S-Marc cancelada."}
