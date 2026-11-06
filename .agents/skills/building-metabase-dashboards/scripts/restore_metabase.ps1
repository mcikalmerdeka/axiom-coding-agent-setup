# Restore the Metabase application database from a pg_dump backup.
#
# DESTRUCTIVE: stops Metabase, drops the current app database, and restores the
# dump. Users, settings, questions, and dashboards return to the dump's state.
# The analytics database is not touched.
#
# Usage:
#   .\scripts\restore_metabase.ps1 -DumpFile .\metabase\backups\metabase_20261106_142757.dump
#   .\scripts\restore_metabase.ps1 -DumpFile ... -Force
#
# Without -Force you must type RESTORE to continue.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DumpFile,
    [string]$Service = "postgres",
    [string]$Database = "metabase",
    [string]$DbUser = "postgres",
    [string]$MetabaseService = "metabase",
    [string]$MetabaseUrl = "http://127.0.0.1:3000",
    [int]$HealthTimeoutSeconds = 180,
    [string]$ProjectRoot = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$projectRoot = if ($ProjectRoot) { (Resolve-Path $ProjectRoot).Path } else { Split-Path -Parent $PSScriptRoot }
Push-Location $projectRoot

try {
    $resolvedDump = (Resolve-Path $DumpFile).Path
    if (-not (Test-Path $resolvedDump -PathType Leaf)) {
        throw "Dump file not found: $resolvedDump"
    }

    if (-not $Force) {
        Write-Host "This will DELETE the current Metabase application database and"
        Write-Host "restore it from:"
        Write-Host "  $resolvedDump"
        $answer = Read-Host "Type RESTORE to continue"
        if ($answer -ne "RESTORE") {
            throw "Restore cancelled."
        }
    }

    Write-Host "Stopping Metabase..."
    docker compose stop $MetabaseService | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not stop the Metabase container."
    }

    Write-Host "Recreating the $Database application database..."
    docker compose exec -T $Service psql -U $DbUser -d postgres -v ON_ERROR_STOP=1 `
        -c "DROP DATABASE IF EXISTS $Database WITH (FORCE);"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not drop the $Database database."
    }
    docker compose exec -T $Service psql -U $DbUser -d postgres -v ON_ERROR_STOP=1 `
        -c "CREATE DATABASE $Database;"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the $Database database."
    }

    $containerFile = "/tmp/metabase_restore.dump"
    Write-Host "Copying the dump into the Postgres container..."
    docker compose cp $resolvedDump "${Service}:$containerFile"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not copy the dump into the container."
    }

    Write-Host "Restoring..."
    docker compose exec -T $Service pg_restore -U $DbUser -d $Database `
        --no-owner --no-privileges --exit-on-error $containerFile
    if ($LASTEXITCODE -ne 0) {
        throw "pg_restore failed with exit code $LASTEXITCODE. Metabase remains stopped."
    }
    docker compose exec -T $Service rm -f $containerFile | Out-Null

    Write-Host "Starting Metabase..."
    docker compose up -d $MetabaseService | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not start the Metabase container."
    }

    Write-Host "Waiting for Metabase health..."
    $deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing "$MetabaseUrl/api/health" -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Host "Metabase is healthy at $MetabaseUrl."
                return
            }
        }
        catch {
            Start-Sleep -Seconds 3
        }
    }

    Write-Warning "Metabase did not report healthy within $HealthTimeoutSeconds seconds. Check: docker compose logs $MetabaseService --tail 100"
}
finally {
    Pop-Location
}
