import { useState, useRef, useEffect } from "react";
import "./AgentChat.css";
import { User, Bot } from "lucide-react";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function AgentChat({ onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isBarcode, setIsBarcode] = useState(false);
  const messagesEndRef = useRef(null);
  const keyTimesRef = useRef([]);
  const inputRef = useRef(null);

  const [conversationHistory, setConversationHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("agentChatHistory") || "[]");
    } catch {
      return [];
    }
  });
  const [context, setContext] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("agentChatContext") || "{}");
    } catch {
      return {};
    }
  });
  const [initialized, setInitialized] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    const buildWelcomeMessage = async () => {
      try {
        const catResp = await fetch(`${BASE_URL}/api/categories`);
        const cats = await catResp.json();
        const prodResp = await fetch(`${BASE_URL}/api/products/`);
        const prods = await prodResp.json();

        let examples = [];

        if (prods.length > 0) {
          const randomProd = prods[Math.floor(Math.random() * prods.length)];
          examples.push(`"Aumentame ${randomProd.name} un 30%"`);
        } else {
          examples.push(`"Aumentame un producto un 20%"`);
        }

        if (cats.length > 0) {
          const randomCat = cats[Math.floor(Math.random() * cats.length)];
          const attrResp = await fetch(
            `${BASE_URL}/api/attributes?category_id=${randomCat.id}`,
          );
          const attrs = await attrResp.json();
          if (attrs.length > 0) {
            const randomAttr = attrs[Math.floor(Math.random() * attrs.length)];
            examples.push(
              `"Aumentame los productos de ${randomAttr.name} un 20%"`,
            );
          }
        }

        examples.push(`"Aumentame todos los productos un 15%"`);

        const welcomeText = `¡Hola! Soy tu asistente de precios. Podes pedirme cosas como:\n\n${examples.map((e, i) => `${i + 1}. ${e}`).join("\n")}\n\nTambien podes escanear un codigo de barras y te muestro el producto.\n\n O crear un producto desde acá.`;

        setMessages([{ id: 1, type: "assistant", text: welcomeText }]);
      } catch (error) {
        console.log("ERROR", error);
        setMessages([
          {
            id: 1,
            type: "assistant",
            text: `¡Hola! Soy tu asistente de precios. Podes pedirme cosas como:\n\n1. "Aumentame todos los productos un 15%"\n2. "Aumentame la leche un 30%"\n3. "Cuantos productos tengo?"`,
          },
        ]);
      }
      setInitialized(true);
    };

    if (!initialized) {
      buildWelcomeMessage();
    }
  }, [initialized]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Mantiene el cursor siempre parpadeando en el input: al abrir el chat y
  // cada vez que el asistente termina de responder (cuando loading vuelve a false).
  useEffect(() => {
    if (!loading) {
      const t = setTimeout(() => inputRef.current?.focus(), 0);
      return () => clearTimeout(t);
    }
  }, [loading]);

  const keepFocus = () => {
    if (!loading) setTimeout(() => inputRef.current?.focus(), 0);
  };

  useEffect(() => {
    localStorage.setItem("agentChatContext", JSON.stringify(context));
  }, [context]);

  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!input.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: "user",
      text: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    const sentInput = input;

    setInput("");
    setIsBarcode(false);

    setLoading(true);

    try {
      const conversationForBackend = conversationHistory.map((msg) => ({
        user: msg.user || "",
        assistant: msg.assistant || "",
      }));

      const response = await fetch(`${BASE_URL}/api/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: sentInput,
          conversation_history: conversationForBackend,
          context: context,
        }),
      });
      if (!response.ok) {
        throw new Error("Error en la respuesta del servidor");
      }

      const data = await response.json();

      const assistantMessage = {
        id: Date.now() + 1,
        type: "assistant",
        text: data.message,
        actionExecuted: data.action_executed,
        success: data.success,
        actionData: data.data,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      const newHistory = [
        ...conversationHistory,
        { user: sentInput, assistant: data.message },
      ];
      setConversationHistory(newHistory);
      localStorage.setItem("agentChatHistory", JSON.stringify(newHistory));

      if (data.data && data.data.context) {
        setContext(data.data.context);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "assistant",
          text: "Disculpa, ocurrio un error al procesar tu mensaje. Intenta nuevamente.",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    keyTimesRef.current.push(Date.now());
    if (keyTimesRef.current.length > 30) keyTimesRef.current.shift();

    if (e.key === "Enter" && /^\d{6,}$/.test(input)) {
      const times = keyTimesRef.current;
      if (times.length >= 6) {
        const diffs = [];
        for (let i = 1; i < times.length; i++) {
          diffs.push(times[i] - times[i - 1]);
        }
        const avg = diffs.reduce((a, b) => a + b, 0) / diffs.length;
        if (avg < 60) {
          setIsBarcode(true);
          setTimeout(() => setIsBarcode(false), 2500);
        }
      }
      keyTimesRef.current = [];
    }
  };

  const handleChange = (e) => {
    const val = e.target.value;
    setInput(val);
    if (/^\d{6,}$/.test(val)) {
      keyTimesRef.current.push(Date.now());
      if (keyTimesRef.current.length > 30) keyTimesRef.current.shift();
    } else {
      setIsBarcode(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 1,
        type: "assistant",
        text: "¡Hola! ¿En que puedo ayudarte con los precios?",
      },
    ]);
    setConversationHistory([]);
    setContext({});
    localStorage.removeItem("agentChatHistory");
    localStorage.removeItem("agentChatContext");
  };

  return (
    <aside className="agent-chat-panel">
      <div className="chat-header">
        <h3>Asistente de Precios</h3>
        <div className="header-actions">
          <button
            className="clear-btn"
            onClick={handleClearChat}
            title="Limpiar chat"
          >
            🗑️
          </button>
          <button className="close-btn" onClick={onClose} title="Cerrar chat">
            ✕
          </button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message ${msg.type} ${msg.error ? "error" : ""}`}
          >
            <div className="message-content">
              {msg.type === "assistant" && <span className="avatar">🤖</span>}
              <div className="message-text">{msg.text}</div>
              {msg.type === "user" && (
                <span className="avatar">
                  <User></User>
                </span>
              )}
            </div>
            {msg.actionExecuted && (
              <div className="action-badge">
                {msg.success ? "✅" : "⚠️"} {msg.actionExecuted}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message assistant loading">
            <div className="message-content">
              <span className="avatar avatar-thinking">
                <Bot></Bot>
              </span>
              <div className="thinking-bubble">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="thinking-text">Pensando</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={input}
            autoFocus
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onBlur={keepFocus}
            placeholder="Escribe o escanea un codigo de barras..."
            disabled={loading}
            className={`chat-input ${isBarcode ? "barcode-scanner" : ""}`}
          />
          {isBarcode && (
            <span className="barcode-badge">📷 Barcode detectado</span>
          )}
        </div>
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="send-btn"
        >
          {loading ? (
            <span className="btn-spinner" aria-label="Enviando" />
          ) : (
            "Enviar"
          )}
        </button>
      </form>
    </aside>
  );
}

export default AgentChat;
