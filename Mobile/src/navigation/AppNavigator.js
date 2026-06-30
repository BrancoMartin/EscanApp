import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import HomeScreen from "../screens/HomeScreen";
import ScanScreen from "../screens/ScanScreen";
import SalesHistoryScreen from "../screens/SalesHistoryScreen";
import AddProductScreen from "../screens/AddProductScreen";

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: "#7b46ff" },
          headerTintColor: "#fff",
          headerTitleStyle: { fontWeight: "bold" },
        }}
      >
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: "EscanApp" }}
        />
        <Stack.Screen
          name="Scan"
          component={ScanScreen}
          options={{ title: "Escanear Productos" }}
        />
        <Stack.Screen
          name="SalesHistory"
          component={SalesHistoryScreen}
          options={{ title: "Historial de Ventas" }}
        />
        <Stack.Screen
          name="AddProduct"
          component={AddProductScreen}
          options={{ title: "Agregar Producto" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
