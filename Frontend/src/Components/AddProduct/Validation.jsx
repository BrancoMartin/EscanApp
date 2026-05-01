const addProductValidation = ({ form }) => {
  console.log("FORMULARIO ENTRANDO AL ADD PRODUCT", form);
  const errors = {};

  const names = ["barcode", "name", "price", "description"];
  for (const n of names) {
    if (!form[n].trim()) {
      errors[n] = `* debe ingresar el ${n}`;
    }
  }

  console.log("ERRORES", errors);

  return errors;
};

export default addProductValidation;
