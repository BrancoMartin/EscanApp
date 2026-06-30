import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  SafeAreaView,
  Alert,
} from "react-native";
import { getPendingSale, scanProduct, closeSale, cancelSale, cancelItem } from "../api/client";

export default function ScanScreen() {
  const [barcode, setBarcode] = useState("");
  const [sale, setSale] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPending();
  }, []);

  const loadPending = async () => {
    try {
      const data = await getPendingSale();
      if (data) setSale(data);
    } catch (err) {
      console.error("Error al cargar venta pendiente:", err);
    }
  };

  const handleScan = async () => {
    if (!barcode.trim()) return;
    setLoading(true);
    try {
      const data = await scanProduct(barcode.trim());
      setSale(data);
      setBarcode("");
    } catch (err) {
      Alert.alert("Error", err.message || "No se pudo escanear el producto");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = async () => {
    try {
      await closeSale(sale.id);
      Alert.alert("Éxito", "Venta cerrada exitosamente");
      setSale(null);
    } catch (err) {
      Alert.alert("Error", err.message || "No se pudo cerrar la venta");
    }
  };

  const handleCancelSale = async () => {
    try {
      await cancelSale(sale.id);
      setSale(null);
    } catch (err) {
      Alert.alert("Error", err.message || "No se pudo cancelar la venta");
    }
  };

  const handleCancelItem = async (item) => {
    if (sale.items.length === 1 && sale.items[0].quantity === 1) {
      handleCancelSale();
      return;
    }
    try {
      await cancelItem(sale.id, item.id);
      const updated = await getPendingSale();
      setSale(updated);
    } catch (err) {
      Alert.alert("Error", err.message || "No se pudo cancelar el producto");
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.form}>
        <Text style={styles.label}>Código de barras</Text>
        <TextInput
          style={styles.input}
          value={barcode}
          onChangeText={setBarcode}
          placeholder="Ej. 1234567890123"
          keyboardType="numeric"
        />
        <TouchableOpacity
          style={styles.button}
          onPress={handleScan}
          disabled={loading || !barcode.trim()}
        >
          <Text style={styles.buttonText}>
            {loading ? "Escaneando..." : "Escanear producto"}
          </Text>
        </TouchableOpacity>
      </View>

      {sale && (
        <View style={styles.ticket}>
          <Text style={styles.ticketTitle}>TICKET</Text>
          <Text style={styles.total}>Total: ${sale.total_price}</Text>
          <FlatList
            data={sale.items}
            keyExtractor={(item) => item.id.toString()}
            renderItem={({ item }) => (
              <View style={styles.itemRow}>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{item.product_name}</Text>
                  <Text>Cantidad: {item.quantity}</Text>
                  <Text>Precio unitario: ${item.unit_price}</Text>
                  <Text>Subtotal: ${item.subtotal}</Text>
                </View>
                <TouchableOpacity
                  style={styles.cancelBtn}
                  onPress={() => handleCancelItem(item)}
                >
                  <Text style={styles.cancelBtnText}>X</Text>
                </TouchableOpacity>
              </View>
            )}
          />
          <View style={styles.ticketActions}>
            <TouchableOpacity style={styles.button} onPress={handleClose}>
              <Text style={styles.buttonText}>Cerrar venta</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={handleCancelSale}
            >
              <Text style={styles.buttonText}>Cancelar venta</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f6f4ff", padding: 16 },
  form: { marginBottom: 20 },
  label: { fontSize: 16, fontWeight: "600", marginBottom: 8, color: "#333" },
  input: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#7b46ff",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  button: {
    backgroundColor: "#7b46ff",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  cancelButton: { backgroundColor: "#e74c3c", marginTop: 8 },
  ticket: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  ticketTitle: {
    fontSize: 20,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 8,
  },
  total: {
    fontSize: 18,
    fontWeight: "700",
    color: "#7b46ff",
    textAlign: "center",
    marginBottom: 16,
  },
  itemRow: {
    flexDirection: "row",
    alignItems: "center",
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
    paddingVertical: 8,
  },
  itemInfo: { flex: 1 },
  itemName: { fontWeight: "600", fontSize: 16 },
  cancelBtn: {
    backgroundColor: "#ff4444",
    borderRadius: 20,
    width: 36,
    height: 36,
    alignItems: "center",
    justifyContent: "center",
  },
  cancelBtnText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
  ticketActions: { marginTop: 16, gap: 8 },
});
