[CmdletBinding()]
param(
    [ValidateSet('install', 'current', 'history', 'upgrade', 'downgrade', 'new', 'sql')]
    [string]$Action = 'upgrade',
    [string]$Revision = 'head',
    [string]$Message,
    [string]$OutputPath = 'database/generated/upgrade.sql'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$AlembicConfig = Join-Path $ProjectRoot 'database/alembic.ini'
$DatabaseRequirements = Join-Path $ProjectRoot 'database/requirements.txt'

function Invoke-Alembic {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & python -m alembic -c $AlembicConfig @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Alembic failed with exit code $LASTEXITCODE"
    }
}

switch ($Action) {
    'install' {
        python -m pip install -r $DatabaseRequirements
        if ($LASTEXITCODE -ne 0) { throw 'Database dependency installation failed.' }
    }
    'current' { Invoke-Alembic current }
    'history' { Invoke-Alembic history --verbose }
    'upgrade' { Invoke-Alembic upgrade $Revision }
    'downgrade' {
        if ($Revision -eq 'head') {
            throw "Set -Revision to a target such as '-1' or 'base' for downgrade."
        }
        Invoke-Alembic downgrade $Revision
    }
    'new' {
        if ([string]::IsNullOrWhiteSpace($Message)) {
            throw 'Set -Message when creating a migration.'
        }
        Invoke-Alembic revision -m $Message
    }
    'sql' {
        $ResolvedOutput = Join-Path $ProjectRoot $OutputPath
        $OutputDirectory = Split-Path -Parent $ResolvedOutput
        if (-not (Test-Path -LiteralPath $OutputDirectory)) {
            New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
        }
        $PreviousPreference = $ProgressPreference
        try {
            $ProgressPreference = 'SilentlyContinue'
            python -m alembic -c $AlembicConfig upgrade "$Revision" --sql |
                Set-Content -LiteralPath $ResolvedOutput -Encoding UTF8
            if ($LASTEXITCODE -ne 0) { throw 'Offline SQL generation failed.' }
        } finally {
            $ProgressPreference = $PreviousPreference
        }
        Write-Output "Offline migration SQL: $ResolvedOutput"
    }
}
