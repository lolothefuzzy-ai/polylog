#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete build script for Polylog with optimization and installer creation
.DESCRIPTION
    Builds Polylog desktop application with optional optimization and Inno Setup installer.
    Supports multiple build modes: standard, optimized, and installer creation.
.PARAMETER Optimized
    Use optimized build configuration (excludes API features, saves ~130MB)
.PARAMETER Installer
    Create Windows installer using Inno Setup (requires Inno Setup installed)
.PARAMETER Clean
    Clean build artifacts before building
.PARAMETER Version
    Override version number (default: 0.1.0)
.EXAMPLE
    .\build-installer.ps1
    .\build-installer.ps1 -Optimized
    .\build-installer.ps1 -Optimized -Installer
    .\build-installer.ps1 -Clean -Optimized -Installer
#>

param(
    [switch]$Optimized,
    [switch]$Installer,
    [switch]$Clean,
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Polylog Complete Build System        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root directory
$ProjectRoot = $PSScriptRoot
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"
$InstallerDir = Join-Path $ProjectRoot "installer"

# Select spec file
if ($Optimized) {
    $SpecFile = Join-Path $ProjectRoot "polylog-optimized.spec"
    $BuildMode = "Optimized"
    Write-Host "Build Mode: OPTIMIZED (smaller size)" -ForegroundColor Green
} else {
    $SpecFile = Join-Path $ProjectRoot "polylog.spec"
    $BuildMode = "Standard"
    Write-Host "Build Mode: STANDARD (all features)" -ForegroundColor Yellow
}

if ($Installer) {
    Write-Host "Installer: ENABLED (Inno Setup)" -ForegroundColor Green
} else {
    Write-Host "Installer: DISABLED (folder distribution only)" -ForegroundColor Gray
}
Write-Host ""

# Clean build artifacts if requested
if ($Clean) {
    Write-Host "[1/6] Cleaning build artifacts..." -ForegroundColor Yellow
    if (Test-Path $DistDir) {
        Remove-Item -Recurse -Force $DistDir
        Write-Host "  ✓ Removed dist/" -ForegroundColor Green
    }
    if (Test-Path $BuildDir) {
        Remove-Item -Recurse -Force $BuildDir
        Write-Host "  ✓ Removed build/" -ForegroundColor Green
    }
} else {
    Write-Host "[1/6] Skipping clean (use -Clean to clean)" -ForegroundColor Gray
}

# Check Python installation
Write-Host ""
Write-Host "[2/6] Checking Python environment..." -ForegroundColor Yellow
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
Write-Host "[3/6] Checking PyInstaller..." -ForegroundColor Yellow
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

# Check Inno Setup if installer requested
$InnoSetupPath = $null
if ($Installer) {
    Write-Host ""
    Write-Host "[4/6] Checking Inno Setup..." -ForegroundColor Yellow
    
    # Common Inno Setup installation paths
    $InnoSetupPaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        "C:\Program Files\Inno Setup 5\ISCC.exe"
    )
    
    foreach ($Path in $InnoSetupPaths) {
        if (Test-Path $Path) {
            $InnoSetupPath = $Path
            break
        }
    }
    
    if ($InnoSetupPath) {
        Write-Host "  ✓ Inno Setup found: $InnoSetupPath" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Inno Setup not found" -ForegroundColor Red
        Write-Host "  Download from: https://jrsoftware.org/isinfo.php" -ForegroundColor Yellow
        Write-Host "  Continuing without installer creation..." -ForegroundColor Yellow
        $Installer = $false
    }
} else {
    Write-Host ""
    Write-Host "[4/6] Skipping Inno Setup check (not creating installer)" -ForegroundColor Gray
}

# Verify data files exist
Write-Host ""
Write-Host "[5/6] Verifying data files..." -ForegroundColor Yellow
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
Write-Host "[6/6] Building application with PyInstaller..." -ForegroundColor Yellow
Write-Host "  Using spec: $(Split-Path -Leaf $SpecFile)" -ForegroundColor Gray
Write-Host "  This may take several minutes..." -ForegroundColor Gray
Write-Host ""

$BuildStartTime = Get-Date

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

$BuildEndTime = Get-Date
$BuildDuration = ($BuildEndTime - $BuildStartTime).TotalSeconds

# Verify build output
$ExePath = Join-Path $DistDir "Polylog\Polylog.exe"
if (Test-Path $ExePath) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Build completed successfully! ✓" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Build Mode: $BuildMode" -ForegroundColor Cyan
    Write-Host "Build Time: $([math]::Round($BuildDuration, 2)) seconds" -ForegroundColor Cyan
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
    Write-Host "Distribution size: $FolderSizeMB MB" -ForegroundColor Cyan
    
    if ($Optimized) {
        Write-Host "  (Optimized build - approximately 130MB smaller than standard)" -ForegroundColor Gray
    }
    
} else {
    Write-Host ""
    Write-Host "  ✗ Build completed but executable not found" -ForegroundColor Red
    Write-Host "  Expected: $ExePath" -ForegroundColor Red
    exit 1
}

# Create installer if requested
if ($Installer -and $InnoSetupPath) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Creating Installer Package           " -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    $IssFile = Join-Path $InstallerDir "polylog_installer.iss"
    
    if (-not (Test-Path $IssFile)) {
        Write-Host "  ✗ Installer script not found: $IssFile" -ForegroundColor Red
        Write-Host "  Please ensure installer\polylog_installer.iss exists" -ForegroundColor Red
    } else {
        Write-Host "Building installer..." -ForegroundColor Yellow
        Write-Host "  Script: $IssFile" -ForegroundColor Gray
        Write-Host ""
        
        try {
            & $InnoSetupPath $IssFile
            if ($LASTEXITCODE -ne 0) {
                throw "Inno Setup compilation failed"
            }
            
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  Installer created successfully! ✓    " -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            
            $InstallerFile = Join-Path $DistDir "Polylog-Setup-$Version.exe"
            if (Test-Path $InstallerFile) {
                $InstallerSize = (Get-Item $InstallerFile).Length
                $InstallerSizeMB = [math]::Round($InstallerSize / 1MB, 2)
                
                Write-Host "Installer location:" -ForegroundColor Cyan
                Write-Host "  $InstallerFile" -ForegroundColor White
                Write-Host ""
                Write-Host "Installer size: $InstallerSizeMB MB" -ForegroundColor Cyan
            }
        } catch {
            Write-Host ""
            Write-Host "  ✗ Installer creation failed!" -ForegroundColor Red
            Write-Host "  Error: $_" -ForegroundColor Red
            Write-Host "  Application folder is still available for manual distribution" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Build Summary                        " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Build Configuration:" -ForegroundColor Yellow
Write-Host "  • Mode: $BuildMode" -ForegroundColor White
Write-Host "  • Size: $FolderSizeMB MB" -ForegroundColor White
Write-Host "  • Build Time: $([math]::Round($BuildDuration, 2))s" -ForegroundColor White
if ($Installer -and $InnoSetupPath -and (Test-Path (Join-Path $DistDir "Polylog-Setup-$Version.exe"))) {
    Write-Host "  • Installer: Created ✓" -ForegroundColor White
} else {
    Write-Host "  • Installer: Not created" -ForegroundColor White
}
Write-Host ""

Write-Host "Distribution Options:" -ForegroundColor Yellow
Write-Host "  1. Folder: Copy 'dist\Polylog\' folder and distribute" -ForegroundColor White
if ($Installer -and (Test-Path (Join-Path $DistDir "Polylog-Setup-$Version.exe"))) {
    Write-Host "  2. Installer: Distribute 'Polylog-Setup-$Version.exe'" -ForegroundColor White
}
Write-Host ""
Write-Host "No Python installation needed on target machines!" -ForegroundColor Green
Write-Host ""
