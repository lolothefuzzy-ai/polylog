<#
.SYNOPSIS
Downloads Netlib polyhedra database without external dependencies

.DESCRIPTION
Uses PowerShell's built-in Invoke-WebRequest to fetch Netlib files
Creates a JSON bundle that can be imported into the workspace

.EXAMPLE
./generate_netlib_bundle.ps1
#>

$ErrorActionPreference = "Stop"

# Configuration
$baseUrl = "https://netlib.org/polyhedra/"
$outputFile = "netlib_bundle.json"
$files = 0..141  # All Netlib polyhedra files

# Create bundle structure
$bundle = @{
    meta = @{
        source = $baseUrl
        generated = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    }
    polyhedra = @{}
}

# Download each file
foreach ($id in $files) {
    $url = "${baseUrl}${id}"
    $filename = "${id}.txt"
    
    try {
        Write-Host "Downloading $filename..." -NoNewline
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -ErrorAction Stop
        $bundle.polyhedra[$id] = $response.Content
        Write-Host " ✓" -ForegroundColor Green
    }
    catch {
        Write-Host " ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Save bundle
$bundle | ConvertTo-Json -Depth 5 | Out-File $outputFile

Write-Host ""
Write-Host "✓ Bundle created: $outputFile" -ForegroundColor Green
Write-Host "Contains $($bundle.polyhedra.Count)/142 polyhedra files"
Write-Host "Copy to data/polyhedra/external/netlib/raw/ in your workspace"
