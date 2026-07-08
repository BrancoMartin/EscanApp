import { useNavigate } from "react-router-dom";
import { useState } from "react";
import "./start.css";
import AgentChat from "../Components/AgentChat/AgentChat";

function Start() {
  const [showAgent, setShowAgent] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="start-page">
      <header className="start-header">
        <h1>EscanApp</h1>
        <p>
          Gestioná tu comercio: cargá productos, escaneá ventas y ajustá precios
          con ayuda del asistente IA.
        </p>
      </header>

      <div className="start-actions">
        <button onClick={() => navigate("/add-product")}>
          <span className="button-icon" aria-hidden="true">
            📦
          </span>
          <span className="button-start">Agregar Producto</span>
        </button>
        <button onClick={() => navigate("/sales-history")}>
          <span className="button-icon" aria-hidden="true">
            📊
          </span>
          <span className="button-start">Historial de Ventas</span>
        </button>
        <button onClick={() => navigate("/scan-products")}>
          <span className="button-icon" aria-hidden="true">
            📷
          </span>
          <span className="button-start">Escanear Productos</span>
        </button>
      </div>

      <div className="agent-button-container">
        {!showAgent && (
          <button
            className="agent-button"
            onClick={() => setShowAgent(!showAgent)}
            title="Hablá con nuestro agente para ajustar precios"
          >
            <span className="agent-icon">🤖</span>
          </button>
        )}

        {!showAgent && (
          <div className="agent-tooltip">
            AJUSTA LOS PRECIOS DE TUS PRODUCTOS. Hablando con este agente ia
          </div>
        )}
      </div>

      {showAgent && <AgentChat onClose={() => setShowAgent(false)} />}
    </div>
  );
}

export default Start;
