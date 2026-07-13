import "./Modal.css";

function Modal({ loading, error, buys, onClose }) {
  const total = Array.isArray(buys)
    ? buys.reduce((acc, sale) => acc + Number(sale.total_price || 0), 0)
    : 0;

  return (
    <div className="modal" role="dialog" aria-modal="true">
      <div className="modal-header">
        <div className="modal-header-text">
          <h3 className="modal-title">Ventas del día</h3>
          {!loading && Array.isArray(buys) && buys.length > 0 && (
            <span className="modal-subtitle">
              {buys.length} {buys.length === 1 ? "venta" : "ventas"} · Total $
              {total.toFixed(2)}
            </span>
          )}
        </div>
        <button
          className="modal-close"
          onClick={onClose}
          aria-label="Cerrar"
          title="Cerrar"
        >
          ✕
        </button>
      </div>

      <div className="modal-body">
        {loading ? (
          <p className="modal-state">Cargando ventas...</p>
        ) : error ? (
          <p className="modal-state modal-state-error">{error}</p>
        ) : !buys || buys.length === 0 ? (
          <div className="modal-empty">
            <span className="modal-empty-icon">🗓️</span>
            <p>No hay ventas registradas este día.</p>
          </div>
        ) : (
          <table className="table-modal">
            <thead>
              <tr>
                <th className="headers">ID</th>
                <th className="headers">Hora</th>
                <th className="headers">Total</th>
                <th className="headers">Productos</th>
                <th className="headers">Estado</th>
              </tr>
            </thead>
            <tbody>
              {buys.map((sale) => (
                <tr key={sale.id}>
                  <td className="data data-id">#{sale.id}</td>
                  <td className="data">{sale.created_at}</td>
                  <td className="data data-total">${sale.total_price}</td>
                  <td className="data">
                    {sale.items.map((item, i) => (
                      <span key={i} className="product-chip">
                        {item.product_name} ×{item.quantity}
                      </span>
                    ))}
                  </td>
                  <td className="data">
                    <span
                      className={`state-pill ${
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
        )}
      </div>
    </div>
  );
}

export default Modal;
