# 🪚 Super-Marcenaria (S-Marc) API — V1

API RESTful desenvolvida em **Python** e **FastAPI** para conectar clientes finais a marcenarias locais sob o modelo de **produção Just-in-Time (JIT)**, com precificação paramétrica dinâmica e clube de assinaturas recorrentes (**Clube S-Marc**).

---

## 🚀 Principais Funcionalidades (V1)

* **Catálogo Paramétrico:** Cadastro de marcenarias e móveis sob medida com faixas dimensionais (`medida_min_cm` a `medida_max_cm`) e materiais opcionais armazenados em `JSONB`.
* **Motor de Precificação Dinâmica:** Cálculo proporcional automático baseado nas dimensões escolhidas pelo cliente, somado a adicionais de acabamento.
* **Autenticação & Clube S-Marc:** Cadastro e login com hash de senha (`bcrypt`) e tokens **JWT (HS256)**, além de gestão de assinatura mensal que aplica **10% de desconto automático** nos pedidos.
* **Fluxo de Pedidos & Checkout:** Criação de carrinho com cálculo consolidado de itens, descontos e geração de transação de pagamento.
* **Integração via Webhooks (JIT):** Endpoint dedicado para confirmação de pagamento que libera o pedido automaticamente para a fila de fabricação da marcenaria.

---

## 🛠️ Stack Tecnológica

* **Linguagem:** Python 3.12
* **Framework Web:** FastAPI + Uvicorn
* **ORM & Banco de Dados:** SQLAlchemy 2.0 + PostgreSQL 19 (`psycopg`)
* **Validação de Dados:** Pydantic v2
* **Segurança:** JWT (`python-jose`) + `passlib[bcrypt]`

---

## 📂 Arquitetura do Projeto

```text
super-marcenaria-api/
├── app/
│   ├── routers/          # Rotas modulares (catálogo, usuários, pedidos, webhooks)
│   ├── services/         # Regras de negócio (motor de precificação paramétrica)
│   ├── database.py       # Conexão SQLAlchemy e injeção de sessão (yield db)
│   ├── main.py           # Inicialização da API e registro de roteadores
│   ├── models.py         # Modelos relacionais (9 tabelas + ENUMs)
│   └── schemas.py        # Contratos de entrada e saída (Pydantic)
├── sql/
│   └── init.sql          # Script DDL completo do banco PostgreSQL
├── .env.example          # Modelo de variáveis de ambiente
├── requirements.txt      # Dependências congeladas do projeto
└── README.md             # Documentação oficial