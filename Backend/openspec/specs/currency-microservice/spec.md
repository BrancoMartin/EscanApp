# Currency Microservice Domain

## Overview
Microservicio en C# / .NET para consultar tasas de cambio y convertir monedas usando exchangerate-api.com.

## Requirements

### Requirement: Consultar tasa de cambio
El sistema SHALL obtener la tasa de cambio entre dos monedas desde exchangerate-api.com.

#### Scenario: Tasa obtenida exitosamente
- **WHEN** se solicita GetExchangeRate("ARS", "USD")
- **THEN** el sistema consulta la API externa
- **AND** retorna la tasa de cambio como decimal

#### Scenario: Error en API externa
- **WHEN** la API externa no responde o retorna error
- **THEN** el sistema lanza excepción con mensaje descriptivo

### Requirement: Convertir ARS a USD
El sistema SHALL convertir un monto en ARS a USD usando la tasa de cambio actual.

#### Scenario: Conversión exitosa
- **WHEN** se invoca ConvertArsToUsd(1000)
- **THEN** el sistema consulta la tasa ARS->USD
- **AND** retorna montoInArs * tasa

### Requirement: API REST endpoints
El sistema SHALL exponer endpoints REST para consultar tasas y convertir monedas.

#### Scenario: GET /api/currency/rate/{from}/{to}
- **WHEN** se envía GET /api/currency/rate/USD/ARS
- **THEN** retorna { from, to, rate }

#### Scenario: GET /api/currency/convert/{amount}
- **WHEN** se envía GET /api/currency/convert/1000
- **THEN** retorna { amount_in_ars, amount_in_usd }

## Project Structure
- `Backend/CurrencyMicroservice/CurrencyMicroservice.csproj` — proyecto .NET 8
- `Application/Interfaces/ICurrencyService.cs` — interfaz del servicio
- `Application/Services/CurrencyService.cs` — implementación con IHttpClientFactory
- `Controllers/CurrencyController.cs` — endpoints REST
- `Program.cs` — configuración y DI
- `appsettings.json` — configuración (puerto 5001)

## Dependencies
- exchangerate-api.com (API externa)
- IHttpClientFactory (inyección de dependencias .NET)
