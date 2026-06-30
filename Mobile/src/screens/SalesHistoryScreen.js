import React, { useState } from "react";
import {
  View,
  Text,
  FlatList,
  Modal,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Platform,
} from "react-native";
import { getSalesByDate } from "../api/client";

export default function SalesHistoryScreen() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [sales, setSales] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedSale, setSelectedSale] = useState(null);

  const handleDatePress = async (date) => {
    const formatted = date.toISOString().split("T")[0];
    try {
      const data = await getSalesByDate(formatted);
      setSales(data);
      setSelectedDate(date);
    } catch (err) {
      setSales([]);
    }
  };

  const months = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
  ];

  const daysInMonth = new Date(
    selectedDate.getFullYear(),
    selectedDate.getMonth() + 1,
    0
  ).getDate();

  const firstDay = new Date(
    selectedDate.getFullYear(),
    selectedDate.getMonth(),
    1
  ).getDay();

  const days = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(i);

  const changeMonth = (delta) => {
    const newDate = new Date(selectedDate);
    newDate.setMonth(newDate.getMonth() + delta);
    setSelectedDate(newDate);
  };

  const openModal = (sale) => {
    setSelectedSale(sale);
    setModalVisible(true);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.calendar}>
        <View style={styles.calendarHeader}>
          <TouchableOpacity onPress={() => changeMonth(-1)}>
            <Text style={styles.arrow}>{"<"}</Text>
          </TouchableOpacity>
          <Text style={styles.monthTitle}>
            {months[selectedDate.getMonth()]} {selectedDate.getFullYear()}
          </Text>
          <TouchableOpacity onPress={() => changeMonth(1)}>
            <Text style={styles.arrow}>{">"}</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.weekDays}>
          {["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"].map((d) => (
            <Text key={d} style={styles.weekDay}>{d}</Text>
          ))}
        </View>
        <View style={styles.daysGrid}>
          {days.map((day, i) => (
            <TouchableOpacity
              key={i}
              style={[
                styles.day,
                day === selectedDate.getDate() && styles.selectedDay,
              ]}
              onPress={() => {
                if (day) {
                  const d = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), day);
                  handleDatePress(d);
                }
              }}
              disabled={!day}
            >
              <Text style={[styles.dayText, day === selectedDate.getDate() && styles.selectedDayText]}>
                {day || ""}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <FlatList
        data={sales}
        keyExtractor={(item) => item.id.toString()}
        ListEmptyComponent={
          <Text style={styles.empty}>No hay ventas en esta fecha</Text>
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.saleCard} onPress={() => openModal(item)}>
            <Text style={styles.saleId}>Venta #{item.id}</Text>
            <Text>Total: ${item.total_price}</Text>
            <Text>Productos: {item.items?.length || 0}</Text>
          </TouchableOpacity>
        )}
      />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Detalle de Venta #{selectedSale?.id}</Text>
            <FlatList
              data={selectedSale?.items || []}
              keyExtractor={(item) => item.id.toString()}
              renderItem={({ item }) => (
                <View style={styles.modalItem}>
                  <Text style={styles.modalItemName}>{item.product_name}</Text>
                  <Text>Qty: {item.quantity} x ${item.unit_price}</Text>
                  <Text style={styles.subtotal}>Subtotal: ${item.subtotal}</Text>
                </View>
              )}
            />
            <Text style={styles.modalTotal}>
              Total: ${selectedSale?.total_price}
            </Text>
            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setModalVisible(false)}
            >
              <Text style={styles.closeButtonText}>Cerrar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f6f4ff", padding: 16 },
  calendar: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  calendarHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  arrow: { fontSize: 24, color: "#7b46ff", paddingHorizontal: 16 },
  monthTitle: { fontSize: 18, fontWeight: "bold", color: "#333" },
  weekDays: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginBottom: 8,
  },
  weekDay: { fontWeight: "600", color: "#666", width: "14.28%", textAlign: "center" },
  daysGrid: { flexDirection: "row", flexWrap: "wrap" },
  day: {
    width: "14.28%",
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: 20,
  },
  selectedDay: { backgroundColor: "#7b46ff" },
  dayText: { fontSize: 14, color: "#333" },
  selectedDayText: { color: "#fff", fontWeight: "bold" },
  empty: { textAlign: "center", color: "#999", marginTop: 40, fontSize: 16 },
  saleCard: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 16,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  saleId: { fontWeight: "bold", fontSize: 16, marginBottom: 4 },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    padding: 24,
  },
  modalContent: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 20,
    maxHeight: "80%",
  },
  modalTitle: { fontSize: 18, fontWeight: "bold", marginBottom: 16, textAlign: "center" },
  modalItem: {
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
    paddingVertical: 8,
  },
  modalItemName: { fontWeight: "600" },
  subtotal: { color: "#7b46ff", fontWeight: "600" },
  modalTotal: {
    fontSize: 18,
    fontWeight: "bold",
    textAlign: "center",
    marginTop: 16,
    color: "#7b46ff",
  },
  closeButton: {
    backgroundColor: "#7b46ff",
    padding: 12,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 16,
  },
  closeButtonText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
});
