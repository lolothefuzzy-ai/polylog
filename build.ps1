# Build script with absolute paths
$cargoPath = "$env:USERPROFILE\.cargo\bin\cargo"

if (-not (Test-Path $cargoPath)) {
    Write-Error "Cargo not found at $cargoPath"
    exit 1
}

# Build Tauri project
Set-Location src-tauri
& $cargoPath build

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    exit $LASTEXITCODE
}

Write-Host "Build successful"
