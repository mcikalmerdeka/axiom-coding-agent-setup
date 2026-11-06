# Back up the Metabase application database.
#
# The app DB contains every user, collection, question, dashboard, setting, and
# session. The dump is private: keep it out of Git.
#
# Usage:
#   .\scripts\backup_metabase.ps1
#   .\scripts\backup_metabase.ps1 -Service postgres -Database metabase

[CmdletBinding()]
param(
    [string]$Service = "postgres",
    [string]$Database = "metabase",
    [string]$DbUser = "postgres",
    [string]$OutputDir = "metabase/backups",
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = if ($ProjectRoot) { (Resolve-Path $ProjectRoot).Path } else { Split-Path -Parent $PSScriptRoot }
Push-Location $projectRoot

try {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $containerFile = "/tmp/metabase_$timestamp.dump"
    $localDir = if ([System.IO.Path]::IsPathRooted($OutputDir)) {
        $OutputDir
    } else {
        Join-Path $projectRoot $OutputDir
    }
    $localFile = Join-Path $localDir "metabase_$timestamp.dump"

    New-Item -ItemType Directory -Force -Path $localDir | Out-Null

    Write-Host "Dumping the $Database application database..."
    docker compose exec -T $Service pg_dump -U $DbUser -d $Database -Fc -f $containerFile
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump failed with exit code $LASTEXITCODE"
    }

    Write-Host "Copying the dump out of the container..."
    docker compose cp "${Service}:$containerFile" $localFile
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose cp failed with exit code $LASTEXITCODE"
    }

    docker compose exec -T $Service rm -f $containerFile | Out-Null

    $sizeMb = [math]::Round((Get-Item $localFile).Length / 1MB, 2)
    Write-Host "Backup written: $localFile ($sizeMb MB)"
    Write-Host "Keep this file private. It is ignored by Git."
}
finally {
    Pop-Location
}
