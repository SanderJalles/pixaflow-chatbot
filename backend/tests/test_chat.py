import os
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def test_chat_returns_product_stock(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "LOCAL")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "products_test.db")
        with TestClient(create_app(product_db_file=db_file)) as client:
            response = client.post("/chat", json={"question": "Qual a quantidade de Camiseta?"})

            assert response.status_code == 200
            data = response.json()
            assert data["out_of_context"] is False
            assert "Camiseta" in data["answer"]


def test_chat_detects_out_of_context_question(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "LOCAL")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "products_test.db")
        with TestClient(create_app(product_db_file=db_file)) as client:
            response = client.post("/chat", json={"question": "Qual a capital da França?"})

        assert response.status_code == 200
        data = response.json()
        assert data["out_of_context"] is True
        assert "desculpe" in data["answer"].lower()


def test_chat_handles_greeting(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "LOCAL")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "products_test.db")
        with TestClient(create_app(product_db_file=db_file)) as client:
            response = client.post("/chat", json={"question": "oi"})

        assert response.status_code == 200
        data = response.json()
        assert data["out_of_context"] is False
        assert "produtos" in data["answer"].lower()


def test_chat_returns_product_variants(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "LOCAL")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "products_test.db")
        with TestClient(create_app(product_db_file=db_file)) as client:
            response = client.post("/chat", json={"question": "Quais tamanhos de Tenis tem?"})

        assert response.status_code == 200
        data = response.json()
        assert data["out_of_context"] is False
        assert "38" in data["answer"]
        assert "40" in data["answer"]
        assert "42" in data["answer"]
