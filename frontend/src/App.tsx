import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type ChatResponse = {
  answer: string;
  source: string;
  out_of_context: boolean;
  details?: Record<string, unknown> | null;
};

type Product = {
  id: number;
  name: string;
  description: string;
  quantity: number;
  price: number;
  category: string;
  color: string;
  size: string;
  material: string;
  sku: string;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: string;
  outOfContext?: boolean;
};

const API_BASE_URL = "http://localhost:8000";

const SUGGESTIONS = [
  "Quais produtos estao cadastrados?",
  "Qual a quantidade de Camiseta?",
  "Quais cores estao disponiveis?",
  "Qual o tamanho do Tenis?",
  "Qual o preco da Mochila?",
  "Qual a capital da Franca?",
];

function currency(value: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Ola. Pergunte sobre produtos, precos, descricoes ou quantidades em estoque.",
      source: "frontend",
    },
  ]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [productsLoading, setProductsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const totalStock = useMemo(
    () => products.reduce((total, product) => total + product.quantity, 0),
    [products],
  );

  useEffect(() => {
    async function loadProducts() {
      try {
        const response = await fetch(`${API_BASE_URL}/products`);
        if (!response.ok) {
          throw new Error(`Erro ${response.status}`);
        }

        const data = (await response.json()) as Product[];
        setProducts(data);
        setApiOnline(true);
      } catch {
        setApiOnline(false);
        setError("Nao foi possivel carregar os produtos. Verifique se o backend esta rodando.");
      } finally {
        setProductsLoading(false);
      }
    }

    loadProducts();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendQuestion(text: string) {
    const trimmedQuestion = text.trim();
    if (!trimmedQuestion || loading) {
      return;
    }

    const userMessage: Message = {
      id: `${Date.now()}-user`,
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setError(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmedQuestion }),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        throw new Error(errorBody?.detail ?? `Erro ${response.status}`);
      }

      const data = (await response.json()) as ChatResponse;
      const assistantMessage: Message = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: data.answer,
        source: data.source,
        outOfContext: data.out_of_context,
      };

      setApiOnline(true);
      setMessages((current) => [...current, assistantMessage]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro inesperado";
      setApiOnline(false);
      setError(`Nao foi possivel obter resposta do backend. ${message}`);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    sendQuestion(question);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Produtos cadastrados">
        <div className="brand">
          <div className="brand-mark">P</div>
          <div>
            <h1>Pixaflow</h1>
            <p>Chatbot de produtos</p>
          </div>
        </div>

        <div className={`status ${apiOnline ? "online" : apiOnline === false ? "offline" : ""}`}>
          <span className="status-dot" />
          {apiOnline ? "Backend conectado" : apiOnline === false ? "Backend indisponivel" : "Conectando"}
        </div>

        <section className="panel">
          <div className="panel-header">
            <h2>Produtos</h2>
            <span>{products.length}</span>
          </div>

          {productsLoading ? (
            <p className="muted">Carregando produtos...</p>
          ) : (
            <div className="product-list">
              {products.map((product) => (
                <button
                  className="product-item"
                  key={product.id}
                  type="button"
                  onClick={() => sendQuestion(`Me fale sobre ${product.name}`)}
                >
                  <span>
                    <strong>{product.name}</strong>
                    <small>{product.category} • {product.color} • Tam. {product.size}</small>
                    <small>{product.material}</small>
                  </span>
                  <span className="product-side">
                    <strong>{currency(product.price)}</strong>
                    <small>{product.quantity} un.</small>
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="stats">
          <div>
            <span>{totalStock}</span>
            <small>itens em estoque</small>
          </div>
          <div>
            <span>Gemini</span>
            <small>Google AI Studio</small>
          </div>
        </section>
      </aside>

      <main className="chat-area">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Consulta ao banco da loja</p>
            <h2>Assistente de estoque e produtos</h2>
          </div>
        </header>

        <section className="suggestions" aria-label="Perguntas sugeridas">
          {SUGGESTIONS.map((suggestion) => (
            <button key={suggestion} type="button" onClick={() => sendQuestion(suggestion)} disabled={loading}>
              {suggestion}
            </button>
          ))}
        </section>

        <section className="messages" aria-live="polite">
          {messages.map((message) => (
            <article className={`message ${message.role}`} key={message.id}>
              <div className="message-meta">
                <strong>{message.role === "user" ? "Voce" : "Chatbot"}</strong>
                {message.source ? <span>{message.source}</span> : null}
              </div>
              <p>{message.content}</p>
              {message.outOfContext ? <div className="warning">Pergunta fora de contexto</div> : null}
            </article>
          ))}

          {loading ? (
            <article className="message assistant loading-message">
              <div className="message-meta">
                <strong>Chatbot</strong>
              </div>
              <p>Consultando produtos no banco...</p>
            </article>
          ) : null}

          <div ref={messagesEndRef} />
        </section>

        {error ? <div className="error-box">{error}</div> : null}

        <form className="chat-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={question}
            placeholder="Pergunte sobre quantidade, preco ou descricao"
            onChange={(event) => setQuestion(event.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !question.trim()} aria-label="Enviar pergunta">
            <span>Enviar</span>
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;
