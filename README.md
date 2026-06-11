# Pixaflow Chatbot de Produtos

Projeto de teste tecnico para consulta de produtos da loja com backend em FastAPI, LLM Gemini via Google AI Studio e frontend em React + TypeScript.

## Estrutura

- `backend/` - API Python FastAPI
- `frontend/` - aplicacao React + TypeScript
- `.github/workflows/python-tests.yml` - CI para testes de backend

## Backend

### Requisitos

- Python 3.14+
- `pip`

### Instalacao

PowerShell:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Git Bash:

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
```

Depois de criar o `backend/.env`, edite o arquivo e preencha `GEMINI_API_KEY` com sua chave do Google AI Studio. Para rodar sem consumir a API do Gemini, use `LLM_PROVIDER=LOCAL`.

### Executando

PowerShell:

```bash
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Git Bash:

```bash
cd backend
source .venv/Scripts/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estara disponivel em `http://localhost:8000`.

### Endpoints

- `GET /` - verifica se o servico esta ativo
- `GET /products` - lista produtos do banco
- `POST /chat` - envia uma pergunta ao chatbot

Exemplo de payload:

```json
{
  "question": "Qual a quantidade de Camiseta?"
}
```

### Comportamento

- O backend busca os produtos no banco SQLite e envia esses dados como contexto para a LLM.
- O Gemini responde somente sobre produtos, estoque, quantidade, preco, descricao, cor, tamanho, categoria, material e SKU.
- Perguntas fora do contexto retornam `out_of_context: true`.
- O modo `LOCAL` existe para desenvolvimento rapido e para os testes automatizados.

## Configuracao da LLM

### Modo LOCAL

Funciona sem credenciais:

```env
LLM_PROVIDER=LOCAL
PRODUCT_DB_FILE=backend/products.db
```

### Modo GEMINI com Google AI Studio

1. Acesse o Google AI Studio e crie uma API key.
2. Copie `backend/.env.example` para `backend/.env`.
3. Configure `backend/.env`:

```env
LLM_PROVIDER=GEMINI
GEMINI_API_KEY=sua-chave-do-google-ai-studio
GEMINI_MODEL=gemini-flash-latest
PRODUCT_DB_FILE=backend/products.db
```

Nao e necessario instalar SDKs de nuvem, configurar projeto externo ou autenticar com linha de comando.

## Frontend

### Instalacao

```bash
cd frontend
npm install
```

### Executando

```bash
cd frontend
npm run dev
```

O frontend sera servido em `http://localhost:5173`.

## Testes

No backend:

```bash
cd backend
python -m pytest
```

## GitHub Actions

O workflow `.github/workflows/python-tests.yml` executa `pytest` no backend.
