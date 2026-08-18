param(
    [ValidateSet('up', 'down', 'status', 'logs')]
    [string]$Action = 'up'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$composeArgs = @(
    '-f', 'compose.yaml',
    '-f', 'compose.database.yaml',
    '--profile', 'database'
)

if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
    Write-Warning 'Created .env from .env.example. Change both passwords before exposing the service outside localhost.'
}

switch ($Action) {
    'up' {
        docker compose @composeArgs up -d --build
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        docker compose @composeArgs ps -a
        Write-Output 'CV Algorithm Platform: http://localhost:8080'
    }
    'down' {
        docker compose @composeArgs down
    }
    'status' {
        docker compose @composeArgs ps -a
    }
    'logs' {
        docker compose @composeArgs logs --tail 200 -f
    }
}
