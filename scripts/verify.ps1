$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

Write-Output '1/9 Python syntax'
python -m compileall -q backend database packages services examples scripts tests

Write-Output '2/9 TOML syntax'
@'
from pathlib import Path
import tomllib
for path in Path('.').rglob('pyproject.toml'):
    with path.open('rb') as stream:
        tomllib.load(stream)
'@ | python -

Write-Output '3/9 YAML syntax'
if (Get-Command yq -ErrorAction SilentlyContinue) {
    yq '.' compose.yaml | Out-Null
    yq '.' compose.camera.yaml | Out-Null
    yq '.' compose.database.yaml | Out-Null
    Get-ChildItem examples -Recurse -File -Include '*.yaml','*.yml' | ForEach-Object {
        yq '.' $_.FullName | Out-Null
    }
} else {
    docker compose -f compose.yaml -f compose.database.yaml --profile database config --quiet
    Write-Output 'Example manifest YAML checks SKIPPED: yq is not installed'
}

Write-Output '4/9 Architecture boundaries'
$dockerLeaks = rg -l 'import docker|from docker' backend\src
if ($dockerLeaks) { throw "Platform API imports Docker SDK: $dockerLeaks" }
$directFetch = rg -l '\bfetch\(' frontend\src | Where-Object { $_ -ne 'frontend\src\api\http.ts' }
if ($directFetch) { throw "Frontend bypasses API client: $directFetch" }

Write-Output '5/9 PostgreSQL adapter boundaries'
$managerDatabaseLeaks = rg -n 'sqlalchemy|psycopg|aiosqlite|sqlite3|asyncpg|mysqlclient' services
if ($managerDatabaseLeaks) { throw "Database dependency leaked into runtime services: $managerDatabaseLeaks" }
$backendDependency = Select-String -Path backend\pyproject.toml -SimpleMatch 'psycopg[binary]'
if (-not $backendDependency) { throw 'Backend PostgreSQL driver is missing' }

Write-Output '6/9 Database migration chain'
python scripts/verify_database_migrations.py

if (Get-Command pytest -ErrorAction SilentlyContinue) {
    Write-Output '7/9 Python tests'
    pytest packages\algorithm-sdk\tests backend\tests services\algorithm-manager\tests tests
} else {
    Write-Output '7/9 Python tests SKIPPED: pytest is not installed'
}

Write-Output '8/9 Dependency-free manager smoke tests'
$env:PYTHONPATH = Join-Path $ProjectRoot 'services\algorithm-manager\src'
python scripts\manager_smoke.py
Remove-Item Env:\PYTHONPATH

if (Test-Path frontend\node_modules) {
    Write-Output '9/9 Frontend checks'
    Push-Location frontend
    try {
        npm run typecheck
        npm test
        npm run build
    } finally {
        Pop-Location
    }
} else {
    Write-Output '9/9 Frontend checks SKIPPED: node_modules is not installed'
}

Write-Output 'Verification completed.'
