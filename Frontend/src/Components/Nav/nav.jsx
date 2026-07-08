import { NavLink } from "react-router-dom";
import "./nav.css";

const links = [
  { to: "/", label: "Inicio", end: true },
  { to: "/add-product", label: "Agregar producto" },
  { to: "/scan-products", label: "Escanear productos" },
  { to: "/sales-history", label: "Historial de ventas" },
  { to: "/last-sales", label: "Ventas de las ultimas 24 hs" },
];

function Nav() {
  return (
    <nav className="main-nav">
      <ul className="list-nav">
        {links.map((link) => (
          <li className="item-list" key={link.to}>
            <NavLink to={link.to} end={link.end}>
              {link.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default Nav;
