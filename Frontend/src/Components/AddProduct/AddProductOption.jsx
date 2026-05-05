import { useState } from "react";
import axios from "axios";
import Nav from "../Nav/nav.jsx";
import "./AddProductOption.css";
import addProductValidation from "./Validation.jsx";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

function AddProductOption() {
  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [errors, setErrors] = useState({});

  const handleSubmit = async (event) => {
    event.preventDefault();

    console.log("Datos a enviar:", { barcode, name, price, description });

    const form = {
      barcode: barcode,
      name: name,
      price: price,
      description: description,
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
      try {
        const response = await axios.post(`${BASE_URL}/api/products/`, {
          barcode,
          name,
          price,
          description,
        });
        console.log("RESPUESTA", response.data);
        setMessage(`Producto creado: ${response.data.product.name}`);
        setBarcode("");
        setName("");
        setPrice("");
        setDescription("");
      } catch (err) {
        setError(err.response?.data?.detail || "No se pudo crear el producto");
      }
    }
  };

  return (
    <section className="option-panel">
      <Nav />

      <form onSubmit={handleSubmit} className="option-form">
        <div className="box-title">
          <h2 className="title">Agregar productos</h2>
          <p className="description">
            Ingresa los datos del producto para crear un nuevo registro en el
            inventario.
          </p>
        </div>
        <div className="form-fields">
          <div className="container-label">
            <label className="label-add-product">
              Código de barras
              <input
                type="text"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                placeholder="Código de barras"
              />
            </label>
            {errors.barcode && <p className="error">{errors.barcode}</p>}
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
            {errors.name && <p className="error">{errors.name}</p>}
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
            {errors.price && <p className="error">{errors.price}</p>}
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
              <p className="error">{errors.description}</p>
            )}
          </div>
        </div>
        <button className="button" type="submit">
          Guardar producto
        </button>
        {message && <p className="success-message">{message}</p>}
        {error && <p className="error-message">{error}</p>}
      </form>
    </section>
  );
}

export default AddProductOption;
