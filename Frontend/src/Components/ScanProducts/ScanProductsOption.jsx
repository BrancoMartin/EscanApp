import { useState, useEffect } from "react";
import axios from "axios";
import Nav from "../Nav/nav";
import "./ScanProductsOption.css";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function ScanProductsOption() {
  const [barcode, setBarcode] = useState("");
  const [sale, setSale] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageCancel, setMessageCancel] = useState("");

  useEffect(() => {
    const loadPending = async () => {
      try {
        const response = await axios.get(`${BASE_URL}/api/sales/pending`);
        if (response.data) setSale(response.data);
      } catch (err) {
        console.error("Error al cargar venta pendiente:", err);
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
        `${BASE_URL}/api/products/barcode/${encodeURIComponent(barcode)}`,
      );

      console.log("RESPUESTA ESCANEAR PRODUCTO", response.data);

      setSale(response.data);

      console.log("TOTAL PRICE", sale.total_price);
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo escanear el producto");
    } finally {
      setLoading(false);
    }
  };

  const HandleCloseSale = async () => {
    try {
      const response = await axios.post(
        `${BASE_URL}/api/sales/${sale.id}/close`,
      );
      console.log("RESPUESTA CERRAR VENTA", response.data);
      setMessage("Venta cerrada exitosamente");
      setSale(false);
    } catch (err) {
      setMessage(err.response?.data?.detail || "No se pudo cerrar la venta");
    }
  };

  const getSaleDetails = async (saleId) => {
    if (!saleId) return;
    try {
      const response = await axios.get(`${BASE_URL}/api/sales/${saleId}`);
      setSale(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo cargar la venta");
    }
  };

  const handleCancelSale = async () => {
    console.log("CANCELANDO VENTA COMPLETA: ", sale.id);

    const response = await axios.delete(`${BASE_URL}/api/sales/${sale.id}`);
    setSale(false);
    setBarcode("");

    console.log("RESPUESTA CANCELAR VENTA", response.data);
  };

  const handleCancelProduct = async (item) => {
    console.log("ID DEL ITEM SALE", item.);
    console.log("SALE ID", sale.id);
    console.log("SALE", sale);
    if (sale.items.length === 1 && sale.items[0].quantity === 1) {
      handleCancelSale();
    } else {
      console.log("CANCELANDO ITEM VENTA: ", item.product_id);
      try {
        const response = await axios.put(
          `${BASE_URL}/api/sales/${sale.id}/items/${item.product_id}`,
        );
        getSaleDetails(sale.id); // Actualiza los detalles de la venta después de cancelar el producto
        console.log("RESPUESTA CANCELAR PRODUCTO", response.data.message);
        setMessageCancel(response.data.message);
      } catch (err) {
        setMessageCancel(
          err.response?.data?.detail || "No se pudo cancelar el producto",
        );
      }
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
            <h2>TICKET</h2>
            <h4>Total: ${sale.total_price}</h4>
            <div className="sale-items">
              {sale.items?.map((item) => (
                <div key={item.id} className="sale-item">
                  <strong>{item.product_name}</strong>
                  <span>Cantidad: {item.quantity}</span>
                  <span>Precio unitario: ${item.unit_price}</span>
                  <span>Subtotal: ${item.subtotal}</span>
                  <button
                    className="button-cancel"
                    onClick={() => handleCancelProduct(item)}
                  >
                    Cancelar producto
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="box-button">
            <button className="button" onClick={HandleCloseSale}>
              Cerrar venta
            </button>
            <button className="button-cancel" onClick={handleCancelSale}>
              Cancelar venta completa
            </button>
          </div>
        </>
      )}
      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}
      {messageCancel && <p className="success-message">{messageCancel}</p>}
    </section>
  );
}

export default ScanProductsOption;
