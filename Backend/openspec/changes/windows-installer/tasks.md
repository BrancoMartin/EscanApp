## 1. Corrección de defectos que bloquean el empaquetado

- [x] 1.1 Completar `requirements.txt` con `langchain`, `langchain-ollama` y `pyinstaller` (faltaban; un build limpio falla)
- [x] 1.2 Unificar el modelo base en `qwen2.5:0.5b` (`Backend/.env` decía `gemma3:4b`, 3.3 GB innecesarios)
- [x] 1.3 Quitar el BOM UTF-8 de `Modelfiles/GeneralConsultant` (rompe el parseo de `ollama create`)
- [x] 1.4 Convertir `Backend/.env` en `Backend/.env.example` y dejar de empaquetar el `.env`

## 2. Rutas de runtime (datos de usuario escribibles)

- [x] 2.1 Crear `Backend/runtime.py` con `resource_dir()`, `data_dir()`, `log_dir()`, `db_path()`, `modelfiles_dir()`
- [x] 2.2 `Backend/database.py`: la DB pasa a `%LOCALAPPDATA%\EscanApp\pos.db` cuando está congelada
- [x] 2.3 Siembra de la base inicial en el primer arranque de cada usuario
- [x] 2.4 `Backend/api/app.py`: resolver `Frontend/dist` vía `runtime.resource_dir()`

## 3. Aprovisionamiento y autorreparación del entorno de IA

- [x] 3.1 Crear `Backend/agent/provisioning.py`: detectar Ollama, listar modelos, pull del base, create de los faltantes (idempotente)
- [x] 3.2 Ejecutar la verificación en el arranque, en hilo daemon, sin bloquear la UI
- [x] 3.3 Endpoint `GET /api/system/status` con estado de Ollama, modelos faltantes y progreso
- [x] 3.4 Ocultar la ventana de consola de los subprocesos de Ollama en Windows (`CREATE_NO_WINDOW`)

## 4. Empaquetado con PyInstaller

- [x] 4.1 Reescribir `pos.spec`: onedir (`COLLECT`) en vez de onefile
- [x] 4.2 Filtrar `datas`: excluir `openspec/`, `CurrencyMicroservice/`, `.claude/`, `.env`, `__pycache__`
- [x] 4.3 Incluir `Frontend/dist`, `Modelfiles/` y la `pos.db` semilla
- [x] 4.4 Recurso de versión de Windows + icono, generados desde `VERSION`
- [x] 4.5 `hiddenimports` completos para langchain / langchain-ollama

## 5. Instalador Inno Setup

- [x] 5.1 Crear `installer/EscanApp.iss` con `AppId` fijo, icono, licencia, versión, publisher
- [x] 5.2 Accesos directos (Menú Inicio siempre, Escritorio opcional) y desinstalador
- [x] 5.3 Ejecutar `postinstall.ps1` tras la instalación, con progreso visible
- [x] 5.4 Abrir EscanApp al finalizar la instalación
- [x] 5.5 Desinstalador: preguntar si borrar los datos de `%LOCALAPPDATA%\EscanApp`
- [x] 5.6 `installer/LICENSE.txt`

## 6. Post-instalación (aprovisionamiento de Ollama)

- [x] 6.1 `installer/postinstall.ps1`: detectar Ollama (PATH + rutas conocidas + registro)
- [x] 6.2 Instalar Ollama en silencio solo si falta (vendor local si existe, si no descarga oficial)
- [x] 6.3 Esperar a que `http://127.0.0.1:11434` responda, con timeout acotado
- [x] 6.4 `ollama pull qwen2.5:0.5b` (solo si falta)
- [x] 6.5 `ollama create` de los 9 modelos desde los Modelfiles (solo los faltantes)
- [x] 6.6 No abortar la instalación si no hay internet: avisar y delegar en la autorreparación del arranque

## 7. Build de un solo comando

- [x] 7.1 Crear `VERSION` (1.0.0) como fuente de verdad
- [x] 7.2 `scripts/build_release.ps1`: verificar herramientas, limpiar, `npm ci` + `npm run build`, PyInstaller, ISCC
- [x] 7.3 `scripts/build_release.bat` como envoltorio de un solo clic
- [x] 7.4 Salida en `release/EscanAppSetup-<version>.exe`
- [x] 7.5 Fallar con mensaje claro si falta Node, Python o Inno Setup

## 8. Documentación

- [x] 8.1 `docs/RELEASE.md`: cómo publicar una versión nueva y cómo hacer la variante offline
- [x] 8.2 Actualizar `README.md` con el flujo de instalación del usuario final

## 9. Verificación

- [x] 9.1 `python -m py_compile` de todos los archivos Python tocados
- [x] 9.2 `npm run build` del frontend sin errores
- [x] 9.3 Build completo end-to-end: `scripts\build_release.bat` genera el instalador
- [x] 9.4 Verificar que la app congelada escribe la DB en `%LOCALAPPDATA%\EscanApp`
- [x] 9.5 Verificar que el aprovisionamiento es idempotente (segunda corrida no re-descarga nada)
- [x] 9.6 `openspec validate windows-installer`
