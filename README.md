# EscanApp

Sistema de venta con escaneo de codigo de barras,
desarrollado para pequeños comercios.
Permite gestionar productos, registrar ventas y generar tickets de forma fácil y rapida.

Incluye un **asistente de inteligencia artificial** que corre **localmente** en la PC del comercio
(9 agentes especializados sobre Ollama): permite crear productos, ajustar precios, gestionar
atributos y consultar el inventario conversando en lenguaje natural.

## FUNCIONALIDADES:
**Gestion de productos** : El usuario carga manualmente sus productos mediante un formulario, escaneando su codigo de barras
para guardarlo en la base de datos.

**Escaneo en caja**: Al atender a un cliente el usuario escanea los productos, y se genera un ticket en tiempo
real con el detalle de la compra.

**Cierre de venta**: El usuario cierra la venta mediante un boton "cerrar venta" y esta queda guardada en la base de datos como closed.

**Historial de ventas**: Se pueden consultar las ventas realizadas en las ultimas 24 horas. Las ventas anteriores a las 24 horas no se muestran.

**Asistente de IA**: 9 agentes locales para crear productos, ajustar precios (aumentos y descuentos),
detectar y asignar atributos, y responder consultas sobre el inventario.

## TECNOLOGIAS UTILIZADAS:

**Frontend**: React + Vite

**Backend**: Fast API (python)

**Base de datos**: SQLite

**ORM**: SQLAlchemy

**Escritorio**: pywebview

**IA**: Ollama + LangChain (9 modelos derivados de `qwen2.5:0.5b`)

**Empaquetado**: PyInstaller + Inno Setup

---

## INSTALACION Y USO (Clientes)

1. Descargá **`EscanAppSetup.exe`** de la sección Releases.
2. Doble clic.
3. Esperá unos minutos y listo.

**No necesitás instalar nada más.** Ni Python, ni Node, ni Ollama, ni abrir una consola.
El instalador se encarga de todo: instala la aplicación, instala el motor de IA si no lo tenés,
descarga el modelo base y crea los 9 agentes.

> La primera instalación tarda entre 5 y 15 minutos porque descarga el modelo de IA (~400 MB).
> Necesita conexión a internet **solo durante la instalación**. Después la app funciona offline:
> los modelos corren en tu propia PC y tus datos nunca salen de ella.

Si en el momento de instalar no tenés internet, la instalación igual termina bien: la aplicación
descarga lo que falte sola, la primera vez que la abras con conexión.

### Tus datos

Se guardan en `%LOCALAPPDATA%\EscanApp` (base de datos, logs y Modelfiles).
Al desinstalar, EscanApp te pregunta si querés conservarlos.

---

## DESARROLLO

```bash
# Backend + ventana de escritorio
python main.py

# Solo el servidor (para probar la API)
python main.py --no-window

# Frontend en modo desarrollo (hot reload en :5173)
cd Frontend && npm run dev
```

Requiere Ollama corriendo con los 9 modelos. Si falta alguno, la app lo crea sola al arrancar
(ver `Backend/agent/provisioning.py`).

## PUBLICAR UNA VERSION

```
1. Editar el archivo VERSION      (ej: 1.0.1)
2. Doble clic en scripts\build_release.bat
3. Subir release\EscanAppSetup.exe
```

El detalle completo está en **[docs/RELEASE.md](docs/RELEASE.md)**.

## SPECS

El proyecto es *spec-driven*: todo cambio se documenta primero en `Backend/openspec/`.

```bash
cd Backend && openspec list
```
