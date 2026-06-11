import json
import os
import re
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

from .schemas import ChatResponse, Product

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_LLM_PROVIDER = "LOCAL"
PRODUCT_KEYWORDS = [
    "produto",
    "produtos",
    "estoque",
    "quantidade",
    "preco",
    "preço",
    "descricao",
    "descrição",
    "loja",
    "cor",
    "cores",
    "tamanho",
    "categoria",
    "material",
    "sku",
]
OUT_OF_CONTEXT_MESSAGE = (
    "Desculpe, posso responder apenas sobre os produtos cadastrados no banco de dados da loja. "
    "Por favor, faca uma pergunta sobre produtos, estoque, quantidade, preco, cor ou tamanho."
)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def _format_product(product: Product) -> str:
    return (
        f"{product.name}: {product.description}. "
        f"Categoria: {product.category}. Cor: {product.color}. Tamanho: {product.size}. "
        f"Material: {product.material}. SKU: {product.sku}. "
        f"Quantidade em estoque: {product.quantity}. Preco: R${product.price:.2f}."
    )


def _question_refers_to_products(question: str) -> bool:
    text = question.lower()
    return any(keyword in text for keyword in PRODUCT_KEYWORDS)


def _find_matching_product(question: str, products: Iterable[Product]) -> Product | None:
    text = question.lower()
    for product in products:
        if product.name.lower() in text:
            return product
    return None


def _build_answer(question: str, products: list[Product]) -> ChatResponse:
    question_text = question.strip()
    product = _find_matching_product(question_text, products)
    lower = question_text.lower()

    if product is not None:
        return ChatResponse(answer=_format_product(product), source="local-stub", out_of_context=False)

    if "quantidade" in lower or "estoque" in lower:
        lines = [f"{item.name}: {item.quantity}" for item in products]
        answer = "Quantidade disponivel por produto: " + "; ".join(lines)
        return ChatResponse(answer=answer, source="local-stub", out_of_context=False)

    if "preco" in lower or "preço" in lower or "valor" in lower:
        lines = [f"{item.name}: R${item.price:.2f}" for item in products]
        answer = "Preco dos produtos cadastrados: " + "; ".join(lines)
        return ChatResponse(answer=answer, source="local-stub", out_of_context=False)

    if "cor" in lower or "cores" in lower:
        lines = [f"{item.name}: {item.color}" for item in products]
        answer = "Cores dos produtos cadastrados: " + "; ".join(lines)
        return ChatResponse(answer=answer, source="local-stub", out_of_context=False)

    if "tamanho" in lower:
        lines = [f"{item.name}: {item.size}" for item in products]
        answer = "Tamanhos dos produtos cadastrados: " + "; ".join(lines)
        return ChatResponse(answer=answer, source="local-stub", out_of_context=False)

    if "categoria" in lower:
        lines = [f"{item.name}: {item.category}" for item in products]
        answer = "Categorias dos produtos cadastrados: " + "; ".join(lines)
        return ChatResponse(answer=answer, source="local-stub", out_of_context=False)

    if "material" in lower:
        lines = [f"{item.name}: {item.material}" for item in products]
        answer = "Materiais dos produtos cadastrados: " + "; ".join(lines)
        return ChatResponse(answer=answer, source="local-stub", out_of_context=False)

    if "sku" in lower:
        lines = [f"{item.name}: {item.sku}" for item in products]
        answer = "SKUs dos produtos cadastrados: " + "; ".join(lines)
        return ChatResponse(answer=answer, source="local-stub", out_of_context=False)

    if "lista" in lower or "produtos" in lower or "o que" in lower:
        lines = [item.name for item in products]
        answer = "Produtos disponiveis: " + ", ".join(lines)
        return ChatResponse(answer=answer, source="local-stub", out_of_context=False)

    if not _question_refers_to_products(question_text):
        return ChatResponse(answer=OUT_OF_CONTEXT_MESSAGE, source="local-stub", out_of_context=True)

    answer = (
        "Nao encontrei exatamente esse produto no banco de dados. "
        "Pergunte novamente usando o nome do produto ou peca informacoes de estoque, preco, cor ou tamanho."
    )
    return ChatResponse(answer=answer, source="local-stub", out_of_context=False)


def _build_gemini_prompt(question: str, products: list[Product]) -> str:
    product_list = "\n".join(
        (
            f"- Nome: {product.name}\n"
            f"  Descricao: {product.description}\n"
            f"  Categoria: {product.category}\n"
            f"  Cor: {product.color}\n"
            f"  Tamanho: {product.size}\n"
            f"  Material: {product.material}\n"
            f"  SKU: {product.sku}\n"
            f"  Quantidade: {product.quantity}\n"
            f"  Preco: R${product.price:.2f}"
        )
        for product in products
    )

    return (
        "Voce e um chatbot de uma loja. Responda apenas usando o contexto dos produtos abaixo, "
        "como em um RAG simples: a pergunta do usuario deve ser comparada com os dados do banco. "
        "Nao use conhecimento externo e nao invente produtos, precos, quantidades ou atributos.\n\n"
        "Se a pergunta nao for sobre produtos, estoque, quantidade, preco, descricao, cor, tamanho, "
        "categoria, material ou SKU da loja, retorne out_of_context como true e explique educadamente "
        "que so responde sobre produtos.\n\n"
        "Responda sempre em JSON valido, sem markdown, neste formato:\n"
        '{"answer": "texto para o usuario", "out_of_context": false, "source": "gemini"}\n\n'
        f"Produtos do banco:\n{product_list}\n\n"
        f"Pergunta do usuario: {question}"
    )


def _parse_json_response(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", text, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None


def _extract_response_text(response: object) -> str:
    text = getattr(response, "text", "")
    if text:
        return str(text).strip()
    return str(response).strip()


def _generate_with_gemini(question: str, products: list[Product]) -> ChatResponse:
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "O provedor Gemini requer o pacote google-generativeai. "
            "Instale com: pip install google-generativeai"
        ) from exc

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY nao configurada. Crie uma chave no Google AI Studio e defina "
            "GEMINI_API_KEY no arquivo .env."
        )

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(_build_gemini_prompt(question, products))
        raw_text = _extract_response_text(response)

        parsed = _parse_json_response(raw_text)
        if parsed is not None and "answer" in parsed:
            return ChatResponse(
                answer=str(parsed["answer"]),
                source=str(parsed.get("source", "gemini")),
                out_of_context=bool(parsed.get("out_of_context", False)),
                details=parsed.get("details"),
            )

        return ChatResponse(answer=raw_text, source="gemini", out_of_context=False)
    except Exception as exc:
        error_message = str(exc)
        if "429" in error_message or "quota" in error_message.lower():
            fallback = _build_answer(question, products)
            fallback.source = "local-fallback"
            fallback.details = {
                "reason": "Gemini quota exceeded",
                "provider_error": error_message,
            }
            return fallback

        raise RuntimeError(f"Erro ao chamar Google AI Studio Gemini: {error_message}") from exc


def generate_answer(question: str, products: list[Product]) -> ChatResponse:
    provider = os.environ.get("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().upper()
    if provider == "GEMINI":
        return _generate_with_gemini(question, products)
    return _build_answer(question, products)
