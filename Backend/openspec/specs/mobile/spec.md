# Mobile Frontend Domain

## Overview
Aplicación móvil React Native que consume la API REST del BarcodePaymentSystem, permitiendo escanear productos, gestionar ventas y consultar historial.

## Requirements

### Requirement: Navegación
El sistema SHALL tener navegación por tabs/stack entre pantallas.

#### Scenario: Pantallas disponibles
- **WHEN** el usuario abre la app
- **THEN** ve la pantalla de inicio con 3 botones
- **AND** puede navegar a Escanear, Historial o Agregar Producto

### Requirement: Escanear productos
El sistema SHALL permitir escanear códigos de barras y mostrar el ticket de venta pendiente.

#### Scenario: Escaneo exitoso
- **WHEN** el usuario ingresa un barcode
- **THEN** se agrega el producto a la venta pendiente
- **AND** se actualiza el ticket

#### Scenario: Cerrar venta
- **WHEN** el usuario cierra la venta
- **THEN** la venta pasa a estado "closed"

### Requirement: Historial de ventas
El sistema SHALL mostrar un calendario para seleccionar fecha y listar ventas.

#### Scenario: Calendario nativo
- **WHEN** el usuario selecciona una fecha
- **THEN** se cargan las ventas de ese día
- **AND** puede ver detalle en modal

### Requirement: Agregar producto
El sistema SHALL permitir crear nuevos productos desde el móvil.

#### Scenario: Creación exitosa
- **WHEN** el usuario completa el formulario
- **THEN** se envía POST a /api/products/
- **AND** se muestra confirmación

## Project Structure
- `Mobile/App.js` — entry point
- `src/navigation/AppNavigator.js` — React Navigation stack
- `src/screens/HomeScreen.js` — pantalla de inicio
- `src/screens/ScanScreen.js` — escaneo y ticket
- `src/screens/SalesHistoryScreen.js` — historial con calendario
- `src/screens/AddProductScreen.js` — formulario de alta
- `src/api/client.js` — cliente HTTP con fetch

## Dependencies
- React Native 0.76
- React Navigation (native-stack)
- AsyncStorage
