import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./nav.css";

function Nav() {
  return (
    <nav className="main-nav">
      <ul className="list-nav">
        <li className="item-list">
          <a href="/">Inicio</a>
        </li>
        <li className="item-list">
          <a href="/add-product">Agregar producto</a>
        </li>
        <li className="item-list">
          <a href="/scan-products">Escanear productos</a>
        </li>
        <li className="item-list">
          <a href="/sales-history">Historial de ventas</a>
        </li>
        <li className="item-list">
          <a href="/last-sales">Ventas de las ultimas 24 hs</a>
        </li>
      </ul>
    </nav>
  );
}

export default Nav;
