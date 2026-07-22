## ADDED Requirements

### Requirement: Emisión de la clave de licencia al comprar

Cuando una orden de compra pasa a aprobada, el sistema SHALL generar una clave de licencia única, ligada a esa orden, y entregársela al comprador por los mismos canales que el enlace de descarga (pantalla de éxito y correo). La clave SHALL ser suficientemente larga y aleatoria como para no ser adivinable.

#### Scenario: Orden aprobada genera clave

- **WHEN** una orden pasa a aprobada por primera vez
- **THEN** el sistema genera una clave de licencia única asociada a la orden
- **AND** se la hace llegar al comprador junto con el enlace de descarga
- **AND** no se genera una segunda clave si el webhook de pago se reintenta

#### Scenario: La clave nace sin vencimiento en el modelo de pago único

- **WHEN** el plan comprado es de pago único
- **THEN** la licencia se emite sin fecha de vencimiento

### Requirement: Activación ligada a una única máquina

La app SHALL requerir activar la clave de licencia en el primer arranque. La activación SHALL vincular la clave a una huella de la computadora (machine fingerprint). Una clave SHALL admitir **1 (una)** máquina activa a la vez.

#### Scenario: Primera activación

- **WHEN** el usuario ingresa una clave válida no activada en su primera PC
- **THEN** el sistema vincula la clave a la huella de esa máquina
- **AND** habilita la app
- **AND** guarda un comprobante de activación firmado por el servidor

#### Scenario: Segunda máquina rechazada

- **WHEN** se intenta activar una clave ya vinculada a otra máquina distinta
- **THEN** el sistema rechaza la activación
- **AND** informa que la licencia ya está en uso en otra computadora
- **AND** NO habilita la app en la segunda máquina

#### Scenario: Reactivación en la misma máquina

- **WHEN** se reactiva una clave en la MISMA máquina a la que ya estaba vinculada (reinstalación)
- **THEN** el sistema la acepta sin consumir una activación nueva

#### Scenario: Cambio de computadora asistido

- **WHEN** un cliente legítimo cambia de PC y su clave sigue vinculada a la anterior
- **THEN** el sistema ofrece un camino de reactivación asistida (soporte libera la máquina anterior)
- **AND** la liberación no es automática, para no habilitar un uso simultáneo en dos equipos

### Requirement: Validación con tolerancia offline

La app SHALL guardar localmente el comprobante de activación firmado y revalidar la licencia contra el servidor de forma periódica. Ante falta de conexión, la app SHALL seguir funcionando durante un período de gracia configurable. Solo SHALL bloquear el uso si la revalidación falla de forma sostenida más allá de la gracia, o si la licencia está vencida o fue revocada.

#### Scenario: Sin Internet dentro de la gracia

- **WHEN** la app no puede contactar al servidor de licencias pero está dentro del período de gracia
- **THEN** la app sigue funcionando normalmente

#### Scenario: Sin Internet más allá de la gracia

- **WHEN** la revalidación falla de forma sostenida y se supera el período de gracia
- **THEN** la app bloquea el uso e informa que necesita conectarse para validar la licencia

#### Scenario: Comprobante manipulado

- **WHEN** el comprobante local fue editado (por ejemplo, para extender el vencimiento)
- **THEN** la validación de la firma falla
- **AND** el sistema trata la licencia como no válida

### Requirement: Vencimiento de licencia (soporte de cobro recurrente)

La licencia SHALL poder tener o no una fecha de vencimiento. Si la tiene, una vez pasada esa fecha la app SHALL bloquear el uso hasta que la licencia se renueve. Este mecanismo SHALL ser el mismo tanto para el pago único (sin vencimiento) como para un futuro cobro mensual (con vencimiento renovable).

#### Scenario: Licencia mensual vigente

- **WHEN** la licencia tiene vencimiento y la fecha actual es anterior
- **THEN** la app funciona normalmente

#### Scenario: Licencia mensual vencida

- **WHEN** la fecha de vencimiento de la licencia ya pasó
- **THEN** la app bloquea el uso e informa que la licencia venció
- **AND** ofrece renovarla

### Requirement: Estado de la licencia consultable

La app SHALL exponer el estado actual de la licencia en uno de estos valores: `no_activada`, `activa`, `periodo_gracia`, `vencida`, `revocada`. Este estado SHALL poder consultarse para diagnóstico, del mismo modo que el estado del agente de IA en `/api/system/status`.

#### Scenario: Consultar estado

- **WHEN** se consulta el estado de la licencia
- **THEN** el sistema devuelve uno de los estados definidos
- **AND** si aplica, la fecha de vencimiento y hasta cuándo dura el período de gracia
