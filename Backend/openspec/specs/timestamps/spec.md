# Timestamps — Spec

## Overview
Agregar created_at/updated_at a modelos que faltan.

Estado actual: `Sale` y `Category` tienen `created_at`. `Product`, `Attribute`, `ProductAttribute` no.

**Propósito**: Auditoría y trazabilidad.

## Dependencias
- Ninguna

## Implementation Notes
- `Sale.created_at` MUST conservar fecha y hora para permitir consultas por ventanas relativas como "últimas 24 horas".
- Los flujos que creen ventas (`POST /api/sales/` y escaneo que crea venta pendiente) MUST usar `datetime.now()` o un valor equivalente con hora, no `date.today()`.
