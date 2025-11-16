# Connect Cursor Workspace to Existing GitHub Repository
# Usage: .\connect-to-github.ps1 "https://github.com/YOUR_USERNAME/REPO_NAME.git"

param(
    [Parameter(Mandatory=$true)]
    [string]$RepositoryUrl
)

Write-Host "🔄 Connecting to existing GitHub repository..." -ForegroundColor Cyan
Write-Host ""

# Check if Git is initialized
if (-not (Test-Path .git)) {
    Write-Host "⚠️  Git not initialized. Initializing now..." -ForegroundColor Yellow
    git init
}

# Check if remote already exists
$existingRemote = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠️  Remote 'origin' already exists: $existingRemote" -ForegroundColor Yellow
    $response = Read-Host "Replace with new remote? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        git remote remove origin
        Write-Host "✅ Removed existing remote" -ForegroundColor Green
    } else {
        Write-Host "❌ Cancelled. Keeping existing remote." -ForegroundColor Red
        exit 0
    }
}

# Add remote
Write-Host "🔗 Adding remote repository..." -ForegroundColor Cyan
Write-Host "   URL: $RepositoryUrl" -ForegroundColor Gray
git remote add origin $RepositoryUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to add remote!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Remote added successfully" -ForegroundColor Green
Write-Host ""

# Verify remote
Write-Host "📍 Verifying remote connection..." -ForegroundColor Cyan
git remote -v
Write-Host ""

# Fetch from remote to see what's there
Write-Host "📥 Fetching from remote repository..." -ForegroundColor Cyan
git fetch origin

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Could not fetch from remote. This might be a new repository." -ForegroundColor Yellow
    Write-Host "   Or you may need to authenticate." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Authenticate: gh auth login" -ForegroundColor Gray
    Write-Host "   2. Try again: git fetch origin" -ForegroundColor Gray
    exit 1
}

# Check what branch exists on remote
$remoteBranches = git branch -r 2>$null
if ($remoteBranches) {
    Write-Host "✅ Found remote branches:" -ForegroundColor Green
    $remoteBranches | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    Write-Host ""
    
    # Determine main branch (main or master)
    $mainBranch = "main"
    if ($remoteBranches -match "origin/master") {
        $mainBranch = "master"
    }
    
    Write-Host "🌿 Detected main branch: $mainBranch" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if we have local changes
    $hasLocalFiles = (Get-ChildItem -File | Where-Object { $_.Name -ne '.git' -and $_.Name -notlike '.git*' }).Count -gt 0
    
    if ($hasLocalFiles) {
        Write-Host "⚠️  You have local files that may conflict with remote." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Options:" -ForegroundColor Cyan
        Write-Host "   1. Stash local changes and pull remote" -ForegroundColor Gray
        Write-Host "   2. Commit local changes first, then merge" -ForegroundColor Gray
        Write-Host "   3. Cancel and handle manually" -ForegroundColor Gray
        Write-Host ""
        $choice = Read-Host "Choose option (1/2/3)"
        
        switch ($choice) {
            "1" {
                Write-Host "📦 Stashing local changes..." -ForegroundColor Cyan
                git add .
                git stash push -m "Local changes before connecting to remote"
                Write-Host "✅ Changes stashed" -ForegroundColor Green
                Write-Host ""
                Write-Host "📥 Pulling from remote..." -ForegroundColor Cyan
                git checkout -b $mainBranch origin/$mainBranch 2>$null
                if ($LASTEXITCODE -ne 0) {
                    git checkout $mainBranch
                    git pull origin $mainBranch
                }
                Write-Host "✅ Pulled from remote" -ForegroundColor Green
                Write-Host ""
                Write-Host "💡 To restore stashed changes: git stash pop" -ForegroundColor Yellow
            }
            "2" {
                Write-Host "💾 Committing local changes..." -ForegroundColor Cyan
                git add .
                git commit -m "Local changes before connecting to remote"
                Write-Host "✅ Changes committed" -ForegroundColor Green
                Write-Host ""
                Write-Host "📥 Pulling from remote..." -ForegroundColor Cyan
                git branch -M $mainBranch
                git pull origin $mainBranch --allow-unrelated-histories
                Write-Host "✅ Merged with remote" -ForegroundColor Green
            }
            "3" {
                Write-Host "ℹ️  Manual setup required." -ForegroundColor Yellow
                Write-Host ""
                Write-Host "Commands to run:" -ForegroundColor Cyan
                Write-Host "   git branch -M $mainBranch" -ForegroundColor Gray
                Write-Host "   git pull origin $mainBranch --allow-unrelated-histories" -ForegroundColor Gray
                exit 0
            }
        }
    } else {
        # No local files, just pull
        Write-Host "📥 Pulling from remote..." -ForegroundColor Cyan
        git checkout -b $mainBranch origin/$mainBranch 2>$null
        if ($LASTEXITCODE -ne 0) {
            git branch -M $mainBranch
            git pull origin $mainBranch
        }
        Write-Host "✅ Pulled from remote" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️  Remote repository appears to be empty or new." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can:" -ForegroundColor Cyan
    Write-Host "   1. Push your local files to create the initial commit" -ForegroundColor Gray
    Write-Host "   2. Or start fresh from remote" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Connection established!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Current status:" -ForegroundColor Cyan
git status
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Cyan
Write-Host "   - Make your changes" -ForegroundColor Gray
Write-Host "   - Commit: git add . && git commit -m 'Your message'" -ForegroundColor Gray
Write-Host "   - Push: git push origin $mainBranch" -ForegroundColor Gray
Write-Host "   - Or use: .\push-to-github.ps1 'Your message'" -ForegroundColor Gray

