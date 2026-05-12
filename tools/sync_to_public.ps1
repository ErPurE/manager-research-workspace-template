param(
    [string]$PrivateRepo = "D:\ErPurE\Documents\Manager",
    [string]$PublicRepo = "D:\ErPurE\Documents\manager-research-workspace-template",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$ManifestPath = Join-Path $PSScriptRoot "public_sync_manifest.json"
$Manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $ManifestPath | ConvertFrom-Json
$PrivateRoot = (Resolve-Path -LiteralPath $PrivateRepo).Path
$PublicRoot = (Resolve-Path -LiteralPath $PublicRepo).Path

function Normalize-RelativePath {
    param([string]$Root, [string]$Path)
    $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path.TrimEnd("\", "/")
    $resolvedPath = (Resolve-Path -LiteralPath $Path).Path
    return $resolvedPath.Substring($resolvedRoot.Length).TrimStart("\", "/") -replace "\\", "/"
}

function Test-DeniedPath {
    param([string]$RelativePath)
    foreach ($pattern in $Manifest.deny_patterns) {
        if ($RelativePath -like $pattern) {
            return $true
        }
    }
    return $false
}

function Test-TextFile {
    param([string]$Path)
    $extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    return $Manifest.text_extensions -contains $extension
}

function Get-AllowedFiles {
    $files = New-Object System.Collections.Generic.List[string]

    foreach ($relative in $Manifest.allow_files) {
        $path = Join-Path $PrivateRoot $relative
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $files.Add((Normalize-RelativePath -Root $PrivateRoot -Path $path))
        }
    }

    foreach ($relativeDir in $Manifest.allow_dirs) {
        $dir = Join-Path $PrivateRoot $relativeDir
        if (Test-Path -LiteralPath $dir -PathType Container) {
            Get-ChildItem -LiteralPath $dir -Recurse -File | ForEach-Object {
                $files.Add((Normalize-RelativePath -Root $PrivateRoot -Path $_.FullName))
            }
        }
    }

    return $files |
        Sort-Object -Unique |
        Where-Object { -not (Test-DeniedPath $_) }
}

function Assert-NoSensitiveContent {
    param([string]$Root, [string[]]$RelativePaths)
    foreach ($relative in $RelativePaths) {
        if ($relative -eq "tools/public_sync_manifest.json") {
            continue
        }
        $path = Join-Path $Root ($relative -replace "/", "\")
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            continue
        }
        if (-not (Test-TextFile $path)) {
            continue
        }
        foreach ($pattern in $Manifest.sensitive_patterns) {
            $matches = Select-String -LiteralPath $path -Pattern $pattern -Encoding UTF8 -ErrorAction SilentlyContinue
            if ($matches) {
                $first = $matches | Select-Object -First 1
                throw "Sensitive pattern '$pattern' matched ${relative}:$($first.LineNumber). Sync aborted."
            }
        }
    }
}

function Get-FileHashOrEmpty {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return ""
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

$allowed = @(Get-AllowedFiles)
Assert-NoSensitiveContent -Root $PrivateRoot -RelativePaths $allowed

$changes = foreach ($relative in $allowed) {
    $source = Join-Path $PrivateRoot ($relative -replace "/", "\")
    $target = Join-Path $PublicRoot ($relative -replace "/", "\")
    $sourceHash = Get-FileHashOrEmpty $source
    $targetHash = Get-FileHashOrEmpty $target
    $status = if (-not $targetHash) { "ADD" } elseif ($sourceHash -ne $targetHash) { "MOD" } else { "SAME" }
    [pscustomobject]@{
        Status = $status
        Path = $relative
    }
}

$changes | Where-Object { $_.Status -ne "SAME" } | Format-Table -AutoSize

if (-not $Apply) {
    Write-Host "Dry run only. Re-run with -Apply to copy allowlisted files."
    exit 0
}

foreach ($change in $changes | Where-Object { $_.Status -ne "SAME" }) {
    $source = Join-Path $PrivateRoot ($change.Path -replace "/", "\")
    $target = Join-Path $PublicRoot ($change.Path -replace "/", "\")
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
}

$publicFiles = @($allowed | Where-Object {
    Test-Path -LiteralPath (Join-Path $PublicRoot ($_ -replace "/", "\")) -PathType Leaf
})
Assert-NoSensitiveContent -Root $PublicRoot -RelativePaths $publicFiles

Push-Location $PublicRoot
try {
    python -m py_compile dashboard\server.py dashboard\launcher.py
    node --check dashboard\app.js
    powershell -ExecutionPolicy Bypass -File .agent\validate_agent_runtime.ps1
}
finally {
    Pop-Location
}

Write-Host "Applied public-safe framework sync."
