## Why

**Hoy la app no valida nada: el mismo `EscanApp.exe` corre en cuantas PC quieran.**

Esto es el cimiento del cobro. Sin una licencia que la app verifique, no hay diferencia entre un cliente que pagó y uno que copió el `.exe` de un pendrive. Y es todavía más crítico si el modelo pasa a ser mensual: sin validación no hay forma de que el software deje de funcionar cuando vence el mes.

La decisión de negocio ya está tomada: **una licencia habilita 1 (una) computadora** (ver términos de la landing). Falta que el software lo haga cumplir.

Este change es **solo de diseño**: define la capacidad `licensing` en el SDD. No se escribe código todavía. Es a propósito —es la parte del sistema que decide si un cliente puede usar lo que pagó, y equivocar el diseño (dejar un bypass trivial, o al revés, bloquear a un cliente legítimo que cambió de PC) es caro en las dos direcciones.

## What Changes

- **Clave de licencia por compra.** Al aprobarse una orden, el backend de la landing SHALL generar una clave de licencia única ligada a esa orden, y entregársela al comprador (junto al enlace de descarga, por la misma vía: pantalla de éxito y correo).
- **Activación ligada a la máquina.** En el primer arranque, la app SHALL pedir la clave y activarla contra el servidor de licencias, que la vincula a una huella de la computadora (machine fingerprint). Una clave activa **1 máquina**; un segundo intento en otra PC SHALL rechazarse (con un camino de reactivación asistida para el caso legítimo de cambio de equipo).
- **Validación con tolerancia offline.** La app SHALL guardar un comprobante de activación firmado y revalidar periódicamente. Un kiosco puede quedarse sin Internet: la app SHALL seguir funcionando durante un período de gracia y solo bloquear si la revalidación falla de forma sostenida o la licencia venció.
- **Vencimiento opcional (preparado para lo mensual).** La licencia SHALL poder tener o no fecha de vencimiento. Hoy (pago único) se emite sin vencimiento; el mismo mecanismo soporta el cobro mensual sin rediseño.
- **Estado consultable.** La app SHALL exponer el estado de la licencia (activa, período de gracia, vencida, no activada) para poder diagnosticar, reutilizando el patrón del endpoint de estado de la IA (`/api/system/status`).

## Capabilities

### Added Capabilities
- `licensing`: activación, vinculación a máquina (1 por licencia), revalidación con gracia offline y soporte de vencimiento.

## Impact

- **Nuevo dominio SDD** `openspec/specs/licensing/` (se materializa al archivar este change).
- **EscanApp (esta app):** nuevo módulo de licencia (activación, almacenamiento del comprobante firmado, revalidación, gate de arranque), un endpoint de estado y una pantalla de activación en el frontend.
- **Landing (`LandingBarcode`):** emisión de la clave al aprobar la orden y un endpoint de activación/validación (el servidor de licencias). Se conecta con el flujo de correo ya existente (`webhooks.py`).
- **Decisión de alcance:** 1 activación por licencia. La reactivación por cambio de PC se resuelve asistida (soporte libera la máquina anterior), no automática, para no abrir un bypass.
- **Seguridad:** el comprobante local SHALL estar firmado por el servidor; una fecha de vencimiento editada a mano en el disco del cliente NO SHALL alcanzar para extender la licencia.
- **No** se implementa nada en este change: es el contrato. La implementación va en un change posterior, cuando este diseño esté aprobado.
