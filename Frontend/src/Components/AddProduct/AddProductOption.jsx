import { useState, useRef } from "react";
import Nav from "../Nav/nav.jsx";
import "./AddProductOption.css";
import addProductValidation from "./Validation.jsx";
import { Plus, ScanLine, Keyboard, Upload } from "lucide-react";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

// Intervalo máximo (ms) entre caracteres para considerarlo lector de barras.
// Mismo criterio que la pantalla de escaneo.
const SCANNER_MAX_INTERVAL = 50;

function AddProductOption() {
  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [description, setDescription] = useState("");
  const [proveedor, setProveedor] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  // Origen del código: "scanner" | "manual" | "" (todavía no se escribió nada).
  const [barcodeSource, setBarcodeSource] = useState("");

  // Importación masiva desde Excel/CSV.
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [importError, setImportError] = useState("");
  const fileInputRef = useRef(null);

  const lastKeyTimeRef = useRef(0);

  const handleImport = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportResult(null);
    setImportError("");
    setImporting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${BASE_URL}/api/products/import`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw { response: { data } };
      }
      setImportResult(data);
    } catch (err) {
      setImportError(
        err?.response?.data?.detail || "No se pudo importar el archivo"
      );
    } finally {
      setImporting(false);
      // Permite volver a elegir el mismo archivo si hace falta reintentar.
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Mide el tiempo entre teclas para distinguir el lector (rápido) del tecleo
  // manual (lento). Con una sola pausa larga se marca como ingreso manual.
  // A diferencia de la pantalla de escaneo, acá NO se auto-envía nada: todavía
  // faltan el nombre y el precio. La detección es informativa, para poder
  // verificar cuál de los dos caminos de entrada se está ejercitando.
  const handleBarcodeChange = (e) => {
    const value = e.target.value;
    const now = Date.now();

    if (value === "") {
      // Reinicio: nuevo código, se asume lector hasta que se demuestre lo contrario.
      setBarcodeSource("");
    } else if (value.length === 1) {
      // Primer carácter: todavía no hay intervalo para medir.
      setBarcodeSource("scanner");
    } else if (now - lastKeyTimeRef.current > SCANNER_MAX_INTERVAL) {
      setBarcodeSource("manual");
    }

    lastKeyTimeRef.current = now;
    setBarcode(value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    console.log("Datos a enviar:", {
      barcode,
      name,
      price,
      description,
      proveedor,
    });

    const form = {
      barcode: barcode,
      name: name,
      price: price,
      description: description,
      proveedor: proveedor,
    };

    console.log("FORMULARIO POR ENVIARSE A LAS VALIDACIONES");

    const errors = addProductValidation({ form });

    setErrors(errors);

    setMessage("");
    setError("");

    console.log("ERRORES EN EL HANDLE SUBMIT", errors);

    console.log("LONGITUD DE LOS ERRORES", Object.keys(errors).length);

    if (Object.keys(errors).length === 0) {
      console.log("ENTRANDO A MANDAR LOS PRODUCTOS");
      setSaving(true);
      try {
        console.log("MANDANDO DATOS PARA CREAR PRODUCTO");
        console.log("PROOVEDOR: ", proveedor);
        const response = await fetch(`${BASE_URL}/api/products/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            barcode,
            name,
            price,
            description,
            proveedor,
          }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw { response: { data } };
        }
        console.log("RESPUESTA", data);
        setMessage(`Producto creado: ${data.product.name}`);
        setBarcode("");
        setName("");
        setPrice("");
        setDescription("");
        // El proveedor también se limpia: quedaba con el valor del producto
        // anterior y se colaba en el siguiente sin que el usuario lo notara.
        setProveedor("");
        setBarcodeSource("");
      } catch (err) {
        setError(err?.response?.data?.detail || "No se pudo crear el producto");
      } finally {
        setSaving(false);
      }
    }
  };

  return (
    <section className="option-panel">
      <Nav />

      <form onSubmit={handleSubmit} className="option-form">
        <div className="box-title">
          <span className="box-title-icon" aria-hidden="true">
            <Plus></Plus>
          </span>
          <div className="box-title-text">
            <h2 className="title">Agregar productos</h2>
            <p className="description">
              Ingresa los datos del producto para crear un nuevo registro en el
              inventario.
            </p>
          </div>
        </div>
        <div className="form-fields">
          <div className="container-label">
            <label className="label-add-product">
              Código de barras
              <input
                type="text"
                value={barcode}
                onChange={handleBarcodeChange}
                placeholder="Escaneá o escribí el código"
              />
            </label>
            {barcodeSource && (
              <p className={`barcode-source barcode-source--${barcodeSource}`}>
                {barcodeSource === "scanner" ? (
                  <>
                    <ScanLine size={14} aria-hidden="true" /> Escaneado con el
                    lector
                  </>
                ) : (
                  <>
                    <Keyboard size={14} aria-hidden="true" /> Ingresado a mano
                  </>
                )}
              </p>
            )}
            {errors.barcode && (
              <p className="error">* debe ingresar el código de barras</p>
            )}
          </div>

          <div className="container-label">
            <label className="label-add-product">
              Nombre
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nombre del producto"
              />
            </label>
            {errors.name && <p className="error">* debe ingresar el nombre</p>}
          </div>

          <div className="container-label">
            <label className="label-add-product">
              Precio
              <input
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="Precio"
              />
            </label>
            {errors.price && <p className="error">* debe ingresar el precio</p>}
          </div>
          <div className="container-label">
            <label className="label-add-product">
              Descripción
              <input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Descripción opcional"
              />
            </label>
            {errors.description && (
              <p className="error">* debe ingresar la descripción</p>
            )}
          </div>
          <div className="container-label">
            <label className="label-add-product">
              Proveedor
              <input
                value={proveedor}
                onChange={(e) => setProveedor(e.target.value)}
                placeholder="Opcional"
              />
            </label>
          </div>
        </div>
        <button className="button" type="submit" disabled={saving}>
          {saving ? "Guardando..." : "Guardar producto"}
        </button>
        {message && <p className="success-message">{message}</p>}
        {error && <p className="error-message">{error}</p>}
      </form>

      <div className="import-box">
        <div className="box-title">
          <span className="box-title-icon" aria-hidden="true">
            <Upload />
          </span>
          <div className="box-title-text">
            <h2 className="title">Importar desde Excel o CSV</h2>
            <p className="description">
              Cargá tu lista de productos de una vez. Aceptamos Excel (.xlsx) y
              CSV exportados de otros sistemas. El archivo debe tener una fila de
              encabezados con <strong>nombre</strong>, <strong>precio</strong> y{" "}
              <strong>código de barras</strong> (el proveedor es opcional).
            </p>
          </div>
        </div>

        <label className="button import-button">
          {importing ? "Importando..." : "Elegir archivo e importar"}
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xlsm,.xls,.csv,.txt,.tsv"
            onChange={handleImport}
            disabled={importing}
            style={{ display: "none" }}
          />
        </label>

        {importError && <p className="error-message">{importError}</p>}

        {importResult && (
          <div className="import-result">
            <p className="success-message">
              {importResult.importados} producto(s) importado(s)
              {importResult.rechazados > 0 &&
                `, ${importResult.rechazados} rechazado(s)`}
              .
            </p>
            {importResult.errores?.length > 0 && (
              <ul className="import-errors">
                {importResult.errores.map((e) => (
                  <li key={e.fila}>
                    Fila {e.fila}: {e.motivo}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default AddProductOption;
