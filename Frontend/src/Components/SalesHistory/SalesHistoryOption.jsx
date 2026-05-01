import { useEffect, useState } from "react";
import axios from "axios";
import Nav from "../Nav/nav";
import "./SalesHistoryOption.css";

function SalesHistoryOption() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get("http://localhost:8000/api/sales/");
        console.log("HISTORIAL DE VENTAS: ", response.data);
        setHistory(response.data);
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
      <div className="box-title">
        <h2 className="title">Historial de ventas</h2>
        <p className="description">
          Consulta las ventas ya cerradas y revisa el detalle de cada ticket.
        </p>
      </div>

      {loading ? (
        <p>Cargando ventas...</p>
      ) : error ? (
        <p className="error-message">{error}</p>
      ) : history.length === 0 ? (
        <p>No hay ventas registradas aún.</p>
      ) : (
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
              {history?.map((sale) => (
                <tr key={sale.id}>
                  <td>{sale.id}</td>
                  <td>{sale.date}</td>
                  <td>{sale.total}</td>
                  <td>{sale.items_count}</td>
                  <td>{sale.state}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default SalesHistoryOption;
