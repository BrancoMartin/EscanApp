<#
    EscanApp - Aprovisionamiento del entorno de IA (post-instalacion)

    Lo ejecuta el instalador de Inno Setup despues de copiar los archivos.
    Deja la maquina del usuario lista para usar la app:

        1. Detecta si Ollama ya esta instalado (y NO lo reinstala si esta).
        2. Si falta, lo instala en silencio: usa la copia vendorizada si existe,
           si no la descarga del sitio oficial.
        3. Espera a que el servidor de Ollama quede operativo.
        4. Descarga el modelo base (solo si falta).
        5. Crea los 9 modelos personalizados desde los Modelfiles (solo los que faltan).

    IMPORTANTE: este script NUNCA aborta la instalacion. Si no hay internet o algo
    falla, avisa y termina con exito igual: la aplicacion vuelve a intentar el
    aprovisionamiento sola en cada arranque (Backend/agent/provisioning.py). Una
    instalacion a medias se repara sola en vez de dejar al usuario a pie.
#>

[CmdletBinding()]
param(
    # Carpeta donde quedo instalada la aplicacion ({app} de Inno Setup).
    [Parameter(Mandatory = $true)]
    [string]$InstallDir
)

$ErrorActionPreference = 'Continue'

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

# Modelo base del que derivan los 9 modelos (la directiva FROM de los Modelfiles).
$BaseModel = 'qwen2.5:0.5b'

# tag de Ollama -> nombre del Modelfile. Misma lista que crear_modelos.bat.
$Models = [ordered]@{
    'cualifiquer-intent'            = 'CualifiquerIntent'
    'create-product'                = 'CreateProduct'
    'increase-detector'             = 'IncreaseDetector'
    'attribute-extractor'           = 'AttributeExtractor'
    'attribute-classifier'          = 'AttributeClassifier'
    'attribute-resolver'            = 'AttributeResolver'
    'incomplet-handler'             = 'IncompletHandler'
    'general-consultant'            = 'GeneralConsultant'
    'create-categories-by-products' = 'CreateCategories'
}

$OllamaApi = 'http://127.0.0.1:11434'
$OllamaDownloadUrl = 'https://ollama.com/download/OllamaSetup.exe'

$LogDir = Join-Path $env:LOCALAPPDATA 'EscanApp\logs'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogFile = Join-Path $LogDir 'install.log'

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

function Write-Log {
    param([string]$Message, [string]$Color = 'Gray')
    $line = "[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $Message
    Write-Host $line -ForegroundColor $Color
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

function Write-Step {
    param([string]$Message)
    Write-Host ''
    Write-Host "== $Message" -ForegroundColor Cyan
    Add-Content -Path $LogFile -Value "== $Message" -Encoding utf8
}

function Find-Ollama {
    # El PATH del proceso puede no tener Ollama todavia (recien instalado), asi
    # que ademas del PATH miramos las rutas donde lo deja el instalador oficial.
    $command = Get-Command 'ollama' -ErrorAction SilentlyContinue
    if ($null -ne $command) { return $command.Source }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'),
        (Join-Path $env:ProgramFiles 'Ollama\ollama.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Test-OllamaServer {
    try {
        $null = Invoke-RestMethod -Uri "$OllamaApi/api/tags" -TimeoutSec 5 -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Get-InstalledModels {
    try {
        $response = Invoke-RestMethod -Uri "$OllamaApi/api/tags" -TimeoutSec 10 -ErrorAction Stop
    } catch {
        return $null
    }

    $names = New-Object System.Collections.Generic.HashSet[string]
    foreach ($model in $response.models) {
        $name = $model.name
        if ([string]::IsNullOrWhiteSpace($name)) { continue }
        [void]$names.Add($name)
        if ($name.EndsWith(':latest')) {
            [void]$names.Add($name.Substring(0, $name.Length - 7))
        }
    }
    return $names
}

function Wait-OllamaServer {
    param([int]$TimeoutSeconds = 120)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-OllamaServer) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Start-OllamaServer {
    param([string]$Binary)

    Write-Log "Levantando el servidor de Ollama..."
    try {
        Start-Process -FilePath $Binary -ArgumentList 'serve' -WindowStyle Hidden -ErrorAction Stop
    } catch {
        Write-Log "No se pudo iniciar el servidor: $($_.Exception.Message)" 'Yellow'
        return $false
    }
    return (Wait-OllamaServer -TimeoutSeconds 60)
}

function Find-ModelfilesDir {
    # PyInstaller 6 (onedir) deja los recursos bajo _internal\. Se contemplan las
    # dos ubicaciones para no depender de un detalle interno de PyInstaller.
    $candidates = @(
        (Join-Path $InstallDir '_internal\Modelfiles'),
        (Join-Path $InstallDir 'Modelfiles')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

# ---------------------------------------------------------------------------
# 1. Ollama: detectar / instalar
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '===========================================================' -ForegroundColor Magenta
Write-Host '  EscanApp - Preparando los agentes de inteligencia artificial' -ForegroundColor Magenta
Write-Host '===========================================================' -ForegroundColor Magenta
Write-Log "Instalacion en: $InstallDir"

Write-Step 'Buscando Ollama'
$ollama = Find-Ollama

if ($null -ne $ollama) {
    Write-Log "Ollama ya esta instalado: $ollama" 'Green'
} else {
    Write-Log 'Ollama no esta instalado en esta PC. Se instalara automaticamente.' 'Yellow'

    # Copia vendorizada (para armar un instalador que funcione sin internet).
    $vendored = Join-Path $InstallDir 'setup\OllamaSetup.exe'
    $setupPath = $null

    if (Test-Path $vendored) {
        Write-Log 'Usando el instalador de Ollama incluido en el producto.'
        $setupPath = $vendored
    } else {
        $setupPath = Join-Path $env:TEMP 'OllamaSetup.exe'
        Write-Step 'Descargando Ollama (puede tardar varios minutos)'
        try {
            $ProgressPreference = 'SilentlyContinue'   # sin esto Invoke-WebRequest es lentisimo
            Invoke-WebRequest -Uri $OllamaDownloadUrl -OutFile $setupPath -UseBasicParsing -ErrorAction Stop
            Write-Log 'Descarga completada.' 'Green'
        } catch {
            Write-Log "No se pudo descargar Ollama: $($_.Exception.Message)" 'Red'
            Write-Log 'EscanApp se instalo igual. Al abrir la app con internet, los agentes se instalan solos.' 'Yellow'
            exit 0
        }
    }

    Write-Step 'Instalando Ollama en silencio'
    try {
        # El instalador de Ollama esta hecho con Inno Setup: acepta /VERYSILENT.
        $process = Start-Process -FilePath $setupPath `
                                 -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' `
                                 -Wait -PassThru -ErrorAction Stop
        Write-Log "Instalador de Ollama finalizado (codigo $($process.ExitCode))."
    } catch {
        Write-Log "Fallo la instalacion de Ollama: $($_.Exception.Message)" 'Red'
        Write-Log 'EscanApp se instalo igual. Al abrir la app, se reintenta solo.' 'Yellow'
        exit 0
    }

    $ollama = Find-Ollama
    if ($null -eq $ollama) {
        Write-Log 'Ollama se instalo pero no se encontro su ejecutable.' 'Red'
        Write-Log 'La aplicacion reintentara sola en el proximo arranque.' 'Yellow'
        exit 0
    }
    Write-Log "Ollama instalado: $ollama" 'Green'
}

# ---------------------------------------------------------------------------
# 2. Esperar a que el servidor este operativo
# ---------------------------------------------------------------------------

Write-Step 'Esperando a que Ollama quede operativo'

if (-not (Test-OllamaServer)) {
    if (-not (Start-OllamaServer -Binary $ollama)) {
        Write-Log 'El servidor de Ollama no respondio a tiempo.' 'Red'
        Write-Log 'La aplicacion reintentara sola en el proximo arranque.' 'Yellow'
        exit 0
    }
}
Write-Log "Ollama operativo en $OllamaApi" 'Green'

# ---------------------------------------------------------------------------
# 3. Modelo base
# ---------------------------------------------------------------------------

$present = Get-InstalledModels
if ($null -eq $present) { $present = New-Object System.Collections.Generic.HashSet[string] }

Write-Step "Modelo base ($BaseModel)"

if ($present.Contains($BaseModel)) {
    Write-Log 'El modelo base ya estaba descargado. Se omite la descarga.' 'Green'
} else {
    Write-Log 'Descargando el modelo base (~400 MB). Esto puede tardar varios minutos...' 'Yellow'
    & $ollama pull $BaseModel
    if ($LASTEXITCODE -ne 0) {
        Write-Log "No se pudo descargar el modelo base (codigo $LASTEXITCODE)." 'Red'
        Write-Log 'La aplicacion reintentara sola en el proximo arranque con internet.' 'Yellow'
        exit 0
    }
    Write-Log 'Modelo base descargado.' 'Green'
    $present = Get-InstalledModels
    if ($null -eq $present) { $present = New-Object System.Collections.Generic.HashSet[string] }
}

# ---------------------------------------------------------------------------
# 4. Los 9 modelos personalizados
# ---------------------------------------------------------------------------

Write-Step 'Creando los 9 agentes de IA'

$modelfilesDir = Find-ModelfilesDir
if ($null -eq $modelfilesDir) {
    Write-Log 'No se encontro la carpeta Modelfiles en la instalacion.' 'Red'
    exit 0
}
Write-Log "Modelfiles: $modelfilesDir"

$created = 0
$skipped = 0
$failed = 0
$total = $Models.Count
$index = 0

foreach ($tag in $Models.Keys) {
    $index++
    $modelfile = Join-Path $modelfilesDir $Models[$tag]

    if (-not (Test-Path $modelfile)) {
        Write-Log "[$index/$total] Falta el Modelfile de '$tag'." 'Red'
        $failed++
        continue
    }

    if ($present.Contains($tag)) {
        Write-Log "[$index/$total] '$tag' ya existe. Se omite." 'DarkGray'
        $skipped++
        continue
    }

    Write-Log "[$index/$total] Creando '$tag'..."
    & $ollama create $tag -f $modelfile
    if ($LASTEXITCODE -eq 0) {
        Write-Log "[$index/$total] '$tag' listo." 'Green'
        $created++
    } else {
        Write-Log "[$index/$total] Fallo la creacion de '$tag' (codigo $LASTEXITCODE)." 'Red'
        $failed++
    }
}

# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '===========================================================' -ForegroundColor Magenta
Write-Log "Agentes creados: $created | ya existentes: $skipped | con error: $failed"

if ($failed -gt 0) {
    Write-Log 'Algunos agentes no se pudieron crear. La aplicacion los reintenta sola al abrirse.' 'Yellow'
} else {
    Write-Log 'Entorno de IA listo. Ya podes usar EscanApp.' 'Green'
}
Write-Host '===========================================================' -ForegroundColor Magenta

# Siempre 0: un fallo de aprovisionamiento no debe hacer fracasar la instalacion.
exit 0
