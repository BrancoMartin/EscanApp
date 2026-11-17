# AGENTS.md — EscanApp

Este archivo define las instrucciones obligatorias para cualquier agente de IA o desarrollador que trabaje en EscanApp. Debe leerse completo antes de inspeccionar, modificar o ejecutar el proyecto.

## 1. Producto y objetivo

EscanApp es un punto de venta (POS) de escritorio para Windows, orientado principalmente a kioscos y pequeños comercios de Argentina.

El objetivo del producto es ofrecer una aplicación sencilla, confiable y profesional para gestionar productos, códigos de barras y ventas. Las decisiones técnicas deben priorizar la estabilidad, la protección de los datos del comercio, la facilidad de uso y el mantenimiento a largo plazo.

No asumir que una funcionalidad está implementada porque figure en el roadmap, en una propuesta OpenSpec o en este documento. Antes de modificarla, inspeccionar el código y verificar su estado real.

## 2. Stack y estructura general

- Aplicación de escritorio Windows.
- Backend: Python + FastAPI.
- Frontend: React 19 + Vite 8.
- Contenedor de escritorio: pywebview.
- Base de datos local: SQLite.
- IA local: Ollama, con nueve agentes/modelos definidos en `Modelfiles/`.
- Empaquetado: PyInstaller + Inno Setup 6.
- `main.py` es el único punto de entrada de la aplicación.
- `Mobile/` es un cliente React Native separado; no forma parte del empaquetado actual de escritorio.
- `Backend/CurrencyMicroservice/` es un proyecto independiente .NET 8; no está integrado al runtime Python ni incluido en PyInstaller.

### Flujo de una petición

`main.py` → `Backend/api/app.py:create_app()` → routers → services → repositories → models.

Los routers actuales incluyen, entre otros, `/api/products`, `/api/sales`, `/api/agent` y rutas `/api` para categorías y atributos. Los servicios nuevos deben conectarse mediante `Backend/dependencies.py` cuando corresponda.

Antes de agregar una capa, patrón, servicio externo o dependencia, comprobar si ya existe una solución en el proyecto. Evitar duplicar responsabilidades.

## 3. Comandos de desarrollo y validación

Ejecutar los comandos desde la raíz del repositorio, salvo que se indique lo contrario.

| Tarea | Comando |
| --- | --- |
| Desarrollo completo (backend :8000 + Vite :5173) | `.\start.ps1 -Mode dev` |
| Aplicación de escritorio | `python main.py` o `.\start.ps1 -Mode desktop` |
| Backend sin ventana | `python main.py --no-window` |
| Frontend solamente | `cd Frontend; npm run dev` |
| Lint frontend | `cd Frontend; npm run lint` |
| Build frontend | `cd Frontend; npm run build` |
| Tests backend (pytest, bases temporales) | `pip install -r requirements-dev.txt` y `python -m pytest` |
| Crear una migración de esquema (CLI dev) | `cd Backend; alembic revision --autogenerate -m "descripcion"` |
| Aplicar migraciones (CLI dev) | `cd Backend; alembic upgrade head` |
| Listar y restaurar copias de seguridad | `python scripts/restore_backup.py --list` (con la app cerrada) |
| Listar cambios OpenSpec | `cd Backend; openspec list` |
| Crear cambio OpenSpec | `cd Backend; openspec new change <kebab-name>` |
| Crear release | actualizar `VERSION` y ejecutar `scripts\build_release.bat` |
| Release sin reconstruir frontend | `powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -SkipFrontend` |
| Release omitiendo instalación de dependencias | `powershell -ExecutionPolicy Bypass -File scripts\build_release.ps1 -SkipDeps` |

Notas importantes:

- `start.ps1` crea o reutiliza `.venv`, instala `requirements.txt` y configura `PYTHONPATH`.
- El entorno virtual del repositorio utiliza Python 3.12.
- Ejecutar Python desde la raíz. No ejecutar `python Backend/api/app.py`: puede romper los imports `from Backend...`.
- El puerto 8000 debe estar libre durante el desarrollo. `main.py` puede elegir un puerto libre alternativo si 8000 está ocupado, pero `start.ps1` y Vite esperan el puerto 8000.
- Vite redirige las peticiones `/api` a `localhost:8000` durante el desarrollo.
- FastAPI sirve `Frontend/dist` en `/` cuando ese directorio existe.
- Verificar los comandos reales en los scripts antes de cambiarlos. No inventar comandos ni asumir que un script hace algo que no hace.

## 4. Reglas obligatorias antes de modificar código

1. Leer este archivo completo.
2. Inspeccionar el código relacionado con la tarea y seguir el flujo existente.
3. Consultar `cd Backend; openspec list` y revisar si hay un change relacionado.
4. Para cambios funcionales, arquitectónicos, de base de datos o de comportamiento, crear o actualizar una propuesta OpenSpec en `Backend/openspec/changes/` antes de implementar. Seguir `proposal.md`, `design.md` y `tasks.md` cuando existan.
5. Si el cambio es pequeño y puramente correctivo, documentar igualmente el alcance y la validación en el PR o informe final. Si OpenSpec lo exige, no omitirlo.
6. Identificar qué datos, pantallas, endpoints y flujos existentes podrían verse afectados.
7. No modificar archivos o componentes ajenos a la tarea sin una razón concreta y documentada.

No implementar una solución grande directamente sin entender primero el diseño y las decisiones existentes.

## 5. Protección de datos y base de datos

La base de datos puede contener información real de comercios. Tratarla siempre como datos de producción, incluso durante el desarrollo local.

### Ubicaciones actuales

- Desarrollo: `<repo>/pos.db`.
- Aplicación empaquetada: `%LOCALAPPDATA%\EscanApp\pos.db`.
- `ESCANAPP_DATA_DIR` permite definir un directorio alternativo y aislado para comprobaciones desechables.
- `Backend/database.py` utiliza `runtime.db_path()` para resolver la ubicación.

### Reglas no negociables

- Nunca borrar, reemplazar, truncar, recrear ni limpiar una base de datos existente sin autorización explícita del responsable del proyecto.
- Nunca ejecutar pruebas o scripts destructivos sobre `pos.db` ni sobre la base de datos de un cliente.
- Para pruebas, usar una base temporal en un directorio aislado, por ejemplo mediante `ESCANAPP_DATA_DIR`.
- Antes de una operación que pueda alterar datos o el esquema de una base existente, crear un backup y verificar que el archivo de backup sea legible y consistente.
- Si el backup falla o no puede verificarse, detener la operación. No continuar con la migración ni con la modificación de datos.
- No imprimir datos sensibles ni credenciales en logs, consola, reportes o mensajes de error.
- No cambiar la ubicación de datos de clientes ni el mecanismo de persistencia sin analizar el impacto en instalaciones existentes.
- Las operaciones de venta, stock, pagos y movimientos de caja deben preservar consistencia transaccional. Evitar estados parcialmente guardados.

### Estado actual del esquema

El esquema lo administra **Alembic** (implementado en el change `database-migrations`). `Base.metadata.create_all()` ya no se usa en runtime: `Backend/database.py:init_db()` delega en `Backend/migrations_runner.py`, que al arrancar clasifica la base y aplica las migraciones pendientes.

- Modelos: `Backend/models/`, con `Base` en `Backend/models/base.py` (nunca importar `Base` desde `Backend/database` en código nuevo).
- Revisiones: `Backend/migrations/versions/`; la revisión base `0001` reproduce el DDL exacto de 1.0.1 con SQL crudo, porque `op.create_table` aplicaría la `naming_convention` nueva.
- Clasificación al arrancar: A (nueva), B (versionada), C (1.0.x con las 6 tablas, se sella), D (vacía) y E (desconocida → no se toca, la app no arranca).
- Antes de migrar una base con datos se crea una copia verificada en `backups/`; si la copia falla, no se migra.
- `installer/seed/pos.db` fue retirado: las tablas las crea siempre la migración base.

Reglas:

- Todo cambio de esquema va en una migración versionada; nada depende de `create_all()`.
- Revisar a mano el `--autogenerate`: SQLite requiere `render_as_batch` para varias operaciones y la restricción sin nombre de `product_attributes` está filtrada a propósito en `Backend/db_autogen.py` (nombrarla es una migración explícita pendiente, no un efecto de Alembic).
- Las migraciones deben ser compatibles con bases de clientes existentes y con el proceso de actualización.
- Probar upgrades desde una base 1.0.x con datos ficticios y probar instalación nueva y actualización. Usar `ESCANAPP_DATA_DIR` para bases descartables; nunca `pos.db`.
- La actualización hace backup verificado antes de migrar; ante cualquier fallo del backup, no migrar.
- El empaquetado incluye `Backend/migrations` y falla el build si falta (`pos.spec`).
- No modificar la revisión base ni la estrategia de baseline sin completar el diseño OpenSpec y las pruebas de actualización correspondientes.

## 6. Arquitectura y convenciones de código

### Backend

- Mantener la separación existente entre API, services, repositories y models.
- Los routers deben ocuparse de HTTP y validación de entrada/salida; la lógica de negocio debe vivir en services.
- Acceder a persistencia mediante repositories o el patrón ya utilizado por el módulo.
- Inyectar dependencias siguiendo `Backend/dependencies.py`.
- Evitar lógica de negocio duplicada entre endpoints.
- Manejar errores de forma explícita y devolver respuestas coherentes. No ocultar excepciones relevantes con bloques `except` genéricos.

### Frontend

- `Frontend/` es la SPA activa de escritorio.
- Usar `fetch` nativo para HTTP; no incorporar Axios.
- Respetar la estructura, componentes, estilos y convenciones existentes antes de crear abstracciones nuevas.
- Gestionar estados de carga, errores, confirmaciones y estados vacíos.
- Evitar duplicar lógica de acceso a API si ya existe un helper o patrón en el proyecto.
- La interfaz debe ser clara para un usuario de kiosco: acciones evidentes, textos breves y errores comprensibles.

### Nombres e idioma

- Identificadores de código en inglés.
- Textos visibles para el usuario, términos comerciales y comentarios en español.
- Mantener consistencia en nombres, formatos de moneda, fechas y mensajes.
- No introducir emojis en la interfaz salvo que el responsable lo solicite expresamente.

### Restricciones conocidas

- `Backend/openspec/config.yaml` prohíbe `isinstance()`. No agregar nuevas apariciones. Usar verificaciones explícitas compatibles con la configuración del proyecto.
- Existe una aparición previa señalada en `Backend/services/product_import_service.py`; no ampliar ese patrón.
- No agregar dependencias o tecnologías nuevas sin justificar por qué son necesarias y qué impacto tienen en tamaño, mantenimiento, compatibilidad y distribución.

## 7. Inteligencia artificial y Ollama

- Los nueve modelos se crean desde `Modelfiles/*` mediante `Backend/agent/provisioning.py` durante el inicio.
- `Backend/api/routes/controller_agent.py` contiene rutas rápidas determinísticas mediante regex antes de llamar al modelo 0.5b.
- El modelo pequeño no es confiable para interpretar códigos de barras, precios y totales. Preservar las validaciones y resoluciones determinísticas existentes.
- Mantener el presupuesto actual de un modelo por request salvo que un cambio OpenSpec justifique y mida otra estrategia.
- No delegar a un LLM cálculos de dinero, totales, descuentos, impuestos, códigos de barras ni operaciones que deban ser exactas.
- La IA puede interpretar lenguaje natural o asistir al usuario, pero la lógica crítica del POS debe validarse con código determinístico.
- Considerar el rendimiento en PCs de kiosco de recursos limitados. Evitar descargas, inicializaciones o llamadas a modelos innecesarias.
- La aplicación debe informar claramente cuando Ollama o un modelo no esté disponible. No bloquear funciones esenciales de venta por una falla de IA si pueden operar sin ella.
- No afirmar que existe un modo completo sin IA hasta implementarlo y probarlo.

El estado pendiente de creación de productos está actualmente en el diccionario en memoria `_pending_products`, con clave `"default"`, en `controller_agent.py`. Esto supone un único usuario y se pierde al reiniciar. No ampliar esta solución sin evaluar persistencia, concurrencia y múltiples usuarios.

## 8. Reglas de negocio y producto

EscanApp se está preparando para su uso comercial en kioscos. Las funcionalidades deben responder a flujos reales de un comercio y no solamente a una demostración técnica.

Antes de implementar una función, considerar:

- Qué necesita hacer el kiosquero y cuántos pasos requiere.
- Qué ocurre si el lector de códigos de barras falla o lee un código desconocido.
- Qué sucede ante pérdida de conexión, cierre inesperado o reinicio.
- Cómo se evitan ventas duplicadas, importes incorrectos y pérdida de datos.
- Cómo se corrige una operación sin borrar el historial de auditoría.
- Qué información necesita el usuario para entender el resultado.

No inventar reglas comerciales, fiscales o contables. Si falta una definición —por ejemplo, tratamiento fiscal del ticket, impuestos, medios de pago o política de anulaciones—, documentar la decisión pendiente y solicitar confirmación antes de implementarla.

### Comportamientos existentes que requieren cuidado

- El historial de ventas está limitado intencionalmente a las últimas 24 horas en las consultas actuales. No cambiar ese comportamiento silenciosamente. Si el producto necesita historial completo, proponer el cambio como decisión funcional independiente y actualizar API, UI y pruebas.
- La existencia de endpoints no implica que la funcionalidad esté disponible en la interfaz. Verificar ambos lados.
- No asumir que hay control de stock, cierre de caja, impresión fiscal, usuarios, roles, licencias, backups automáticos o actualizaciones automáticas: verificar implementación real antes de mencionarlos como disponibles.

## 9. Seguridad y privacidad

- No guardar claves API, contraseñas, tokens, secretos, certificados privados ni credenciales en el repositorio.
- Usar variables de entorno o mecanismos seguros de configuración para secretos.
- No incluir secretos en `.env` versionados, instaladores, logs, capturas ni documentación pública.
- Validar y normalizar entradas en backend; no confiar únicamente en validaciones del frontend.
- Aplicar el principio de mínimo privilegio cuando se incorporen usuarios, roles o servicios remotos.
- Proteger endpoints y operaciones administrativas cuando el sistema de autenticación esté implementado.
- No enviar datos de ventas, clientes o productos a servicios externos o modelos en la nube sin autorización y una definición explícita de privacidad.
- Registrar errores técnicos sin exponer información sensible.
- Toda integración externa debe usar HTTPS y validar firmas/autenticidad cuando corresponda.

## 10. Pruebas y criterios de calidad

El estado inicial documentado del proyecto no cuenta con una suite de tests consolidada y `pytest` no está instalado en el entorno actual, aunque aparece en la configuración OpenSpec. Verificar el estado real antes de asumir lo contrario.

A medida que se implemente la infraestructura de pruebas:

- Cada cambio funcional debe incorporar o actualizar pruebas automatizadas.
- Los tests deben usar bases temporales y datos ficticios; nunca la base real del repositorio o de un cliente.
- Cubrir casos normales, errores, límites y regresiones relevantes.
- Para lógica de dinero, ventas, códigos de barras, inventario y migraciones, priorizar pruebas determinísticas.
- Ejecutar los tests del backend y los checks del frontend que correspondan.
- Ejecutar `npm run lint` y `npm run build` para cambios de frontend.
- Para cambios de empaquetado, ejecutar el proceso de release y verificar el instalador en Windows.
- Si una validación no puede ejecutarse, informar el motivo exacto. Nunca declarar que pasó una prueba que no se ejecutó.

No considerar terminado un cambio únicamente porque compila o porque el agente no detecta errores visuales.

## 11. OpenSpec y documentación

OpenSpec es el proceso de especificación del proyecto.

Para cambios funcionales o técnicos relevantes:

1. Definir problema, objetivo y alcance.
2. Documentar requisitos y escenarios de aceptación en `proposal.md`.
3. Describir arquitectura, decisiones y alternativas en `design.md` cuando corresponda.
4. Dividir el trabajo en tareas verificables en `tasks.md`.
5. Implementar respetando la especificación aprobada.
6. Actualizar documentación y marcar tareas únicamente cuando estén realmente completadas.

No modificar una especificación aprobada de forma incompatible sin explicar el motivo y actualizar el change correspondiente.

No marcar tareas como terminadas por haber creado archivos vacíos, stubs o código sin probar.

## 12. Empaquetado, instalación y actualizaciones

- `VERSION` es la única fuente de versión para el ejecutable, el nombre del instalador y `/api/system/status`.
- Nunca cambiar el `AppId` de `installer/EscanApp.iss`: permite actualizaciones in-place que preservan los datos en `%LOCALAPPDATA%\EscanApp`.
- `pos.spec` utiliza modo onedir y requiere `Frontend/dist`.
- El bundle actual incluye `Frontend/dist`, `Modelfiles/`, `VERSION` y `Backend/migrations` (el build falla si falta esta última).
- Ya no se incluye `installer/seed/pos.db`: el esquema lo crea la migración base.
- El release actual es exclusivo de Windows y usa PyInstaller + Inno Setup 6.
- `scripts/build_release.ps1` requiere que Python, Node e ISCC estén disponibles y debe fallar claramente si falta alguno.
- No modificar silenciosamente rutas de instalación, directorios de datos, identificadores del instalador ni reglas de actualización.
- El desinstalador y las actualizaciones deben preservar los datos del comercio, salvo que el usuario solicite expresamente eliminarlos.
- Toda nueva dependencia o archivo necesario en runtime debe incluirse y probarse en el paquete final; que funcione en desarrollo no garantiza que funcione empaquetado.
- Probar el instalador en una máquina o entorno Windows limpio y probar actualización desde una versión anterior.
- No afirmar que el instalador está firmado digitalmente ni que SmartScreen está resuelto sin comprobar la firma y el comportamiento real.

## 13. Archivos generados y control de versiones

Los siguientes elementos están generados o excluidos normalmente de Git:

- `build/`
- `dist/`
- `release/`
- `Frontend/dist/`
- `*.db`
- `*.exe`
- `backups/`

No hay excepciones versionadas de bases de datos: `installer/seed/pos.db` fue retirado. No cambiar estas reglas sin revisar el impacto en el empaquetado y en los datos.

No incluir bases de datos reales, archivos de clientes, logs sensibles, credenciales ni builds locales en commits.

## 14. Flujo de trabajo, Git y releases

- Trabajar en una rama de trabajo; no hacer commits directamente sobre la rama principal salvo autorización explícita.
- Mantener los cambios acotados a la tarea.
- No sobrescribir cambios locales del usuario ni descartar trabajo existente.
- Antes de modificar archivos, revisar `git status` y respetar cambios sin commit.
- No ejecutar comandos destructivos de Git (`reset --hard`, `clean -fd`, force push, rebase destructivo) sin autorización explícita.
- No publicar releases ni desplegar a producción sin aprobación humana explícita.
- Los releases deben ser reproducibles y estar asociados a una versión/tag identificable.
- Si existe CI configurado, respetar sus checks. No deshabilitar validaciones para hacer pasar un build.

## 15. Comunicación y entrega de tareas

Al finalizar una tarea, informar en español y de forma concreta:

1. Qué se modificó y por qué.
2. Archivos creados, modificados o eliminados.
3. Decisiones técnicas relevantes y supuestos realizados.
4. Pruebas y comandos ejecutados, con su resultado real.
5. Qué no se pudo probar y por qué.
6. Riesgos, limitaciones o tareas pendientes.
7. Si se actualizó OpenSpec y qué tareas quedaron completadas.

No ocultar errores, advertencias, deuda técnica ni cambios fuera del alcance.
No declarar una tarea terminada si quedan errores conocidos que afectan su aceptación.

## 16. Prioridades para decisiones técnicas

Ante varias soluciones posibles, priorizar en este orden:

1. No perder ni corromper datos del comercio.
2. Exactitud de ventas, importes y operaciones críticas.
3. Estabilidad en Windows y compatibilidad con instalaciones existentes.
4. Facilidad de uso para el kiosquero.
5. Mantenibilidad y simplicidad de la arquitectura.
6. Rendimiento en hardware modesto.
7. Costo operativo y facilidad de soporte.

No agregar complejidad, microservicios, infraestructura cloud o nuevas tecnologías si una solución local más simple cumple los requisitos.

## 17. Principio final

EscanApp es un producto que puede manejar dinero y datos reales. La seguridad de la información, la integridad de las ventas y la continuidad operativa tienen prioridad sobre la velocidad de implementación.

Si una instrucción, requerimiento o cambio parece poner en riesgo esos principios, detenerse, explicar el riesgo y solicitar una decisión antes de continuar.
