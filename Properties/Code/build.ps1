#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build script for Polylog Desktop Application
.DESCRIPTION
    Automates the packaging of Polylog into a standalone Windows executable using PyInstaller.
    Creates a distributable folder with all dependencies bundled.
.PARAMETER Clean
    Clean build artifacts before building
.PARAMETER Version
    Override version number (default: reads from pyproject.toml)
.EXAMPLE
    .\build.ps1
    .\build.ps1 -Clean
    .\build.ps1 -Version "1.0.0"
#>

param(
    [switch]$Clean,
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Polylog Desktop Application Builder  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root directory
$ProjectRoot = $PSScriptRoot
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"
$SpecFile = Join-Path $ProjectRoot "polylog.spec"

# Clean build artifacts if requested
if ($Clean) {
    Write-Host "[1/5] Cleaning build artifacts..." -ForegroundColor Yellow
    if (Test-Path $DistDir) {
        Remove-Item -Recurse -Force $DistDir
        Write-Host "  ✓ Removed dist/" -ForegroundColor Green
    }
    if (Test-Path $BuildDir) {
        Remove-Item -Recurse -Force $BuildDir
        Write-Host "  ✓ Removed build/" -ForegroundColor Green
    }
    # Remove .spec file to regenerate
    if (Test-Path $SpecFile) {
        Write-Host "  ℹ Found existing spec file" -ForegroundColor Gray
    }
} else {
    Write-Host "[1/5] Skipping clean (use -Clean to clean)" -ForegroundColor Gray
}

# Check Python installation
Write-Host ""
Write-Host "[2/5] Checking Python environment..." -ForegroundColor Yellow
try {
    $PythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "  ✓ Python found: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.9+ or add it to PATH" -ForegroundColor Red
    exit 1
}

# Check PyInstaller installation
Write-Host ""
Write-Host "[3/5] Checking PyInstaller..." -ForegroundColor Yellow
$PyInstallerInstalled = & python -c "import pyinstaller; print('installed')" 2>$null
if ($PyInstallerInstalled -ne "installed") {
    Write-Host "  ℹ PyInstaller not found, installing..." -ForegroundColor Yellow
    & python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ PyInstaller installed" -ForegroundColor Green
} else {
    Write-Host "  ✓ PyInstaller found" -ForegroundColor Green
}

# Verify data files exist
Write-Host ""
Write-Host "[4/5] Verifying data files..." -ForegroundColor Yellow
$DataFiles = @(
    "data\scalers.json",
    "data\symmetries.json"
)
$MissingFiles = @()
foreach ($File in $DataFiles) {
    $FullPath = Join-Path $ProjectRoot $File
    if (Test-Path $FullPath) {
        Write-Host "  ✓ Found $File" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Missing $File" -ForegroundColor Red
        $MissingFiles += $File
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "  Warning: Some data files are missing" -ForegroundColor Yellow
    Write-Host "  The application may not work correctly" -ForegroundColor Yellow
}

# Build with PyInstaller
Write-Host ""
Write-Host "[5/5] Building application with PyInstaller..." -ForegroundColor Yellow
Write-Host "  This may take several minutes..." -ForegroundColor Gray
Write-Host ""

try {
    & pyinstaller --noconfirm $SpecFile
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed"
    }
} catch {
    Write-Host ""
    Write-Host "  ✗ Build failed!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Verify build output
$ExePath = Join-Path $DistDir "Polylog\Polylog.exe"
if (Test-Path $ExePath) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Build completed successfully! ✓" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location:" -ForegroundColor Cyan
    Write-Host "  $ExePath" -ForegroundColor White
    Write-Host ""
    Write-Host "Distribution folder:" -ForegroundColor Cyan
    Write-Host "  $(Join-Path $DistDir "Polylog\")" -ForegroundColor White
    Write-Host ""
    
    # Get folder size
    $FolderSize = (Get-ChildItem -Recurse -File (Join-Path $DistDir "Polylog") | Measure-Object -Property Length -Sum).Sum
    $FolderSizeMB = [math]::Round($FolderSize / 1MB, 2)
    Write-Host "Distribution size: $FolderSizeMB MB" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "To distribute:" -ForegroundColor Yellow
    Write-Host "  1. Copy the entire 'dist\Polylog\' folder" -ForegroundColor White
    Write-Host "  2. Run 'Polylog.exe' on any Windows machine" -ForegroundColor White
    Write-Host ""
    Write-Host "Optional: Create installer using Inno Setup or NSIS" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "  ✗ Build completed but executable not found" -ForegroundColor Red
    Write-Host "  Expected: $ExePath" -ForegroundColor Red
    exit 1
}

Write-Host ""
