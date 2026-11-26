from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Marcenaria, Produto
from app.schemas import MarcenariaCreate, MarcenariaResponse, ProdutoCreate, ProdutoResponse

router = APIRouter(prefix="/catalogo", tags=["Catálogo e Marcenarias"])

@router.post("/marcenarias", response_model=MarcenariaResponse, status_code=201)
def cadastrar_marcenaria(dados: MarcenariaCreate, db: Session = Depends(get_db)):
    nova = Marcenaria(**dados.model_dump())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

@router.post("/produtos", response_model=ProdutoResponse, status_code=201)
def cadastrar_produto(dados: ProdutoCreate, db: Session = Depends(get_db)):
    if dados.medida_max_cm < dados.medida_min_cm:
        raise HTTPException(status_code=400, detail="medida_max_cm deve ser maior ou igual a medida_min_cm.")
    
    marcenaria = db.query(Marcenaria).filter(Marcenaria.id == dados.marcenaria_id).first()
    if not marcenaria:
        raise HTTPException(status_code=404, detail="Marcenaria não encontrada.")

    novo_produto = Produto(**dados.model_dump())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto

@router.get("/produtos", response_model=List[ProdutoResponse])
def listar_produtos(
    material: Optional[str] = None,
    marcenaria_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Produto)
    if material:
        query = query.filter(Produto.material_base.ilike(f"%{material}%"))
    if marcenaria_id:
        query = query.filter(Produto.marcenaria_id == marcenaria_id)
    return query.all()

@router.post("/produtos/{produto_id}/curtir")
def curtir_produto(produto_id: UUID, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    produto.curtidas += 1
    db.commit()
    return {"produto_id": produto.id, "curtidas": produto.curtidas}