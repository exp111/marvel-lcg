[CmdletBinding()]
param(
    [string]$Version,
    [string]$OutputDirectory,
    [string]$PythonEnvironment,
    [switch]$NoArchive,
    [switch]$CustomBootloader,
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $projectRoot "release-artifacts"
}
$artifactRoot = [System.IO.Path]::GetFullPath($OutputDirectory)
$workRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".work"))

function Assert-ChildPath {
    param(
        [Parameter(Mandatory)][string]$Parent,
        [Parameter(Mandatory)][string]$Child
    )

    $parentPath = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\') + '\'
    $childPath = [System.IO.Path]::GetFullPath($Child)
    if (-not $childPath.StartsWith($parentPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify path outside '$Parent': $Child"
    }
}

function Get-ProjectVersion {
    $buildText = Get-Content -Raw (Join-Path $projectRoot "build.py")
    $parts = foreach ($name in @("MAJOR", "MINOR", "PATCH", "BUILD")) {
        $match = [regex]::Match($buildText, "(?m)^\s*$name\s*=\s*(\d+)\s*$")
        if (-not $match.Success) {
            throw "Could not read $name from build.py"
        }
        $match.Groups[1].Value
    }
    return $parts -join "."
}

$applicationVersion = Get-ProjectVersion
if (-not $Version) {
    if ($applicationVersion -match '^(\d+\.\d+\.\d+)\.0$') {
        $Version = $Matches[1]
    }
    else {
        $Version = $applicationVersion
    }
}
if ($Version -notmatch '^\d+\.\d+\.\d+(\.\d+)?$') {
    throw "Release version must use three or four numeric parts, for example 1.0.0 or 0.5.9.202."
}

if ($NoArchive -and $CustomBootloader) {
    throw "NoArchive and CustomBootloader are separate comparison variants and cannot be combined."
}

$variantSuffix = if ($CustomBootloader) { "-customboot" } elseif ($NoArchive) { "-noarchive" } else { "" }
$packagingVariant = if ($CustomBootloader) {
    "PyInstaller onedir with the verified v1.1.1 locally compiled bootloader"
}
elseif ($NoArchive) {
    "PyInstaller onedir with individual Python modules"
}
else {
    "PyInstaller onedir with embedded Python module archive"
}

$requiredPaths = @(
    "build.py",
    "main.py",
    "launch.json",
    "data\cards.json",
    "public\marvel.html",
    "assets\sounds",
    "assets\textures",
    "deck\starter",
    "PATCH_NOTES.md",
    "ATTRIBUTION.md",
    "packaging\marvel-lcg-release.spec"
)
foreach ($relativePath in $requiredPaths) {
    $path = Join-Path $projectRoot $relativePath
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required release input is missing: $relativePath"
    }
}

$uiVersion = $applicationVersion
if ($applicationVersion -match '^(\d+\.\d+\.\d+)\.0$') {
    $uiVersion = $Matches[1]
}
$expectedUiVersion = "$uiVersion" + "r"
$marvelHtml = Get-Content -Raw (Join-Path $projectRoot "public\marvel.html")
$staleUiVersions = [regex]::Matches($marvelHtml, '[?&]v=([^"''&]+)') |
    ForEach-Object { $_.Groups[1].Value } |
    Where-Object { $_ -ne $expectedUiVersion } |
    Sort-Object -Unique
if ($staleUiVersions) {
    throw "public\marvel.html contains stale UI cache version(s): $($staleUiVersions -join ', '). Expected $expectedUiVersion."
}

if (-not $PythonEnvironment) {
    $PythonEnvironment = Join-Path $projectRoot ".venv-release"
}
$pythonEnvironmentRoot = [System.IO.Path]::GetFullPath($PythonEnvironment)
$python = Join-Path $pythonEnvironmentRoot "Scripts\python.exe"
$pyinstaller = Join-Path $pythonEnvironmentRoot "Scripts\pyinstaller.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Release Python was not found at $python. Create a Python 3.12 .venv-release environment and install requirements-release.txt."
}
if (-not (Test-Path -LiteralPath $pyinstaller)) {
    throw "PyInstaller was not found at $pyinstaller. Install requirements-release.txt into .venv-release."
}
$pythonVersion = (& $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')").Trim()
if ($LASTEXITCODE -ne 0 -or $pythonVersion -ne "3.12.13") {
    throw "Release builds require Python 3.12.13; $python reports '$pythonVersion'."
}

if ($CustomBootloader) {
    $bootloader = (& $python -c "from pathlib import Path; import PyInstaller; print(Path(PyInstaller.__file__).parent / 'bootloader' / 'Windows-64bit-intel' / 'run.exe')").Trim()
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $bootloader)) {
        throw "Could not locate the PyInstaller Windows x64 bootloader in $pythonEnvironmentRoot."
    }

    $expectedBootloaderSha256 = "1ab6b9e06ed50d4fb489b017af71520a3d22566ee4372bcd2b12902264a4f32d"
    $actualBootloaderSha256 = (Get-FileHash -LiteralPath $bootloader -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualBootloaderSha256 -ne $expectedBootloaderSha256) {
        throw "The custom-bootloader build requires the verified v1.1.1 bootloader. Expected SHA-256 $expectedBootloaderSha256, got $actualBootloaderSha256 at $bootloader."
    }
}
$typescript = Get-Command "tsc.cmd" -ErrorAction SilentlyContinue
if (-not $typescript) {
    throw "TypeScript compiler tsc.cmd was not found. Install TypeScript with npm install -g typescript."
}

if ($PreflightOnly) {
    Write-Host "Release preflight passed for Marvel LCG $Version$variantSuffix (application $applicationVersion, Python $pythonVersion)."
    Write-Host "Packaging variant: $packagingVariant"
    Write-Host "Downloaded assets/cache and optional assets/pics are excluded by the staging manifest."
    exit 0
}

$stageRoot = Join-Path $workRoot "marvel-lcg-v$Version$variantSuffix"
$binaryRoot = Join-Path $workRoot "binary"
$pyinstallerWork = Join-Path $workRoot "pyinstaller"
foreach ($path in @($stageRoot, $binaryRoot, $pyinstallerWork)) {
    Assert-ChildPath -Parent $workRoot -Child $path
}

if (Test-Path -LiteralPath $workRoot) {
    Assert-ChildPath -Parent $PSScriptRoot -Child $workRoot
    Remove-Item -LiteralPath $workRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null
New-Item -ItemType Directory -Path $artifactRoot -Force | Out-Null

Push-Location $projectRoot
try {
    & $typescript.Source -p (Join-Path $projectRoot "public\js\tsconfig.json")
    if ($LASTEXITCODE -ne 0) {
        throw "TypeScript compilation failed with exit code $LASTEXITCODE."
    }

    $previousNoArchive = [Environment]::GetEnvironmentVariable(
        "MARVEL_LCG_NOARCHIVE",
        [EnvironmentVariableTarget]::Process
    )
    try {
        if ($NoArchive) {
            $env:MARVEL_LCG_NOARCHIVE = "1"
        }
        else {
            Remove-Item Env:\MARVEL_LCG_NOARCHIVE -ErrorAction SilentlyContinue
        }

        & $pyinstaller `
            --noconfirm `
            --clean `
            --distpath $binaryRoot `
            --workpath $pyinstallerWork `
            (Join-Path $projectRoot "packaging\marvel-lcg-release.spec")
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        if ($null -eq $previousNoArchive) {
            Remove-Item Env:\MARVEL_LCG_NOARCHIVE -ErrorAction SilentlyContinue
        }
        else {
            $env:MARVEL_LCG_NOARCHIVE = $previousNoArchive
        }
    }
}
finally {
    Pop-Location
}

$binaryBundle = Join-Path $binaryRoot "marvel-lcg"
$executable = Join-Path $binaryBundle "marvel-lcg.exe"
if (-not (Test-Path -LiteralPath $executable)) {
    throw "PyInstaller did not produce $executable"
}
Get-ChildItem -LiteralPath $binaryBundle | Copy-Item -Destination $stageRoot -Recurse

$internalDirectory = Join-Path $stageRoot "_internal"
if (-not (Test-Path -LiteralPath $internalDirectory -PathType Container)) {
    throw "PyInstaller did not produce the expected onedir _internal directory."
}

foreach ($folder in @("data", "public", "docs")) {
    Copy-Item -LiteralPath (Join-Path $projectRoot $folder) -Destination $stageRoot -Recurse
}
New-Item -ItemType Directory -Path (Join-Path $stageRoot "deck") -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot "deck\starter") -Destination (Join-Path $stageRoot "deck") -Recurse

New-Item -ItemType Directory -Path (Join-Path $stageRoot "assets") -Force | Out-Null
foreach ($folder in @("sounds", "textures")) {
    Copy-Item -LiteralPath (Join-Path $projectRoot "assets\$folder") -Destination (Join-Path $stageRoot "assets") -Recurse
}
# Keep the expected runtime paths, but never seed them with a developer's card scans.
New-Item -ItemType Directory -Path (Join-Path $stageRoot "assets\cache") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $stageRoot "assets\pics") -Force | Out-Null

foreach ($file in @("launch.json", "README.md", "PATCH_NOTES.md", "ATTRIBUTION.md")) {
    Copy-Item -LiteralPath (Join-Path $projectRoot $file) -Destination $stageRoot
}

# TypeScript sources and source maps are build inputs, not runtime files.
Get-ChildItem -LiteralPath (Join-Path $stageRoot "public\js") -Recurse -File |
    Where-Object { $_.Extension -in @(".ts", ".map") -or $_.Name -in @("tsconfig.json", "watch.bat") } |
    Remove-Item -Force

$forbiddenFiles = Get-ChildItem -LiteralPath (Join-Path $stageRoot "assets\cache"), (Join-Path $stageRoot "assets\pics") -Recurse -File
if ($forbiddenFiles) {
    throw "Release staging unexpectedly contains cached or optional card images."
}

$commit = & git -c safe.directory='*' -C $projectRoot rev-parse --short HEAD 2>$null
if ($LASTEXITCODE -ne 0) {
    $commit = "unknown"
}
$manifest = @"
Marvel LCG Digital community build
Release version: $Version
Application version: $applicationVersion
Source commit: $commit
Packaging variant: $packagingVariant

Included assets: sounds and interface textures
Excluded assets: downloaded card cache and optional offline card-image pack
Card artwork is retrieved using the image servers configured in launch.json.
"@
Set-Content -LiteralPath (Join-Path $stageRoot "RELEASE-MANIFEST.txt") -Value $manifest -Encoding UTF8

$archive = Join-Path $artifactRoot "marvel-lcg-v$Version$variantSuffix-windows.zip"
$checksum = "$archive.sha256"
foreach ($path in @($archive, $checksum)) {
    if (Test-Path -LiteralPath $path) {
        Assert-ChildPath -Parent $artifactRoot -Child $path
        Remove-Item -LiteralPath $path -Force
    }
}
Compress-Archive -LiteralPath $stageRoot -DestinationPath $archive -CompressionLevel Optimal
$hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath $checksum -Value "$hash  $([System.IO.Path]::GetFileName($archive))" -Encoding ASCII

Write-Host "Created $archive"
Write-Host "SHA-256 $hash"
