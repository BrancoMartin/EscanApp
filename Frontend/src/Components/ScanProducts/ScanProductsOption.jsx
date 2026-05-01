import { useState } from "react";
import axios from "axios";
import Nav from "../Nav/nav";
import "./ScanProductsOption.css";

function ScanProductsOption() {
  const [barcode, setBarcode] = useState("");
  const [sale, setSale] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageCancel, setMessageCancel] = useState("");

  useEffect(() => {
    const loadPending = async () => {
      try {
        const response = await axios.get(
          "http://localhost:8000/api/sales/pending",
        );
        if (response.data) setSale(response.data);
      } catch (err) {
        console.log("No pending sale");
      }
    };
    loadPending();
  }, []);

  const handleScan = async (event) => {
    console.log("HANDLE SCAN EJECUTANDOSE: event: ", event);
    setError("");
    setSale(null);
    setLoading(true);

    console.log("HANDLE SCAN EJECUTANDOSE: barcode: ", barcode);

    try {
      const response = await axios.get(
        `http://localhost:8000/api/products/barcode/${encodeURIComponent(barcode)}`,
      );

      console.log("RESPUESTA ESCANEAR PRODUCTO", response.data);

      setSale(response.data.sale);
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo escanear el producto");
    } finally {
      setLoading(false);
    }
  };

  const HandleCloseSale = async () => {
    try {
      const response = await axios.post(
        `http://localhost:8000/api/sales/${sale.id}/close`,
      );
      console.log("RESPUESTA CERRAR VENTA", response.data);
      setMessage(response.data);
      setSale(null); // Clear the sale after closing
    } catch (err) {
      setMessage(err.response?.data?.detail || "No se pudo cerrar la venta");
    }
  };

  const getSaleDetails = async (saleId) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/sales/${saleId}`,
      );
      setSale(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo cargar la venta");
    }
  };

  const handleCancelProduct = async (itemId) => {
    console.log(
      `Intentando cancelar item con ID: ${itemId} de la venta ID: ${sale.id}`,
    );
    try {
      const response = await axios.put(
        `http://localhost:8000/api/sales/${sale.id}/items/${itemId}`,
      );
      getSaleDetails(sale.id); // Actualiza los detalles de la venta después de cancelar el producto
      console.log("RESPUESTA CANCELAR PRODUCTO", response.data.message);
      setMessageCancel(response.data.message);
    } catch (err) {
      setMessageCancel(
        err.response?.data?.detail || "No se pudo cancelar el producto",
      );
    }
  };

  return (
    <section className="option-panel">
      <Nav />

      <form className="option-form">
        <div className="box-title">
          <h2 className="title">Escanear productos</h2>
          <p className="description">
            Ingresa un código de barras para agregar el producto a la venta
            pendiente.
          </p>
        </div>

        <label className="label-add-product">
          Código de barras
          <input
            type="text"
            value={barcode}
            onChange={(e) => setBarcode(e.target.value)}
            placeholder="Ej. 1234567890123"
            onKeyDown={(e) => e.key === "Enter" && handleScan(e)}
          />
        </label>
        <button
          className="button"
          type="button"
          onClick={handleScan}
          disabled={loading || !barcode.trim()}
        >
          {loading ? "Escaneando..." : "Escanear producto"}
        </button>
      </form>
      {sale && (
        <>
          <div className="sale-preview">
            <h3>Venta pendiente</h3>
            <p>Estado: {sale.state}</p>
            <p>Total: ${sale.total_price}</p>
            <div className="sale-items">
              {sale.items?.map((item) => (
                <div key={item.id} className="sale-item">
                  <strong>{item.product_name}</strong>
                  <span>Cantidad: {item.quantity}</span>
                  <span>Precio unitario: ${item.unit_price}</span>
                  <span>Subtotal: ${item.subtotal}</span>
                  <button onClick={() => handleCancelProduct(item.id)}>
                    Cancelar producto
                  </button>
                </div>
              ))}
            </div>
          </div>
          <button className="button" onClick={HandleCloseSale}>
            Cerrar venta
          </button>
        </>
      )}
      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}
      {messageCancel && <p className="success-message">{messageCancel}</p>}
    </section>
  );
}

export default ScanProductsOption;
