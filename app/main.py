from fastapi import FastAPI
from app.routers import produtos, pedidos, webhooks

app = FastAPI(
    title="Super-Marcenaria (S-Marc) API",
    description="Plataforma de catálogo paramétrico, Clube S-Marc e produção Just-in-Time para marcenarias.",
    version="1.0.0"
)

app.include_router(produtos.router)
app.include_router(pedidos.router)
app.include_router(webhooks.router)

@app.get("/", tags=["Status"])
def root():
    return {
        "projeto": "Super-Marcenaria (S-Marc)",
        "status": "operacional",
        "documentacao": "/docs"
    }