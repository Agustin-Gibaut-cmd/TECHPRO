# ==============================================================================
# TECHPRO - Script de Validación Integral
# Ejecuta comprobaciones del backend (Django) y frontend (Angular)
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [string]$DbEngine = "sqlite"
)

$ErrorActionPreference = "Continue"

# Rutas del repositorio
$Root = (Resolve-Path "$PSScriptRoot\..").Path
$ServerDir = Join-Path $Root "server"
$ClientDir = Join-Path $Root "client"

# 1. Detección de Python
$Python = if (Test-Path "$ServerDir\.venv\Scripts\python.exe") {
    "$ServerDir\.venv\Scripts\python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    (Get-Command python).Source
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    (Get-Command py).Source
} else {
    Write-Error "No se encontró Python. Instalá Python o creá el entorno en server\.venv."
    exit 1
}

# 2. Detección de Node/npm
$Npm = if (Get-Command npm.cmd -ErrorAction SilentlyContinue) {
    (Get-Command npm.cmd).Source
} elseif (Get-Command npm -ErrorAction SilentlyContinue) {
    (Get-Command npm).Source
} else {
    Write-Error "No se encontró npm. Instalá Node.js y npm."
    exit 1
}

# 3. Base de datos para pruebas (usa SQLite por defecto para agilidad local)
if (-not $env:DB_ENGINE) {
    $env:DB_ENGINE = $DbEngine
}

$Failures = @()

function Run-Step {
    param(
        [string]$Title,
        [string]$WorkDir,
        [string]$Command,
        [string[]]$Args
    )

    Write-Host "`n>>> $Title" -ForegroundColor Cyan
    Push-Location $WorkDir
    try {
        & $Command $Args
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] $Title" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] $Title (Código: $LASTEXITCODE)" -ForegroundColor Red
            $script:Failures += $Title
        }
    } catch {
        Write-Host "[EXCEPCIÓN] $_" -ForegroundColor Red
        $script:Failures += $Title
    } finally {
        Pop-Location
    }
}

# 4. Comprobaciones de Backend
if (-not $SkipBackend) {
    $Coverage = Join-Path $ServerDir ".venv\Scripts\coverage.exe"
    Run-Step -Title "Django System Check" -WorkDir $ServerDir -Command $Python -Args @("manage.py", "check")
    Run-Step -Title "Django Migration Consistency" -WorkDir $ServerDir -Command $Python -Args @("manage.py", "makemigrations", "--check", "--dry-run")

    if (Test-Path $Coverage) {
        Run-Step -Title "Django API Tests + Coverage" -WorkDir $ServerDir -Command $Coverage -Args @("run", "--branch", "manage.py", "test")
        Run-Step -Title "Coverage Report" -WorkDir $ServerDir -Command $Coverage -Args @("report", "-m")
    } else {
        Run-Step -Title "Django API Tests" -WorkDir $ServerDir -Command $Python -Args @("manage.py", "test", "tests")
    }
}

# 5. Comprobaciones de Frontend
if (-not $SkipFrontend) {
    if (Test-Path "$ClientDir\node_modules") {
        Run-Step -Title "Angular Component Tests" -WorkDir $ClientDir -Command $Npm -Args @("test", "--", "--watch=false")
        Run-Step -Title "Angular Production Build" -WorkDir $ClientDir -Command $Npm -Args @("run", "build")
    } else {
        Write-Host "`n[AVISO] Se omite el frontend porque no existe client\node_modules (ejecutá 'npm install' en client)." -ForegroundColor Yellow
    }
}

# 6. Comprobación de formato Git
$Git = Get-Command git -ErrorAction SilentlyContinue
if ($Git) {
    Run-Step -Title "Git Whitespace Check" -WorkDir $Root -Command $Git.Source -Args @("diff", "--check")
}

# 7. Resumen de resultados
Write-Host "`n" + ("=" * 55)
if ($Failures.Count -eq 0) {
    Write-Host "TODAS LAS VALIDACIONES PASARON EXITOSAMENTE." -ForegroundColor Green
    Write-Host ("=" * 55) + "`n"
    exit 0
} else {
    Write-Host "VALIDACIÓN INCOMPLETA. Fallaron los siguientes pasos:" -ForegroundColor Red
    foreach ($item in $Failures) {
        Write-Host " - $item" -ForegroundColor Red
    }
    Write-Host ("=" * 55) + "`n"
    exit 1
}
