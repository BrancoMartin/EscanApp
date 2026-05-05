import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import "./start.css";

function Start() {
  const [showAgent, setShowAgent] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="start-page">
      <header className="start-header">
        <h1>EscanApp</h1>
      </header>

      <div className="start-actions">
        <button onClick={() => navigate("/add-product")}>
          <p className="button-start">Agregar Producto</p>
        </button>
        <button onClick={() => navigate("/sales-history")}>
          <p className="button-start">Historial de Ventas</p>
        </button>
        <button onClick={() => navigate("/scan-products")}>
          <p className="button-start">Escanear Productos</p>
        </button>
      </div>
    </div>
  );
}

export default Start;
