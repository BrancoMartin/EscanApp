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

  const handleScan = async (event) => {
    event.preventDefault();
    setError("");
    setSale(null);
    setLoading(true);

    try {
      const response = await axios.get(
        `/api/products/barcode/${encodeURIComponent(barcode)}`, // el encodeURIComponent codifica los caracteres especiales para transformarlos y que puedan estar en la url
      );
      setSale(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo escanear el producto");
    } finally {
      setLoading(false);
    }
  };

  const HandleCloseSale = async () => {
    try {
      const response = await axios.post(`/api/sales/${sale.id}/close`);
      console.log("RESPUESTA CERRAR VENTA", response.data);
      setMessage(response.data);
    } catch (err) {
      setMessage(err.response?.data?.detail || "No se pudo cerrar la venta");
    }
  };

  const getSaleDetails = async (saleId) => {
    try {
      const response = await axios.get(`/api/sales/${saleId}`);
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
      const response = await axios.put(`/api/sales/${sale.id}/items/${itemId}`);
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

      <form onSubmit={HandleCloseSale} className="option-form">
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
            onKeyDown={(e) => e.key === "Enter" && handleScan(e)} // aca tengo que poner un evento que me traiga a ese product y que me agregue al tocket el producto escaneado
          />
        </label>
        <button
          className="button"
          type="submit"
          disabled={loading || !barcode.trim()}
        >
          {loading ? "Creando venta..." : "Crear venta"}
        </button>
      </form>
      {error && <p className="error-message">{error}</p>}
      {sale && (
        <div className="sale-preview">
          <h3>Venta pendiente</h3>
          <p>Estado: {sale.state}</p>
          <p>Total: {sale.total}</p>
          <p>Items: {sale.items_count}</p>
          <div className="sale-items">
            {sale.items?.map((item) => (
              <div key={item.id} className="sale-item">
                <strong>{item.product}</strong>
                <span>Cantidad: {item.quantity}</span>
                <span>Precio unitario: {item.unit_price}</span>
                <span>Subtotal: {item.subtotal}</span>
                <button onClick={() => handleCancelProduct(item.id)}>
                  Cancelar producto
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      {message && <p className="success-message">{message}</p>}
      {messageCancel && <p className="success-message">{messageCancel}</p>}
    </section>
  );
}

export default ScanProductsOption;
