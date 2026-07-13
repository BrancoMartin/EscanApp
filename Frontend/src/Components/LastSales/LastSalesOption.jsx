import { useEffect, useState } from "react";
import Nav from "../Nav/nav";
import "./LastSalesOption.css";
import { History, Clock } from "lucide-react";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function LastSalesOption() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(`${BASE_URL}/api/sales/recent`);
        const data = await response.json();
        setHistory(data);
      } catch {
        setError("No se pudo cargar el historial de ventas");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  return (
    <section className="option-panel">
      <Nav />
      <div className="option-form">
        <div className="box-title">
          <span className="box-title-icon" aria-hidden="true">
            <Clock></Clock>
          </span>
          <div className="box-title-text">
            <h2 className="title">Ventas de las últimas 24 hs</h2>
            <p className="description">
              Consulta las ventas cerradas registradas durante las últimas 24
              horas.
            </p>
          </div>
        </div>

        {loading ? (
          <p className="loading-text">Cargando ventas...</p>
        ) : error ? (
          <p className="error-message">{error}</p>
        ) : history.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">
              <Clock></Clock>
            </span>
            <p className="empty-text">
              No hay ventas registradas en las últimas 24 horas.
            </p>
          </div>
        ) : (
          <>
            <div className="stats-row">
              <div className="stat-card">
                <span className="stat-label">Ventas</span>
                <span className="stat-value">{history.length}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Total facturado</span>
                <span className="stat-value">
                  $
                  {history
                    .reduce((acc, s) => acc + Number(s.total_price || 0), 0)
                    .toFixed(2)}
                </span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Ítems vendidos</span>
                <span className="stat-value">
                  {history.reduce((acc, s) => acc + s.items.length, 0)}
                </span>
              </div>
            </div>
            <div className="history-table-wrapper">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Fecha</th>
                    <th>Total</th>
                    <th>Items</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((sale) => (
                    <tr key={sale.id}>
                      <td>{sale.id}</td>
                      <td>{sale.created_at}</td>
                      <td>${sale.total_price}</td>
                      <td>{sale.items.length}</td>
                      <td>
                        <span
                          className={`sale-pill ${
                            sale.state === "closed" ? "closed" : "open"
                          }`}
                        >
                          {sale.state === "closed" ? "Cerrada" : "Abierta"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default LastSalesOption;
