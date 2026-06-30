param(
    [ValidateSet("dev", "desktop", "backend", "frontend")]
    [string]$Mode = "dev"
)

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "Backend"
$FrontendDir = Join-Path $RootDir "Frontend"
$VenvDir = Join-Path $RootDir ".venv"

function Write-Step {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "`n>> $Message" -ForegroundColor $Color
}

function Wait-Health {
    Write-Step "Esperando que el backend esté listo..." "Yellow"
    $ok = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 1
            if ($r.StatusCode -eq 200) { $ok = $true; break }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    if (-not $ok) {
        Write-Host "El backend no respondió después de 15 segundos." -ForegroundColor Red
        exit 1
    }
    Write-Host "Backend listo!" -ForegroundColor Green
}

function Start-Backend {
    Write-Step "Iniciando backend (uvicorn + FastAPI)" "Green"

    if (-not (Test-Path (Join-Path $VenvDir "Scripts\python.exe"))) {
        Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
        python -m venv $VenvDir
    }

    & (Join-Path $VenvDir "Scripts\Activate.ps1")
    pip install -r (Join-Path $RootDir "requirements.txt") -q

    $env:PYTHONPATH = $RootDir
    $job = Start-Job -ScriptBlock {
        param($bd, $rd)
        Set-Location $rd
        $env:PYTHONPATH = $rd
        & (Join-Path $rd ".venv\Scripts\python.exe") -m uvicorn Backend.api.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
    } -ArgumentList $BackendDir, $RootDir

    return $job
}

function Start-Frontend {
    Write-Step "Iniciando frontend (Vite + React)" "Green"
    Set-Location $FrontendDir
    $job = Start-Job -ScriptBlock {
        param($fd)
        Set-Location $fd
        npm run dev
    } -ArgumentList $FrontendDir
    return $job
}

$jobs = @()

try {
    switch ($Mode) {
        "dev" {
            Write-Host "🚀 Modo desarrollo: backend + frontend" -ForegroundColor Magenta
            $jobs += Start-Backend
            Wait-Health
            $jobs += Start-Frontend

            Write-Host "`n✅ Todo corriendo:" -ForegroundColor Green
            Write-Host "   Backend API: http://127.0.0.1:8000" -ForegroundColor Cyan
            Write-Host "   Frontend:    http://127.0.0.1:5173 (Vite)" -ForegroundColor Cyan
            Write-Host "   Docs API:    http://127.0.0.1:8000/docs" -ForegroundColor Cyan
            Write-Host "`nPresioná Ctrl+C para detener todo.`n" -ForegroundColor Yellow

            while ($true) {
                $jobs | ForEach-Object {
                    if ($_.State -eq "Failed") {
                        Receive-Job $_
                        Write-Host "Un proceso falló. Saliendo..." -ForegroundColor Red
                        exit 1
                    }
                }
                Start-Sleep 2
            }
        }

        "desktop" {
            Write-Host "🖥️ Modo desktop (backend + ventana nativa)" -ForegroundColor Magenta
            & (Join-Path $VenvDir "Scripts\Activate.ps1")
            pip install -r (Join-Path $RootDir "requirements.txt") -q
            $env:PYTHONPATH = $RootDir
            Set-Location $RootDir
            & (Join-Path $VenvDir "Scripts\python.exe") main.py
        }

        "backend" {
            Write-Host "⚙️ Solo backend" -ForegroundColor Magenta
            $jobs += Start-Backend
            Wait-Health
            Write-Host "`n✅ Backend corriendo en http://127.0.0.1:8000" -ForegroundColor Green
            Write-Host "   Presioná Ctrl+C para detener." -ForegroundColor Yellow
            while ($true) { Start-Sleep 2 }
        }

        "frontend" {
            Write-Host "🎨 Solo frontend" -ForegroundColor Magenta
            $jobs += Start-Frontend
            Write-Host "`n✅ Frontend iniciado. Presioná Ctrl+C para detener." -ForegroundColor Yellow
            while ($true) { Start-Sleep 2 }
        }
    }
}
finally {
    Write-Step "Deteniendo procesos..." "Red"
    $jobs | ForEach-Object {
        if ($_.State -eq "Running") { Stop-Job $_ }
        Remove-Job $_ -Force -ErrorAction SilentlyContinue
    }
}
