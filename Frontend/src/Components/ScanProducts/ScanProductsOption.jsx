import { useState, useEffect, useRef } from "react";
import Nav from "../Nav/nav";
import "./ScanProductsOption.css";
import { ScanLine } from "lucide-react";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function ScanProductsOption() {
  const [barcode, setBarcode] = useState("");
  const [sale, setSale] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageCancel, setMessageCancel] = useState("");

  const inputRef = useRef(null);
  const debounceRef = useRef(null);
  // Detecta si el código lo está ingresando el lector (tecleo muy rápido) o
  // una persona a mano. Empieza en true y se vuelve false apenas hay una pausa
  // larga entre teclas, típica del ingreso manual.
  const isScannerInputRef = useRef(true);
  const lastKeyTimeRef = useRef(0);
  // Intervalo máximo (ms) entre caracteres para considerarlo lector de barras.
  const SCANNER_MAX_INTERVAL = 50;

  // Mantiene el cursor siempre parpadeando en la barra de escaneo.
  const focusInput = () => {
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  useEffect(() => {
    focusInput();
    const loadPending = async () => {
      try {
        const response = await fetch(`${BASE_URL}/api/sales/pending`);
        const data = await response.json();
        if (data) setSale(data);
      } catch (err) {
        console.error("Error al cargar venta pendiente:", err);
      }
    };
    loadPending();
  }, []);

  // Auto-escaneo SOLO para el lector de barras: cuando termina de "tipear" el
  // código, se dispara handleScan solo. Si el código se escribió a mano, no se
  // envía automáticamente; el usuario debe apretar el botón o Enter.
  useEffect(() => {
    if (!barcode.trim()) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (isScannerInputRef.current) {
        triggerScan(barcode);
      }
    }, 120);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [barcode]);

  // Mide el tiempo entre teclas para distinguir el lector (rápido) del tecleo
  // manual (lento). Con una sola pausa larga se marca como ingreso manual.
  const handleBarcodeChange = (e) => {
    const value = e.target.value;
    const now = Date.now();

    if (value === "") {
      // Reinicio: nuevo código, se asume lector hasta que se demuestre lo contrario.
      isScannerInputRef.current = true;
    } else if (value.length === 1) {
      // Primer carácter: todavía no hay intervalo para medir.
      isScannerInputRef.current = true;
    } else if (now - lastKeyTimeRef.current > SCANNER_MAX_INTERVAL) {
      isScannerInputRef.current = false;
    }

    lastKeyTimeRef.current = now;
    setBarcode(value);
  };

  const triggerScan = (rawCode) => {
    const code = (rawCode ?? "").trim();
    if (!code || loading) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    isScannerInputRef.current = true;
    setBarcode("");
    handleScan(code);
  };

  const handleScan = async (code) => {
    setError("");
    setMessage("");
    setSale(null);
    setLoading(true);

    try {
      const response = await fetch(
        `${BASE_URL}/api/products/barcode/${encodeURIComponent(code)}`,
      );
      const data = await response.json();
      if (!response.ok) {
        throw { response: { data } };
      }

      setSale(data);
    } catch (err) {
      setError(
        err?.response?.data?.detail || "No se pudo escanear el producto",
      );
    } finally {
      setLoading(false);
      focusInput();
    }
  };

  const HandleCloseSale = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/sales/${sale.id}/close`, {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        throw { response: { data } };
      }
      console.log("RESPUESTA CERRAR VENTA", data);
      setMessage("Venta cerrada exitosamente");
      setSale(false);
    } catch (err) {
      setMessage(err?.response?.data?.detail || "No se pudo cerrar la venta");
    }
  };

  const getSaleDetails = async (saleId) => {
    if (!saleId) return;
    try {
      const response = await fetch(`${BASE_URL}/api/sales/${saleId}`);
      const data = await response.json();
      if (!response.ok) {
        throw { response: { data } };
      }
      setSale(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "No se pudo cargar la venta");
    }
  };

  const handleCancelSale = async () => {
    console.log("CANCELANDO VENTA COMPLETA: ", sale.id);

    const response = await fetch(`${BASE_URL}/api/sales/${sale.id}`, {
      method: "DELETE",
    });
    const data = await response.json();
    setSale(false);
    setBarcode("");

    console.log("RESPUESTA CANCELAR VENTA", data);
  };

  const handleCancelProduct = async (item) => {
    console.log("ITEM", item);
    console.log("ID DEL ITEM SALE", item.id);
    console.log("SALE ID", sale.id);
    console.log("SALE", sale);
    if (sale.items.length === 1 && sale.items[0].quantity === 1) {
      handleCancelSale();
    } else {
      console.log("CANCELANDO ITEM VENTA: ", item.id);
      try {
        const response = await fetch(
          `${BASE_URL}/api/sales/${sale.id}/items/${item.id}`,
          { method: "PUT" },
        );
        const data = await response.json();
        if (!response.ok) {
          throw { response: { data } };
        }
        getSaleDetails(sale.id);
        console.log("RESPUESTA CANCELAR PRODUCTO", data.message);
        setMessageCancel(data.message);
      } catch (err) {
        setMessageCancel(
          err?.response?.data?.detail || "No se pudo cancelar el producto",
        );
      }
    }
  };

  return (
    <section className="option-panel">
      <Nav />

      <form className="option-form">
        <div className="box-title">
          <span className="box-title-icon" aria-hidden="true">
            <ScanLine></ScanLine>
          </span>
          <div className="box-title-text">
            <h2 className="title">Escanear productos</h2>
            <p className="description">
              Ingresa un código de barras para agregar el producto a la venta
              pendiente.
            </p>
          </div>
        </div>

        <div className="scan-row">
          <label className="label-add-product scan-input">
            Código de barras
            <input
              ref={inputRef}
              type="text"
              value={barcode}
              autoFocus
              onChange={handleBarcodeChange}
              onBlur={focusInput}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  triggerScan(barcode);
                }
              }}
              placeholder="Escaneá o escribí el código de barras..."
            />
          </label>
          <button
            className="button scan-button"
            type="button"
            onClick={() => triggerScan(barcode)}
            disabled={loading || !barcode.trim()}
          >
            {loading ? "Escaneando..." : "Escanear"}
          </button>
        </div>
        {error && <p className="error-message">{error}</p>}
      </form>

      {sale && sale.items && (
        <div className="ticket">
          <div className="ticket-head">
            <span className="ticket-badge">🧾</span>
            <h2 className="ticket-title">Ticket de venta</h2>
            <p className="ticket-sub">Venta pendiente #{sale.id}</p>
          </div>

          <div className="ticket-items">
            {sale.items?.map((item) => (
              <div key={item.id} className="ticket-item">
                <div className="ticket-item-main">
                  <strong className="ticket-item-name">
                    {item.product_name}
                  </strong>
                  <span className="ticket-item-meta">
                    {item.quantity} × ${item.unit_price}
                  </span>
                </div>
                <div className="ticket-item-right">
                  <span className="ticket-item-subtotal">${item.subtotal}</span>
                  <button
                    className="ticket-remove"
                    title="Quitar una unidad"
                    onClick={() => handleCancelProduct(item)}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="ticket-total">
            <span>Total</span>
            <span className="ticket-total-value">${sale.total_price}</span>
          </div>

          <div className="ticket-actions">
            <button className="button ticket-close" onClick={HandleCloseSale}>
              Cerrar venta
            </button>
            <button className="button-cancel" onClick={handleCancelSale}>
              Cancelar venta completa
            </button>
          </div>
        </div>
      )}

      {message && <p className="success-message scan-msg">{message}</p>}
      {messageCancel && (
        <p className="success-message scan-msg">{messageCancel}</p>
      )}
    </section>
  );
}

export default ScanProductsOption;
