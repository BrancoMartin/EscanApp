<#
    EscanApp - Build completo del release.

    Un solo comando hace TODO:

        1. Verifica que esten las herramientas (Node, Python, Inno Setup).
        2. Limpia los artefactos de builds anteriores.
        3. Instala las dependencias de Python y de Node.
        4. Compila el frontend React  ->  Frontend/dist
        5. Empaqueta con PyInstaller  ->  dist/EscanApp/
        6. Compila el instalador      ->  release/EscanAppSetup-<version>.exe

    No se invoca directamente: usa scripts\build_release.bat (doble clic).

    Falla RUIDOSAMENTE en cualquier paso. Nunca produce un instalador a partir
    de un build parcial: mas vale no tener release que tener uno roto.
#>

[CmdletBinding()]
param(
    # Saltear la compilacion del frontend (util al iterar solo sobre el backend).
    [switch]$SkipFrontend,
    # Saltear la instalacion de dependencias (util cuando ya estan).
    [switch]$SkipDeps
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root      = Split-Path -Parent $ScriptDir

$AppName    = 'EscanApp'
$DistDir    = Join-Path $Root 'dist'
$BuildDir   = Join-Path $Root 'build'
$ReleaseDir = Join-Path $Root 'release'
$FrontendDir = Join-Path $Root 'Frontend'
$IssFile    = Join-Path $Root 'installer\EscanApp.iss'

$startedAt = Get-Date

function Write-Step {
    param([string]$Message)
    Write-Host ''
    Write-Host ('=' * 70) -ForegroundColor DarkCyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host ('=' * 70) -ForegroundColor DarkCyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Fail {
    param([string]$Message, [string]$Hint)
    Write-Host ''
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
    if ($Hint) {
        Write-Host "          $Hint" -ForegroundColor Yellow
    }
    Write-Host ''
    exit 1
}

function Assert-LastExit {
    param([string]$What)
    if ($LASTEXITCODE -ne 0) {
        Fail "$What fallo (codigo $LASTEXITCODE)." 'El release NO se genero. Revisa el error de arriba.'
    }
}

# ---------------------------------------------------------------------------
# 0. Version
# ---------------------------------------------------------------------------

Write-Step 'EscanApp - Build de release'

$VersionFile = Join-Path $Root 'VERSION'
if (-not (Test-Path $VersionFile)) {
    Fail 'No existe el archivo VERSION en la raiz del proyecto.' 'Crealo con el numero de version, por ejemplo: 1.0.0'
}

$Version = (Get-Content $VersionFile -Raw).Trim()
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Fail "La version '$Version' no tiene el formato MAJOR.MINOR.PATCH." 'Ejemplo valido: 1.0.0'
}
Write-Ok "Version a construir: $Version"

# ---------------------------------------------------------------------------
# 1. Herramientas
# ---------------------------------------------------------------------------

Write-Step '1/6  Verificando herramientas'

# Python: preferimos el venv del proyecto para construir con las versiones fijadas.
$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
if (Test-Path $VenvPython) {
    $Python = $VenvPython
    Write-Ok "Python (entorno virtual del proyecto): $Python"
} else {
    $found = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $found) {
        Fail 'No se encontro Python.' 'Instalalo desde https://www.python.org/downloads/ y marca "Add python.exe to PATH".'
    }
    $Python = $found.Source
    Write-Ok "Python: $Python"
}

if (-not $SkipFrontend) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($null -eq $npm) {
        Fail 'No se encontro npm (Node.js).' 'Instala Node.js LTS desde https://nodejs.org/'
    }
    Write-Ok "npm: $($npm.Source)"
}

# Inno Setup: en el PATH o en alguna de sus ubicaciones tipicas. Se contempla
# la instalacion por-usuario (%LOCALAPPDATA%\Programs), que es donde lo deja
# winget y donde termina cuando se instala sin permisos de administrador.
$Iscc = $null
$isccCommand = Get-Command 'iscc' -ErrorAction SilentlyContinue
if ($null -ne $isccCommand) {
    $Iscc = $isccCommand.Source
} else {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { $Iscc = $candidate; break }
    }
}
if ($null -eq $Iscc) {
    Fail 'No se encontro Inno Setup (ISCC.exe).' 'Instala Inno Setup 6 desde https://jrsoftware.org/isdl.php y volve a correr el build.'
}
Write-Ok "Inno Setup: $Iscc"

# ---------------------------------------------------------------------------
# 2. Limpieza
# ---------------------------------------------------------------------------

Write-Step '2/6  Limpiando builds anteriores'

foreach ($path in @($DistDir, $BuildDir, (Join-Path $FrontendDir 'dist'))) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force
        Write-Ok "Borrado: $path"
    }
}

if (-not (Test-Path $ReleaseDir)) {
    New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
}

# ---------------------------------------------------------------------------
# 3. Dependencias
# ---------------------------------------------------------------------------

if ($SkipDeps) {
    Write-Step '3/6  Dependencias (SALTEADO)'
} else {
    Write-Step '3/6  Instalando dependencias'

    Write-Host '  Python...' -ForegroundColor Gray
    & $Python -m pip install --disable-pip-version-check --quiet -r (Join-Path $Root 'requirements-build.txt')
    Assert-LastExit 'pip install'
    Write-Ok 'Dependencias de Python instaladas'

    if (-not $SkipFrontend) {
        Write-Host '  Node...' -ForegroundColor Gray
        Push-Location $FrontendDir
        try {
            # npm ci es reproducible, pero exige un package-lock.json coherente.
            if (Test-Path (Join-Path $FrontendDir 'package-lock.json')) {
                & npm ci --silent
                if ($LASTEXITCODE -ne 0) {
                    Write-Host '  npm ci fallo; probando npm install...' -ForegroundColor Yellow
                    & npm install --silent
                    Assert-LastExit 'npm install'
                }
            } else {
                & npm install --silent
                Assert-LastExit 'npm install'
            }
        } finally {
            Pop-Location
        }
        Write-Ok 'Dependencias de Node instaladas'
    }
}

# ---------------------------------------------------------------------------
# 4. Frontend
# ---------------------------------------------------------------------------

if ($SkipFrontend) {
    Write-Step '4/6  Frontend (SALTEADO)'
    if (-not (Test-Path (Join-Path $FrontendDir 'dist'))) {
        Fail 'Se salteo el frontend pero no existe Frontend/dist.' 'Corre el build sin -SkipFrontend al menos una vez.'
    }
} else {
    Write-Step '4/6  Compilando el frontend (React + Vite)'

    Push-Location $FrontendDir
    try {
        & npm run build
        Assert-LastExit 'npm run build'
    } finally {
        Pop-Location
    }

    $indexHtml = Join-Path $FrontendDir 'dist\index.html'
    if (-not (Test-Path $indexHtml)) {
        Fail 'El build del frontend no genero Frontend/dist/index.html.' 'Revisa la salida de Vite.'
    }
    Write-Ok 'Frontend compilado en Frontend/dist'
}

# ---------------------------------------------------------------------------
# 5. PyInstaller
# ---------------------------------------------------------------------------

Write-Step '5/6  Empaquetando la aplicacion (PyInstaller)'

Push-Location $Root
try {
    & $Python -m PyInstaller --noconfirm --clean (Join-Path $Root 'pos.spec')
    Assert-LastExit 'PyInstaller'
} finally {
    Pop-Location
}

$AppExe = Join-Path $DistDir "$AppName\$AppName.exe"
if (-not (Test-Path $AppExe)) {
    Fail "PyInstaller no genero $AppExe." 'Revisa la salida de arriba.'
}
Write-Ok "Ejecutable: $AppExe"

# Chequeo de que los recursos criticos quedaron dentro del bundle: sin esto, el
# instalador saldria "bien" y la app fallaria en la PC del cliente.
$internal = Join-Path $DistDir "$AppName\_internal"
$mustExist = @(
    (Join-Path $internal 'Frontend\dist\index.html'),
    (Join-Path $internal 'Modelfiles\CualifiquerIntent'),
    (Join-Path $internal 'VERSION')
)
foreach ($required in $mustExist) {
    if (-not (Test-Path $required)) {
        Fail "Falta un recurso en el bundle: $required" 'Revisa la seccion datas de pos.spec.'
    }
}
Write-Ok 'Frontend, Modelfiles y VERSION verificados dentro del bundle'

# ---------------------------------------------------------------------------
# 6. Instalador
# ---------------------------------------------------------------------------

Write-Step '6/6  Generando el instalador (Inno Setup)'

$vendored = Join-Path $Root 'installer\vendor\OllamaSetup.exe'
if (Test-Path $vendored) {
    Write-Host '  Modo OFFLINE: se incluye OllamaSetup.exe en el instalador.' -ForegroundColor Yellow
} else {
    Write-Host '  Modo ONLINE: Ollama se descarga durante la instalacion.' -ForegroundColor Gray
}

& $Iscc "/DAppVersion=$Version" $IssFile
Assert-LastExit 'Inno Setup (ISCC)'

$Installer = Join-Path $ReleaseDir "EscanAppSetup-$Version.exe"
if (-not (Test-Path $Installer)) {
    Fail "Inno Setup no genero $Installer." 'Revisa la salida de ISCC.'
}

# Copia con el nombre "de siempre", que es el que se publica para descargar.
$Stable = Join-Path $ReleaseDir 'EscanAppSetup.exe'
Copy-Item -Path $Installer -Destination $Stable -Force

# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------

$elapsed = (Get-Date) - $startedAt
$sizeMb = [math]::Round((Get-Item $Installer).Length / 1MB, 1)

Write-Host ''
Write-Host ('=' * 70) -ForegroundColor Green
Write-Host "  RELEASE $Version LISTO" -ForegroundColor Green
Write-Host ('=' * 70) -ForegroundColor Green
Write-Host ''
Write-Host "  Instalador : $Installer"
Write-Host "  Copia      : $Stable"
Write-Host "  Tamano     : $sizeMb MB"
Write-Host "  Tiempo     : $([math]::Round($elapsed.TotalMinutes, 1)) min"
Write-Host ''
Write-Host '  Esto es lo unico que el cliente descarga. Doble clic y a usar.' -ForegroundColor Gray
Write-Host ''

exit 0
