import { useState } from "react";
import Nav from "../Nav/nav";
import "./SalesHistoryOption.css";
import Calendar from "react-calendar";
import Modal from "./Modal.jsx";
import { History } from "lucide-react";

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
          <span className="box-title-icon" aria-hidden="true">
            <History></History>
          </span>
          <div className="box-title-text">
            <h2 className="title">Historial de ventas</h2>
            <p className="description">
              Selecciona un día en el calendario para revisar el detalle de cada
              ticket.
            </p>
          </div>
        </div>

        <Calendar
          className="history-calendar"
          onClickDay={handleModal}
          value={new Date()}
        ></Calendar>

        {modalAbierto && (
          <>
            <div className="overlay" onClick={() => setModalAbierto(false)} />
            <Modal
              loading={loading}
              error={error}
              buys={buys}
              onClose={() => setModalAbierto(false)}
            ></Modal>
          </>
        )}
      </div>
    </section>
  );
}

export default SalesHistoryOption;
