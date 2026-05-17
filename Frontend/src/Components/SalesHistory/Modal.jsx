import React, { useEffect, useState } from "react";
import axios from "axios";
import "./Modal.css";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function Modal({ loading, error, buys }) {
  console.log("LOADING: ", loading);
  console.log("ERROR: ", error);
  console.log("BUYS: ", buys);

  console.log("Tipo de buys:", typeof buys, Array.isArray(buys));

  return (
    <div className="modal">
      {loading ? (
        <p>Cargando ventas...</p>
      ) : buys.length === 0 ? (
        <p>No hay ventas registradas aún.</p>
      ) : (
        <table className="table-modal">
          <thead>
            <tr>
              <th className="headers">ID</th>
              <th className="headers">Fecha</th>
              <th className="headers">Total</th>
              <th className="headers">Productos</th>
              <th className="headers">Estado</th>
            </tr>
          </thead>
          <tbody>
            {buys.length == 0 && (
              <tr>
                <td className="no-data" colSpan="5">
                  No hay ventas registradas aún.
                </td>
              </tr>
            )}
            {buys.length != 0 &&
              buys.map((sale) => (
                <tr key={sale.id}>
                  <td className="data">{sale.id}</td>
                  <td className="data">{sale.created_at}</td>
                  <td className="data">{sale.total_price}</td>
                  <td className="data">
                    {sale.items.map((item) => (
                      <p>
                        {item.product_name} - {item.quantity}
                      </p>
                    ))}
                  </td>
                  {sale.state === "closed" ? (
                    <td className="data closed">Cerrada</td>
                  ) : (
                    <td className="data open">Abierta</td>
                  )}
                </tr>
              ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Modal;
