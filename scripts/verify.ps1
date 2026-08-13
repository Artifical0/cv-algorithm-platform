$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

Write-Output '1/8 Python syntax'
python -m compileall -q backend packages services examples tests

Write-Output '2/8 TOML syntax'
@'
from pathlib import Path
import tomllib
for path in Path('.').rglob('pyproject.toml'):
    with path.open('rb') as stream:
        tomllib.load(stream)
'@ | python -

Write-Output '3/8 YAML syntax'
yq '.' compose.yaml | Out-Null
yq '.' compose.camera.yaml | Out-Null
Get-ChildItem examples -Recurse -File -Include '*.yaml','*.yml' | ForEach-Object {
    yq '.' $_.FullName | Out-Null
}

Write-Output '4/8 Architecture boundaries'
$dockerLeaks = rg -l 'import docker|from docker' backend\src
if ($dockerLeaks) { throw "Platform API imports Docker SDK: $dockerLeaks" }
$directFetch = rg -l '\bfetch\(' frontend\src | Where-Object { $_ -ne 'frontend\src\api\http.ts' }
if ($directFetch) { throw "Frontend bypasses API client: $directFetch" }

Write-Output '5/8 No local database dependencies'
$databaseLeaks = rg -n 'sqlalchemy|psycopg|aiosqlite|sqlite3|asyncpg|mysqlclient' backend services compose.yaml
if ($databaseLeaks) { throw "Database dependency found: $databaseLeaks" }

if (Get-Command pytest -ErrorAction SilentlyContinue) {
    Write-Output '6/8 Python tests'
    pytest packages\algorithm-sdk\tests backend\tests services\algorithm-manager\tests tests
} else {
    Write-Output '6/8 Python tests SKIPPED: pytest is not installed'
}

Write-Output '7/8 Dependency-free manager smoke tests'
$env:PYTHONPATH = Join-Path $ProjectRoot 'services\algorithm-manager\src'
python scripts\manager_smoke.py
Remove-Item Env:\PYTHONPATH

if (Test-Path frontend\node_modules) {
    Write-Output '8/8 Frontend checks'
    Push-Location frontend
    try {
        npm run typecheck
        npm test
        npm run build
    } finally {
        Pop-Location
    }
} else {
    Write-Output '8/8 Frontend checks SKIPPED: node_modules is not installed'
}

Write-Output 'Verification completed.'
