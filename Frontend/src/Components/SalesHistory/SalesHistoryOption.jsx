import { useState } from "react";
import Nav from "../Nav/nav";
import "./SalesHistoryOption.css";
import Calendar from "react-calendar";
import Modal from "./Modal.jsx";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function SalesHistoryOption() {
  const [buys, setBuys] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalAbierto, setModalAbierto] = useState(false);

  async function handleModal(date) {
    console.log("FECHA SELECCIONADA: ", date);

    const dateParceada = date.toISOString().replace("T", " ").replace("Z", " ");

    console.log("FECHA PARSEADA: ", dateParceada);

    try {
      const response = await fetch(
        `${BASE_URL}/api/sales/date/${dateParceada}`,
      );
      const data = await response.json();

      console.log("RESPUESTA DE LA API: ", data);

      setLoading(false);

      setBuys(data);
      setModalAbierto(true);
    } catch (err) {
      setError("Error al cargar las ventas.", err);
    }
  }

  return (
    <section className="option-panel">
      <Nav />
      <div className="option-form">
        <div className="box-title">
          <h2 className="title">Historial de ventas</h2>
          <p className="description">
            Consulta las ventas ya cerradas y revisa el detalle de cada ticket.
          </p>
        </div>

        <Calendar
          className="history-calendar"
          onClickDay={handleModal}
          value={new Date()}
        ></Calendar>

        {modalAbierto && (
          <>
            <div className="overlay" onClick={() => setModalAbierto(false)} />
            <Modal loading={loading} error={error} buys={buys}></Modal>
          </>
        )}
      </div>
    </section>
  );
}

export default SalesHistoryOption;
