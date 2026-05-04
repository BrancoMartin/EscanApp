# pos.spec
import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Incluye el frontend buildeado
        ('Frontend/dist', 'Frontend/dist'),
        # Incluye la carpeta del backend completa
        ('Backend', 'Backend'),
    ],
   hiddenimports=[
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.ext.declarative',      
    'sqlalchemy.orm',                  
    'webview',
],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='POS',
    debug=False,
    strip=False,
    upx=True,
    console=False,   
)