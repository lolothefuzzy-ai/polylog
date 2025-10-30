#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Prepare Polylog for distribution - creates portable package ready to share
.DESCRIPTION
    Post-processes PyInstaller build output to create a clean, portable distribution:
    - Copies application to release directory
    - Adds launcher wrapper and documentation
    - Creates compressed archive
    - Verifies all files are present
.PARAMETER OutputDir
    Directory to create release in (default: ./release/)
.PARAMETER Version
    Version number to include in package name (default: 0.1.0)
.PARAMETER Compress
    Create ZIP archive after preparing distribution
.PARAMETER Clean
    Remove existing release directory before creating new one
.EXAMPLE
    .\\prepare_distribution.ps1
    .\\prepare_distribution.ps1 -Version "1.0.0" -Compress
    .\\prepare_distribution.ps1 -OutputDir "D:\\Releases" -Clean -Compress
#>

param(
    [string]$OutputDir = "./release",
    [string]$Version = "0.1.0",
    [switch]$Compress,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Polylog Distribution Preparation      " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot | Split-Path -Parent
$DistSource = Join-Path $ProjectRoot "dist" "Polylog"
$LauncherSource = Join-Path $ProjectRoot "scripts" "polylog-launcher.bat"
$ReleaseDir = Join-Path $ProjectRoot $OutputDir
$ReleaseName = "Polylog-v$Version-portable"
$ReleaseDestination = Join-Path $ReleaseDir $ReleaseName

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Source: $DistSource" -ForegroundColor Gray
Write-Host "  Output: $ReleaseDestination" -ForegroundColor Gray
Write-Host "  Version: $Version" -ForegroundColor Gray
Write-Host ""

# Step 1: Verify PyInstaller build exists
Write-Host "[1/5] Verifying PyInstaller build..." -ForegroundColor Yellow
if (-not (Test-Path $DistSource)) {
    Write-Host "  ✗ Build not found: $DistSource" -ForegroundColor Red
    Write-Host "  Please run PyInstaller first:" -ForegroundColor Yellow
    Write-Host "    pyinstaller polylog-optimized.spec" -ForegroundColor Gray
    exit 1
}

$ExePath = Join-Path $DistSource "Polylog.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "  ✗ Executable not found: $ExePath" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Build found and valid" -ForegroundColor Green

# Step 2: Clean existing release if requested
Write-Host ""
Write-Host "[2/5] Preparing output directory..." -ForegroundColor Yellow
if ($Clean -and (Test-Path $ReleaseDir)) {
    Write-Host "  Removing existing release directory..." -ForegroundColor Gray
    Remove-Item -Recurse -Force $ReleaseDir
    Write-Host "  ✓ Cleaned" -ForegroundColor Green
}

if (-not (Test-Path $ReleaseDir)) {
    New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
    Write-Host "  ✓ Created output directory" -ForegroundColor Green
}

if (Test-Path $ReleaseDestination) {
    Write-Host "  Note: Updating existing release package" -ForegroundColor Gray
    Remove-Item -Recurse -Force $ReleaseDestination
}

# Step 3: Copy build to release directory
Write-Host ""
Write-Host "[3/5] Copying application files..." -ForegroundColor Yellow
Copy-Item -Path $DistSource -Destination $ReleaseDestination -Recurse -Force
Write-Host "  ✓ Copied $ReleaseDestination" -ForegroundColor Green

# Step 4: Add launcher wrapper and documentation
Write-Host ""
Write-Host "[4/5] Adding launcher and documentation..." -ForegroundColor Yellow

# Copy launcher wrapper
if (Test-Path $LauncherSource) {
    Copy-Item -Path $LauncherSource -Destination (Join-Path $ReleaseDestination "Polylog.bat") -Force
    Write-Host "  ✓ Added Polylog.bat launcher" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Launcher script not found: $LauncherSource" -ForegroundColor Yellow
}

# Create README
$ReadmePath = Join-Path $ReleaseDestination "README.txt"
$ReadmeContent = @"
Polylog v$Version - Portable Distribution
============================================

QUICK START:
-----------
1. Double-click Polylog.exe to launch the GUI

COMMAND LINE USAGE:
-------------------
Launch modes:
  Polylog.exe                       Launch GUI (default)
  Polylog.exe --mode api --port 8080   Launch API server on port 8080
  Polylog.exe --mode cli            Launch interactive CLI
  Polylog.exe demo                  Run automated demo

Help:
  Polylog.exe --help                Show all options

REQUIREMENTS:
-------------
- Windows 7 or later
- No Python installation needed!
- All dependencies are bundled

FEATURES:
---------
- Interactive polyform design with 3D visualization
- Automated placement engine
- Continuous exploration algorithms
- Real-time performance monitoring
- REST API support

DOCUMENTATION:
---------------
For full documentation and examples, visit:
https://github.com/yourusername/polylog

SUPPORT:
--------
For issues or questions, contact: support@example.com

LICENSE:
--------
MIT License - See LICENSE.txt for details
"@

Set-Content -Path $ReadmePath -Value $ReadmeContent
Write-Host "  ✓ Created README.txt" -ForegroundColor Green

# Get distribution size
$DirSize = (Get-ChildItem -Recurse -File $ReleaseDestination | Measure-Object -Property Length -Sum).Sum
$DirSizeMB = [math]::Round($DirSize / 1MB, 2)

Write-Host ""
Write-Host "[5/5] Creating archive..." -ForegroundColor Yellow
Write-Host "  Distribution size: $DirSizeMB MB" -ForegroundColor Gray

# Step 5: Create ZIP archive if requested
$ZipPath = $null
if ($Compress) {
    $ZipName = "$ReleaseName.zip"
    $ZipPath = Join-Path $ReleaseDir $ZipName
    
    Write-Host "  Compressing to ZIP..." -ForegroundColor Gray
    
    # Use Windows PowerShell 5.1+ Compress-Archive
    try {
        Compress-Archive -Path $ReleaseDestination -DestinationPath $ZipPath -Force -ErrorAction Stop
        $ZipSize = (Get-Item $ZipPath).Length
        $ZipSizeMB = [math]::Round($ZipSize / 1MB, 2)
        Write-Host "  ✓ Created $ZipName ($ZipSizeMB MB)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Failed to create ZIP (manual compression recommended)" -ForegroundColor Yellow
        Write-Host "  Error: $_" -ForegroundColor Gray
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Distribution Ready! ✓                " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Location: $ReleaseDestination" -ForegroundColor Cyan
Write-Host "Size: $DirSizeMB MB" -ForegroundColor Cyan

if ($ZipPath) {
    Write-Host ""
    Write-Host "Archive: $ZipPath" -ForegroundColor Cyan
    Write-Host "Size: $ZipSizeMB MB" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "DISTRIBUTION FILES:" -ForegroundColor Yellow
Write-Host "  • Polylog.exe                Main application" -ForegroundColor White
Write-Host "  • Polylog.bat                Launcher wrapper (double-click friendly)" -ForegroundColor White
Write-Host "  • README.txt                 Usage and documentation" -ForegroundColor White
Write-Host "  • _internal/                 Dependencies (DO NOT MODIFY)" -ForegroundColor White

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Test: Run 'Polylog.exe' to verify it works" -ForegroundColor White
Write-Host "  2. Distribute:" -ForegroundColor White

if ($Compress -and $ZipPath) {
    Write-Host "     a. Share $ZipName" -ForegroundColor Gray
    Write-Host "     b. Or share the entire $ReleaseName folder" -ForegroundColor Gray
} else {
    Write-Host "     a. ZIP the $ReleaseName folder for sharing" -ForegroundColor Gray
    Write-Host "     b. Or use -Compress flag next time" -ForegroundColor Gray
}

Write-Host "  3. Recipients just need to extract and run Polylog.exe" -ForegroundColor White
Write-Host ""
Write-Host "No Python installation required on target machines!" -ForegroundColor Green
Write-Host ""
