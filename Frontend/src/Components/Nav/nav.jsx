import { NavLink } from "react-router-dom";
import "./nav.css";
import { ScanLine, Plus, Calendar, House, Clock } from "lucide-react";

const links = [
  { to: "/", label: "Inicio", icon: <House></House>, end: true },
  { to: "/add-product", label: "Agregar producto", icon: <Plus></Plus> },
  {
    to: "/scan-products",
    label: "Escanear productos",
    icon: <ScanLine></ScanLine>,
  },
  {
    to: "/sales-history",
    label: "Historial de ventas",
    icon: <Calendar></Calendar>,
  },
  { to: "/last-sales", label: "Últimas 24 hs", icon: <Clock></Clock> },
];

function Nav() {
  return (
    <nav className="main-nav">
      <div className="nav-brand">
        <span className="nav-brand-icon">
          <img src="/icono1.ico" alt="Logo" />
        </span>
        <span className="nav-brand-name">EscanApp</span>
      </div>
      <ul className="list-nav">
        {links.map((link) => (
          <li className="item-list" key={link.to}>
            <NavLink to={link.to} end={link.end}>
              <span className="item-icon" aria-hidden="true">
                {link.icon}
              </span>
              <span className="item-label">{link.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default Nav;
