import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Alert,
} from "react-native";
import { createProduct } from "../api/client";

export default function AddProductScreen() {
  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [description, setDescription] = useState("");

  const handleSubmit = async () => {
    if (!barcode.trim() || !name.trim() || !price.trim()) {
      Alert.alert("Error", "Completa los campos obligatorios");
      return;
    }

    try {
      const data = await createProduct(barcode, name, parseFloat(price), description);
      Alert.alert("Éxito", `Producto creado: ${data.product?.name || name}`);
      setBarcode("");
      setName("");
      setPrice("");
      setDescription("");
    } catch (err) {
      Alert.alert("Error", err.message || "No se pudo crear el producto");
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.form}>
        <Text style={styles.title}>Agregar productos</Text>
        <Text style={styles.description}>
          Ingresa los datos del producto para crear un nuevo registro en el inventario.
        </Text>

        <View style={styles.field}>
          <Text style={styles.label}>Código de barras *</Text>
          <TextInput
            style={styles.input}
            value={barcode}
            onChangeText={setBarcode}
            placeholder="Código de barras"
          />
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Nombre *</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="Nombre del producto"
          />
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Precio *</Text>
          <TextInput
            style={styles.input}
            value={price}
            onChangeText={setPrice}
            placeholder="Precio"
            keyboardType="decimal-pad"
          />
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Descripción</Text>
          <TextInput
            style={styles.input}
            value={description}
            onChangeText={setDescription}
            placeholder="Descripción opcional"
          />
        </View>

        <TouchableOpacity style={styles.button} onPress={handleSubmit}>
          <Text style={styles.buttonText}>Guardar producto</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f6f4ff", padding: 16 },
  form: { backgroundColor: "#fff", borderRadius: 12, padding: 20, shadowColor: "#000", shadowOpacity: 0.1, shadowRadius: 8, elevation: 4 },
  title: { fontSize: 22, fontWeight: "bold", color: "#7b46ff", marginBottom: 8 },
  description: { fontSize: 14, color: "#666", marginBottom: 20 },
  field: { marginBottom: 16 },
  label: { fontSize: 14, fontWeight: "600", color: "#333", marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: "#fafafa",
  },
  button: {
    backgroundColor: "#7b46ff",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 8,
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
