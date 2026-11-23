$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$serverDirectory = Join-Path $repositoryRoot "server"
$clientDirectory = Join-Path $repositoryRoot "client"
$validationFailures = New-Object "System.Collections.Generic.List[string]"

$localPython = Join-Path $serverDirectory ".venv\Scripts\python.exe"
$pythonPrefix = @()
if (Test-Path $localPython) {
    $pythonExecutable = $localPython
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonExecutable = $pythonCommand.Source
    } else {
        $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
        if (-not $pythonCommand) {
            throw "No se encontró Python. Instalalo o creá server\.venv."
        }
        $pythonExecutable = $pythonCommand.Source
        $pythonPrefix = @("-3")
    }
}

$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    $npmCommand = Get-Command npm -ErrorAction SilentlyContinue
}
if (-not $npmCommand) {
    throw "No se encontró npm. Instalá Node.js y npm."
}
$npmExecutable = $npmCommand.Source

function Invoke-ValidationStep {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Executable,
        [string[]]$Arguments
    )

    Write-Output ""
    Write-Output "== $Name =="
    $exitCode = 1
    Push-Location $WorkingDirectory
    try {
        & $Executable @Arguments
        $exitCode = $LASTEXITCODE
    } catch {
        Write-Output $_
    } finally {
        Pop-Location
    }

    if ($exitCode -eq 0) {
        Write-Output "RESULTADO: OK"
    } else {
        Write-Output "RESULTADO: ERROR (código $exitCode)"
        $script:validationFailures.Add($Name)
    }
}

Invoke-ValidationStep `
    "Django system check" `
    $serverDirectory `
    $pythonExecutable `
    ($pythonPrefix + @("manage.py", "check"))

Invoke-ValidationStep `
    "Django migration consistency" `
    $serverDirectory `
    $pythonExecutable `
    ($pythonPrefix + @("manage.py", "makemigrations", "--check", "--dry-run"))

Invoke-ValidationStep `
    "Django API tests" `
    $serverDirectory `
    $pythonExecutable `
    ($pythonPrefix + @("manage.py", "test", "tests"))

Invoke-ValidationStep `
    "Angular component tests" `
    $clientDirectory `
    $npmExecutable `
    @("test", "--", "--watch=false")

Invoke-ValidationStep `
    "Angular production build" `
    $clientDirectory `
    $npmExecutable `
    @("run", "build")

$gitCommand = Get-Command git -ErrorAction SilentlyContinue
if ($gitCommand) {
    Invoke-ValidationStep `
        "Git whitespace check" `
        $repositoryRoot `
        $gitCommand.Source `
        @("diff", "--check")
}

Write-Output ""
if ($validationFailures.Count -eq 0) {
    Write-Output "VALIDACIÓN COMPLETA: todas las comprobaciones pasaron."
    exit 0
}

Write-Output "VALIDACIÓN INCOMPLETA: fallaron estos pasos:"
foreach ($failure in $validationFailures) {
    Write-Output " - $failure"
}
exit 1
