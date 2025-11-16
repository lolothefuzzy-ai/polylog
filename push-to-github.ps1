# Automated GitHub Push Script for Polylog Visualizer
# Usage: .\push-to-github.ps1 "Your commit message"

param(
    [Parameter(Mandatory=$false)]
    [string]$CommitMessage = "Auto-commit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
)

Write-Host "🔄 Starting automated push workflow..." -ForegroundColor Cyan
Write-Host ""

# Check if Git is initialized
if (-not (Test-Path .git)) {
    Write-Host "❌ Not a Git repository. Run 'git init' first." -ForegroundColor Red
    exit 1
}

# Check if remote is configured
$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  No remote 'origin' configured." -ForegroundColor Yellow
    Write-Host "   Run: git remote add origin https://github.com/YOUR_USERNAME/polylog-visualizer.git" -ForegroundColor Yellow
    exit 1
}

Write-Host "📍 Remote: $remote" -ForegroundColor Gray
Write-Host ""

# Check current branch
$branch = git branch --show-current
Write-Host "🌿 Branch: $branch" -ForegroundColor Gray
Write-Host ""

# Check if there are changes
Write-Host "📊 Checking for changes..." -ForegroundColor Cyan
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "✅ No changes to commit. Repository is up to date." -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 To force push anyway, use: git push origin $branch" -ForegroundColor Gray
    exit 0
}

Write-Host "📝 Changes detected:" -ForegroundColor Cyan
git status --short
Write-Host ""

# Add all changes
Write-Host "📦 Staging all changes..." -ForegroundColor Cyan
git add .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to stage changes!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Changes staged" -ForegroundColor Green
Write-Host ""

# Commit
Write-Host "💾 Committing changes..." -ForegroundColor Cyan
Write-Host "   Message: $CommitMessage" -ForegroundColor Gray
git commit -m $CommitMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Commit failed!" -ForegroundColor Red
    Write-Host "   This might happen if there are no actual changes to commit." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Committed successfully" -ForegroundColor Green
Write-Host ""

# Push to GitHub
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Cyan
git push origin $branch

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    
    # Try to extract GitHub URL
    if ($remote -match "github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$") {
        $username = $matches[1]
        $repo = $matches[2]
        $githubUrl = "https://github.com/$username/$repo"
        Write-Host "🔗 View repository: $githubUrl" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "📊 Latest commit:" -ForegroundColor Gray
    git log -1 --oneline
} else {
    Write-Host ""
    Write-Host "❌ Push failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Common solutions:" -ForegroundColor Yellow
    Write-Host "   1. Check your internet connection" -ForegroundColor Yellow
    Write-Host "   2. Verify GitHub authentication:" -ForegroundColor Yellow
    Write-Host "      gh auth login" -ForegroundColor Gray
    Write-Host "   3. Pull latest changes first:" -ForegroundColor Yellow
    Write-Host "      git pull origin $branch --rebase" -ForegroundColor Gray
    Write-Host "   4. Check remote URL:" -ForegroundColor Yellow
    Write-Host "      git remote -v" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "✨ Done!" -ForegroundColor Green

