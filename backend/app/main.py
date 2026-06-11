import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db, get_all_products
from .llm import generate_answer
from .schemas import ChatRequest, ChatResponse, Product

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / "backend" / ".env")


def _resolve_db_file(db_file: str) -> str:
    path = Path(db_file)
    if path.is_absolute():
        return str(path)
    return str(BASE_DIR / path)


DEFAULT_DB_FILE = _resolve_db_file(os.environ.get("PRODUCT_DB_FILE", "products.db"))


def create_app(product_db_file: Optional[str] = None) -> FastAPI:
    app = FastAPI(
        title="Pixaflow Produtos Chatbot",
        version="0.1.0",
        description="API de consulta de produtos da loja com sinalização de perguntas fora de contexto.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db_file = product_db_file or DEFAULT_DB_FILE
    app.state.db_file = db_file
    init_db(app.state.db_file)

    @app.on_event("startup")
    async def startup_event() -> None:
        init_db(app.state.db_file)

    @app.get("/", summary="Saudação")
    def root() -> dict:
        return {"message": "Pixaflow Chatbot de Produtos está no ar."}

    @app.get("/products", response_model=list[Product], summary="Lista produtos")
    def list_products() -> list[Product]:
        products = get_all_products(app.state.db_file)
        return [Product(**dict(item)) for item in products]

    @app.post("/chat", response_model=ChatResponse, summary="Perguntar ao chatbot")
    def chat(request: ChatRequest) -> ChatResponse:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=422, detail="A pergunta não pode estar vazia.")

        products = [Product(**dict(item)) for item in get_all_products(app.state.db_file)]
        try:
            return generate_answer(question, products)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

    return app


# Factory for uvicorn
def get_app() -> FastAPI:
    return create_app()


# Default app instance for direct uvicorn import (main.py:app)
try:
    app = create_app()
except Exception:
    # If DB creation fails, create minimal app
    app = FastAPI(title="Pixaflow Produtos Chatbot", version="0.1.0")
