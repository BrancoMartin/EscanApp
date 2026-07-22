# Tareas — solo diseño en este change

> Este change es de DISEÑO. No se implementa código: define el contrato de la
> capacidad `licensing`. La implementación va en un change posterior, una vez
> aprobado este.

## 1. Diseño acordado en la propuesta

- [x] 1.1 Alcance de licencia: 1 activación por clave (decisión de negocio)
- [x] 1.2 Emisión de la clave al aprobar la orden (reusa el flujo de correo de la landing)
- [x] 1.3 Activación ligada a huella de máquina + reactivación asistida por cambio de PC
- [x] 1.4 Validación con período de gracia offline
- [x] 1.5 Comprobante local firmado por el servidor (anti-manipulación)
- [x] 1.6 Vencimiento opcional (soporta el futuro cobro mensual sin rediseño)
- [x] 1.7 Estado de licencia consultable
- [x] 1.8 `openspec validate licensing-system`

## 2. Decisiones abiertas para el change de implementación (NO en este)

- [ ] 2.1 Elegir la huella de máquina (¿volume serial + MAC? evitar falsos negativos por cambios de hardware menores)
- [ ] 2.2 Definir el período de gracia por defecto (p. ej. 7 días) y su cadencia de revalidación
- [ ] 2.3 Esquema de firma del comprobante (clave asimétrica del servidor; la pública viaja en la app)
- [ ] 2.4 Dónde vive el servidor de licencias: extender el backend de la landing vs. servicio aparte
- [ ] 2.5 Formato y longitud de la clave de licencia
- [ ] 2.6 UX de la pantalla de activación y del bloqueo por vencimiento/gracia
