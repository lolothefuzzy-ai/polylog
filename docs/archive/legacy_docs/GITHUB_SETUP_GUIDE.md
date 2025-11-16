# GitHub Repository Setup & Automated Push Workflow

## Step-by-Step Guide to Connect Your Cursor Project to GitHub

### Prerequisites
- GitHub account (create at https://github.com if needed)
- Git installed (check with `git --version`)
- Your project code ready in Cursor

---

## Part 1: Initial GitHub Repository Setup

### Step 1: Create GitHub Repository

1. **Go to GitHub**: https://github.com/new
2. **Repository Name**: `polylog-visualizer` (or your preferred name)
3. **Description**: "Interactive visualization tool for Polylog6 polyform generator"
4. **Visibility**: 
   - ✅ **Public** (if you want to share)
   - ✅ **Private** (if you want it private)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click **"Create repository"**

### Step 2: Get Your Repository URL

After creating, GitHub will show you the repository URL. It will look like:
```
https://github.com/YOUR_USERNAME/polylog-visualizer.git
```

**Copy this URL** - you'll need it in the next steps.

---

## Part 2: Connect Local Project to GitHub

### Step 3: Initialize Git (if not already done)

```bash
# In Cursor terminal (Ctrl+` or Cmd+`)
cd C:\Users\Nauti\Desktop\Cursor

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Polylog Visualizer from Cursor"
```

### Step 4: Connect to Remote Repository

```bash
# Add your GitHub repository as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/polylog-visualizer.git

# Verify connection
git remote -v
```

**Expected Output**:
```
origin  https://github.com/YOUR_USERNAME/polylog-visualizer.git (fetch)
origin  https://github.com/YOUR_USERNAME/polylog-visualizer.git (push)
```

### Step 5: Push to GitHub

```bash
# Rename default branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**Note**: If this is your first time, GitHub may prompt for authentication:
- **Option A**: Use GitHub CLI (`gh auth login`)
- **Option B**: Use Personal Access Token (see Authentication section below)

---

## Part 3: Authentication Setup

### Option A: GitHub CLI (Recommended)

```bash
# Install GitHub CLI if not installed
# Windows: winget install GitHub.cli
# Or download from: https://cli.github.com

# Authenticate
gh auth login

# Follow prompts:
# 1. Choose "GitHub.com"
# 2. Choose "HTTPS"
# 3. Authenticate via browser
```

### Option B: Personal Access Token

1. **Create Token**:
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name: "Cursor Development"
   - Expiration: 90 days (or your preference)
   - Scopes: Check ✅ `repo` (full control of private repositories)
   - Click "Generate token"
   - **COPY THE TOKEN** (you won't see it again!)

2. **Use Token**:
   ```bash
   # When pushing, use token as password
   # Username: YOUR_GITHUB_USERNAME
   # Password: YOUR_TOKEN
   ```

3. **Store Credentials** (Windows):
   ```bash
   # Configure Git credential helper
   git config --global credential.helper wincred
   ```

---

## Part 4: Automated Push Workflow

### Option 1: Git Hooks (Automatic on Commit)

Create a post-commit hook that automatically pushes:

```bash
# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create post-commit hook
```

**File**: `.git/hooks/post-commit` (create this file)

```bash
#!/bin/sh
# Auto-push to GitHub after commit

echo "🚀 Auto-pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
else
    echo "❌ Push failed. Check your connection and try: git push origin main"
fi
```

**Make it executable** (Windows PowerShell):
```powershell
# Note: Git hooks work differently on Windows
# You may need to use Git Bash or create a .bat file instead
```

**Windows Alternative**: Create `.git/hooks/post-commit.bat`:
```batch
@echo off
echo 🚀 Auto-pushing to GitHub...
git push origin main
if %errorlevel% equ 0 (
    echo ✅ Successfully pushed to GitHub!
) else (
    echo ❌ Push failed. Check your connection.
)
```

### Option 2: PowerShell Script (Manual Trigger)

**File**: `push-to-github.ps1` (create in project root)

```powershell
# Automated GitHub Push Script
# Usage: .\push-to-github.ps1 "Your commit message"

param(
    [Parameter(Mandatory=$true)]
    [string]$CommitMessage
)

Write-Host "🔄 Starting automated push workflow..." -ForegroundColor Cyan

# Check if there are changes
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "⚠️  No changes to commit." -ForegroundColor Yellow
    exit 0
}

# Add all changes
Write-Host "📦 Staging changes..." -ForegroundColor Cyan
git add .

# Commit
Write-Host "💾 Committing changes..." -ForegroundColor Cyan
git commit -m $CommitMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Commit failed!" -ForegroundColor Red
    exit 1
}

# Push to GitHub
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "🔗 View at: https://github.com/YOUR_USERNAME/polylog-visualizer" -ForegroundColor Cyan
} else {
    Write-Host "❌ Push failed. Check your connection." -ForegroundColor Red
    exit 1
}
```

**Usage**:
```powershell
.\push-to-github.ps1 "Fixed polygon geometry calculation"
```

### Option 3: npm Script (Package.json Integration)

Add to your `package.json`:

```json
{
  "scripts": {
    "push": "git add . && git commit -m \"Auto-commit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')\" && git push origin main",
    "push:msg": "node -e \"const msg = process.argv[1]; require('child_process').execSync(`git add . && git commit -m \\\"${msg}\\\" && git push origin main`, {stdio: 'inherit'})\""
  }
}
```

**Usage**:
```bash
npm run push
# Or with custom message:
npm run push:msg "Your commit message here"
```

### Option 4: GitHub Actions (CI/CD)

**File**: `.github/workflows/auto-push.yml` (create this file)

```yaml
name: Auto Push on Schedule

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:  # Manual trigger

jobs:
  push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure Git
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
      
      - name: Push changes
        run: |
          git add .
          git commit -m "Auto-commit: $(date)" || exit 0
          git push
```

---

## Part 5: Daily Workflow

### Recommended Workflow

1. **Make Changes** in Cursor
2. **Stage Changes**:
   ```bash
   git add .
   ```
3. **Commit**:
   ```bash
   git commit -m "Description of changes"
   ```
4. **Push** (choose one method):
   ```bash
   # Manual
   git push origin main
   
   # Or use script
   .\push-to-github.ps1 "Description of changes"
   
   # Or use npm
   npm run push
   ```

### Quick Commands Reference

```bash
# Check status
git status

# See what changed
git diff

# Add specific file
git add filename.ts

# Commit with message
git commit -m "Your message"

# Push to GitHub
git push origin main

# Pull latest changes
git pull origin main

# View commit history
git log --oneline

# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main
```

---

## Part 6: Troubleshooting

### Issue: "Permission denied (publickey)"

**Solution**: Use HTTPS instead of SSH
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/polylog-visualizer.git
```

### Issue: "Authentication failed"

**Solution**: 
1. Check your GitHub token is valid
2. Update stored credentials:
   ```bash
   git credential-manager-core erase
   # Then push again and enter new credentials
   ```

### Issue: "Updates were rejected"

**Solution**: Pull latest changes first
```bash
git pull origin main --rebase
git push origin main
```

### Issue: "Large file" errors

**Solution**: Add large files to `.gitignore` or use Git LFS
```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.pdf"
git lfs track "*.png"
```

---

## Part 7: Best Practices

### Commit Messages

Use clear, descriptive messages:
```bash
✅ Good: "Fix polygon edge snapping calculation"
✅ Good: "Add tetrahedron assembly validation"
❌ Bad: "fix"
❌ Bad: "update"
```

### Branch Strategy

```bash
# Main branch for stable code
git checkout main

# Feature branches for new work
git checkout -b feature/3d-rendering
# ... make changes ...
git commit -m "Add 3D rendering with THREE.js"
git push origin feature/3d-rendering
# Then create Pull Request on GitHub
```

### Regular Pushes

- Push at least once per day
- Push after completing a feature
- Push before switching tasks
- Never push broken code to main branch

---

## Quick Start Checklist

- [ ] GitHub account created
- [ ] Repository created on GitHub
- [ ] Git initialized locally (`git init`)
- [ ] Remote added (`git remote add origin ...`)
- [ ] Authentication configured (CLI or token)
- [ ] Initial push completed (`git push -u origin main`)
- [ ] Automated push script created (optional)
- [ ] Daily workflow established

---

## Next Steps

1. ✅ Your code is now on GitHub!
2. 📖 Read `WINDSURF_MIGRATION_GUIDE.md` for porting to Windsurf
3. 🔄 Set up automated push workflow
4. 👥 Invite collaborators (Settings → Collaborators)
5. 📝 Enable GitHub Issues for bug tracking

---

**Need Help?**
- GitHub Docs: https://docs.github.com
- Git Docs: https://git-scm.com/doc
- Ask in Cursor: Press `Cmd+L` and ask Claude!

