# Optional Codex update notice for Windows. Remove hooks/codex-hooks.json to disable it.
# It makes one anonymous GET of a public manifest, writes nothing, and fails silently.

$disabledValues = @("1", "true", "yes", "on")
foreach ($name in @("SUPERLEADS_DISABLE_UPDATE_CHECK", "DISABLE_TELEMETRY")) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if ($disabledValues -contains ([string]$value).Trim().ToLowerInvariant()) {
        exit 0
    }
}

try {
    $pluginRoot = $env:PLUGIN_ROOT
    if ([string]::IsNullOrWhiteSpace($pluginRoot)) {
        $pluginRoot = Split-Path -Parent $PSScriptRoot
    }

    $localManifest = Join-Path $pluginRoot ".codex-plugin\plugin.json"
    $localVersion = (Get-Content -LiteralPath $localManifest -Raw | ConvertFrom-Json).version
    if ($localVersion -notmatch '^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$') {
        exit 0
    }

    $remoteManifest = & curl.exe --fail --silent --show-error --max-time 3 "https://raw.githubusercontent.com/fleixweb/superleads/master/.codex-plugin/plugin.json" 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteManifest)) {
        exit 0
    }

    $remoteVersion = (($remoteManifest -join "`n") | ConvertFrom-Json).version
    if ($remoteVersion -notmatch '^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$') {
        exit 0
    }

    $remoteParts = [version]$remoteVersion
    $localParts = [version]$localVersion
    if ($remoteParts -gt $localParts) {
        $available = [string]::Concat([char]0x53EF, [char]0x7528)
        $youAreOn = [string]::Concat([char]0x4F60, [char]0x5728)
        $see = [string]([char]0x89C1)
        Write-Output "Superleads $remoteVersion $available$([char]0xFF08)$youAreOn $localVersion$([char]0xFF09)$([char]0x2192) $see CHANGELOG"
    }
} catch {
    exit 0
}
