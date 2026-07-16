# -*- mode: python ; coding: utf-8 -*-
"""Empaquetado de EscanApp con PyInstaller.

Se construye en modo ONEDIR (COLLECT), no onefile. El onefile descomprime ~25 MB
a %TEMP% en CADA arranque: segundos de espera y basura si el proceso se mata.
Como el producto se instala (no se corre portable), onedir es el modo correcto:
el .exe arranca directo desde su carpeta, y la compresion la hace el instalador
(Inno usa LZMA2), asi que el Setup final pesa practicamente lo mismo.

Tampoco se empaqueta la carpeta Backend entera como "data" (lo que hacia el spec
anterior): eso arrastraba openspec/ (specs internas), CurrencyMicroservice/
(proyecto C#/.NET que ni siquiera corre dentro del .exe), .claude/ y el .env con
configuracion interna. Los modulos Python se recogen por import; como datos se
incluye solo lo que el runtime necesita leer del disco.
"""

import os

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_submodules

SPEC_DIR = os.path.abspath(SPECPATH)

APP_NAME = "EscanApp"
ICON = os.path.join(SPEC_DIR, "icono1.ico")


def read_version():
    try:
        with open(os.path.join(SPEC_DIR, "VERSION"), "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except OSError:
        return "0.0.0"


VERSION = read_version()


def version_tuple(text):
    """'1.2.3' -> (1, 2, 3, 0). Windows exige 4 numeros en el recurso de version."""
    parts = []
    for chunk in text.split("."):
        digits = ""
        for character in chunk:
            if character.isdigit():
                digits += character
        if digits:
            parts.append(int(digits))
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def write_version_resource():
    """Genera el recurso de version de Windows (lo que muestra Propiedades del
    archivo). Ademas de corresponder a un producto comercial, tener metadatos de
    publisher y version es lo que mas reduce los falsos positivos de antivirus
    contra los ejecutables de PyInstaller."""
    numbers = version_tuple(VERSION)
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numbers},
    prodvers={numbers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '0c0a04b0',
        [StringStruct('CompanyName', 'EscanApp'),
         StringStruct('FileDescription', 'EscanApp - Punto de venta con agentes de IA'),
         StringStruct('FileVersion', '{VERSION}'),
         StringStruct('InternalName', '{APP_NAME}'),
         StringStruct('LegalCopyright', 'Copyright (c) EscanApp'),
         StringStruct('OriginalFilename', '{APP_NAME}.exe'),
         StringStruct('ProductName', 'EscanApp'),
         StringStruct('ProductVersion', '{VERSION}')])
    ]),
    VarFileInfo([VarStruct('Translation', [3082, 1200])])
  ]
)
"""
    build_dir = os.path.join(SPEC_DIR, "build")
    os.makedirs(build_dir, exist_ok=True)
    path = os.path.join(build_dir, "version_info.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


VERSION_RESOURCE = write_version_resource()


def data_entries():
    """Recursos de SOLO LECTURA que el runtime necesita leer del disco."""
    entries = []

    # Frontend compilado: lo sirve FastAPI como estaticos.
    frontend_dist = os.path.join(SPEC_DIR, "Frontend", "dist")
    if not os.path.isdir(frontend_dist):
        raise SystemExit(
            "Falta Frontend/dist. Compila el frontend antes de empaquetar:\n"
            "    cd Frontend && npm run build\n"
            "(o usa scripts\\build_release.bat, que lo hace por vos)"
        )
    entries.append((frontend_dist, "Frontend/dist"))

    # Modelfiles: el aprovisionamiento los usa para crear los 9 modelos de IA.
    modelfiles = os.path.join(SPEC_DIR, "Modelfiles")
    if not os.path.isdir(modelfiles):
        raise SystemExit("Falta la carpeta Modelfiles: sin ella no se pueden crear los modelos de IA.")
    entries.append((modelfiles, "Modelfiles"))

    # VERSION: runtime.version() la lee y la reporta en /api/system/status.
    entries.append((os.path.join(SPEC_DIR, "VERSION"), "."))

    # Base de datos inicial (opcional). Si esta, la app la siembra en la carpeta
    # del usuario en su primer arranque; si no, crea el esquema vacio.
    seed_db = os.path.join(SPEC_DIR, "installer", "seed", "pos.db")
    if os.path.isfile(seed_db):
        entries.append((seed_db, "."))

    return entries


hidden = [
    # uvicorn resuelve estos por nombre en runtime: PyInstaller no los ve.
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.ext.declarative",
    "sqlalchemy.orm",
    "webview",
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
]

# Los modulos propios y los de langchain se descubren por import, pero langchain
# resuelve varias piezas dinamicamente: las recogemos explicitamente.
hidden += collect_submodules("Backend")
hidden += collect_submodules("langchain_ollama")

a = Analysis(
    ["main.py"],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=data_entries(),
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Nada de esto corre en runtime y suman decenas de MB al instalador.
        "tkinter",
        "PyInstaller",
        "pytest",
        "IPython",
        "matplotlib",
        "numpy",
        "pandas",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # onedir: los binarios los junta COLLECT
    name=APP_NAME,
    debug=False,
    strip=False,
    upx=False,               # UPX dispara falsos positivos de antivirus
    console=False,
    icon=ICON,
    version=VERSION_RESOURCE,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)
