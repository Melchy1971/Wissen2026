Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendScript = Join-Path $scriptDir 'dev-backend.ps1'
$frontendScript = Join-Path $scriptDir 'dev-frontend.ps1'

function Test-PortListening {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $listener
}

if (-not (Test-Path $backendScript)) {
    throw "Backend start script not found at $backendScript."
}

if (-not (Test-Path $frontendScript)) {
    throw "Frontend start script not found at $frontendScript."
}

if (Test-PortListening -Port 8000) {
    Write-Host 'Backend already appears to be running on http://127.0.0.1:8000. Skipping start.'
} else {
    Start-Process powershell -ArgumentList @(
        '-NoExit',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        $backendScript
    )
}

if (Test-PortListening -Port 5173) {
    Write-Host 'Frontend already appears to be running on http://127.0.0.1:5173. Skipping start.'
} else {
    Start-Process powershell -ArgumentList @(
        '-NoExit',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        $frontendScript
    )
}