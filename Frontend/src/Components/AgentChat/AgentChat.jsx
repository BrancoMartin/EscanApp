import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./AgentChat.css";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function AgentChat({ onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  console.log(input);

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
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); // esto hace que cada vez que haya un mensaje nuevo baje hasta donde esta este
  };

  useEffect(() => {
    const buildWelcomeMessage = async () => {
      try {
        const catResp = await axios.get(`${BASE_URL}/api/categories`);
        const cats = catResp.data || [];
        const prodResp = await axios.get(`${BASE_URL}/api/products/`);
        const prods = prodResp.data || [];

        let examples = [];

        if (prods.length > 0) {
          const randomProd = prods[Math.floor(Math.random() * prods.length)];
          examples.push(`"Aumentame ${randomProd.name} un 30%"`);
        } else {
          examples.push(`"Aumentame un producto un 20%"`);
        }

        if (cats.length > 0) {
          const randomCat = cats[Math.floor(Math.random() * cats.length)];
          const attrResp = await axios.get(
            `${BASE_URL}/api/attributes?category_id=${randomCat.id}`,
          );
          const attrs = attrResp.data || [];
          if (attrs.length > 0) {
            const randomAttr = attrs[Math.floor(Math.random() * attrs.length)];
            examples.push(`"Aumentame los de ${randomAttr.name} un 20%"`);
          }
        }

        examples.push(`"Aumentame todos los productos un 15%"`);

        const welcomeText = `¡Hola! Soy tu asistente de precios. Podes pedirme cosas como:\n\n${examples.map((e, i) => `${i + 1}. ${e}`).join("\n")}`;

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

    console.log("sent input", sentInput);
    console.log("input", input);
    setLoading(true);

    try {
      const conversationForBackend = conversationHistory.map((msg) => ({
        user: msg.user || "",
        assistant: msg.assistant || "",
      }));

      console.log("mensaje: ", sentInput);

      const response = await axios.post(
        `${BASE_URL}/api/agent/chat`,
        {
          message: sentInput,
          conversation_history: conversationForBackend,
          context: context,
        },
        {
          headers: { "Content-Type": "application/json" },
          timeout: 120000,
        },
      );

      const data = response.data;

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
        console.log("CONTEXTO: ", data.data.context);

        // ME PARECE QUE ACA PODRIA AGREGARSE data.data.context DIRECTAMENTE AL STORAGE DEL CONTEXTO
        // EN VEZ DE METERLO PRIMERO AL STATE DE CONTEXT Y LUEGO EJECUTAR EL USEEFECT

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
              {msg.type === "user" && <span className="avatar">👤</span>}
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
              <span className="avatar">🤖</span>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe tu mensaje aqui..."
          disabled={loading}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="send-btn"
        >
          {loading ? "..." : "Enviar"}
        </button>
      </form>
    </aside>
  );
}

export default AgentChat;
