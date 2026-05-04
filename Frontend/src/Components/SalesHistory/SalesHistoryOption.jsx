import { useEffect, useState } from "react";
import axios from "axios";
import Nav from "../Nav/nav";
import "./SalesHistoryOption.css";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function SalesHistoryOption() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [buys, setBuys] = useState([]);

  const parsearFecha = (fechaString) => {
    // "04/05/2026 01:18"
    const [fecha, hora] = fechaString.split(" ");
    const [dia, mes, año] = fecha.split("/");
    const [horas, minutos] = hora.split(":");
    return new Date(año, mes - 1, dia, horas, minutos);
  };

  useEffect(() => {
    const fetchHistory = async () => {
      const response = await axios.get(`${BASE_URL}/api/sales/`);

      console.log("RESPUESTA DE LA API: ", response.data.created_at);

      const fechaHoy = new Date();

      const ventasRecientes = response.data.filter((sale) => {
        console.log("Fecha hoy: ", fechaHoy);

        const fechaVenta = parsearFecha(sale.created_at);

        console.log("Fecha venta: ", fechaVenta);

        console.log("FECHA DE LA VENTA: ", fechaVenta);
        console.log("FECHA DE HOY: ", fechaHoy);

        const diferenciaHoras = (fechaHoy - fechaVenta) / (1000 * 60 * 60);

        console.log("HORAS DE DIFERENCIA: ", diferenciaHoras);

        return diferenciaHoras <= 24;
      });

      setBuys(ventasRecientes);
      setLoading(false);

      setHistory(response.data);
    };

    fetchHistory();
  }, []);

  console.log("HISTORIAL DE VENTAS: ", buys);

  return (
    <section className="option-panel">
      <Nav />
      <div className="box-title">
        <h2 className="title">Historial de ventas de hoy</h2>
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
                <th>Productos</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {buys.map((sale) => (
                <tr key={sale.id}>
                  <td>{sale.id}</td>
                  <td>{sale.created_at}</td>
                  <td>{sale.total_price}</td>
                  <td>
                    {sale.items.map((item) => (
                      <p>
                        {item.product_name} - {item.quantity}
                      </p>
                    ))}
                  </td>
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
