# Lädt Repo-Root .env in die aktuelle PowerShell-Session (keine Ausgabe der Werte).
# Nutzung:  . .\scripts\load-workspace-env.ps1
# Optional:  . .\scripts\load-workspace-env.ps1 -WorkspaceRoot "D:\pfad\zum\repo"

param(
    [string]$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$envFile = Join-Path $WorkspaceRoot '.env'
if (-not (Test-Path -LiteralPath $envFile)) {
    Write-Warning "Keine .env unter $envFile — Kopie aus .env.example anlegen."
    return
}

Get-Content -LiteralPath $envFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith('#')) { return }
    $eq = $line.IndexOf('=')
    if ($eq -lt 1) { return }
    $key = $line.Substring(0, $eq).Trim()
    $val = $line.Substring($eq + 1).Trim().Trim('"').Trim("'")
    if ($key) {
        Set-Item -Path "Env:$key" -Value $val
    }
}

Write-Host "OK: Umgebungsvariablen aus .env geladen ($envFile)." -ForegroundColor Green
