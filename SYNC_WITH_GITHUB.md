# Sync Cursor Workspace with Existing GitHub Repository

## Quick Setup

You have an existing GitHub repository set up in Windsurf, and you want to develop in Cursor. Here's how to connect them.

---

## Step 1: Get Your Repository URL

### From Windsurf:
1. Open your project in Windsurf
2. Open terminal: `Ctrl+\``
3. Run: `git remote -v`
4. Copy the URL (looks like: `https://github.com/USERNAME/REPO.git`)

### From GitHub:
1. Go to your repository on GitHub
2. Click green "Code" button
3. Copy the HTTPS URL

---

## Step 2: Connect Cursor to GitHub

### Option A: Use the Script (Easiest)

```powershell
# Run the connection script
.\connect-to-github.ps1 "https://github.com/YOUR_USERNAME/YOUR_REPO.git"
```

The script will:
- ✅ Add the remote repository
- ✅ Fetch existing files
- ✅ Handle local file conflicts
- ✅ Set up the connection

### Option B: Manual Setup

```powershell
# 1. Add remote (replace with your URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 2. Verify
git remote -v

# 3. Fetch from remote
git fetch origin

# 4. Check what branch exists
git branch -r

# 5. Pull the files (replace 'main' with your branch name if different)
git pull origin main --allow-unrelated-histories
```

---

## Step 3: Handle File Conflicts

If you have local files that conflict with remote:

### Option 1: Keep Remote Files (Recommended)
```powershell
# Stash local changes
git add .
git stash

# Pull remote files
git pull origin main

# Review stashed changes later
git stash list
git stash show -p stash@{0}  # Preview
git stash pop  # Apply if needed
```

### Option 2: Merge Both
```powershell
# Commit local changes first
git add .
git commit -m "Local changes before sync"

# Pull and merge
git pull origin main --allow-unrelated-histories

# Resolve any conflicts manually
# Then commit the merge
git add .
git commit -m "Merged local and remote files"
```

### Option 3: Keep Local, Overwrite Remote
```powershell
# Commit local changes
git add .
git commit -m "Local development files"

# Force push (⚠️ overwrites remote!)
git push origin main --force
```

---

## Step 4: Verify Connection

```powershell
# Check remote
git remote -v

# Check status
git status

# View commit history
git log --oneline -10
```

---

## Daily Development Workflow

### 1. Start Work Session
```powershell
# Pull latest from GitHub (in case Windsurf made changes)
git pull origin main
```

### 2. Make Changes
- Edit files in Cursor
- Test your changes
- Save files

### 3. Commit & Push
```powershell
# Option A: Use automated script
.\push-to-github.ps1 "Description of changes"

# Option B: Manual
git add .
git commit -m "Description of changes"
git push origin main
```

### 4. Continue in Windsurf
- Open project in Windsurf
- Pull latest: `git pull origin main`
- Your Cursor changes are now available!

---

## Working with Both Editors

### Best Practices

1. **Always Pull First**
   ```powershell
   # In Cursor, before starting work
   git pull origin main
   ```

2. **Push When Done**
   ```powershell
   # In Cursor, when finished
   git push origin main
   ```

3. **Use Branches for Big Features**
   ```powershell
   # Create feature branch
   git checkout -b feature/new-feature
   
   # Work on feature
   # ... make changes ...
   
   # Commit
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   
   # Merge on GitHub or in Windsurf
   ```

### Conflict Resolution

If both editors modified the same file:

```powershell
# Pull will show conflicts
git pull origin main

# Git will mark conflicts like this:
# <<<<<<< HEAD
# Your Cursor changes
# =======
# Windsurf changes
# >>>>>>> origin/main

# Edit file to resolve, then:
git add .
git commit -m "Resolved merge conflicts"
git push origin main
```

---

## Quick Commands Reference

```powershell
# Check connection
git remote -v

# Pull latest
git pull origin main

# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "Your message"

# Push
git push origin main

# View history
git log --oneline

# Create branch
git checkout -b feature-name

# Switch branches
git checkout main
```

---

## Troubleshooting

### Issue: "Repository not found"

**Solution**: Check the URL is correct
```powershell
git remote -v
git remote set-url origin https://github.com/CORRECT_USERNAME/CORRECT_REPO.git
```

### Issue: "Authentication failed"

**Solution**: Authenticate with GitHub
```powershell
gh auth login
# Or use personal access token
```

### Issue: "Updates were rejected"

**Solution**: Pull first, then push
```powershell
git pull origin main --rebase
git push origin main
```

### Issue: "Unrelated histories"

**Solution**: Use allow-unrelated-histories flag
```powershell
git pull origin main --allow-unrelated-histories
```

---

## Next Steps

1. ✅ Connect to GitHub repository
2. ✅ Pull existing files
3. ✅ Start developing in Cursor
4. ✅ Push changes back to GitHub
5. ✅ Continue development in either editor!

---

**You're all set! 🚀**

Your Cursor workspace is now connected to your GitHub repository, and you can develop here while keeping everything synced with Windsurf.

