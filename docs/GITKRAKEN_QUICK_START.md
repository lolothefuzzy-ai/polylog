# GitKraken Quick Start Guide

## Installation

1. **Download GitKraken**
   - Visit: https://www.gitkraken.com/
   - Download for Windows
   - Install

2. **Open Repository**
   - File → Open Repo
   - Select: `C:\Users\Nauti\Desktop\Cursor`
   - Or clone: `https://github.com/lolothefuzzy-ai/polylog.git`

3. **Connect GitHub** (Optional but Recommended)
   - File → Preferences → Integrations
   - Click "Connect" next to GitHub
   - Authorize GitKraken
   - This enables issue tracking and PR management

## Quick Workflow

### 1. View Current Status
- GitKraken shows all changes visually
- Green = new files
- Yellow = modified files
- Red = deleted files

### 2. Create Feature Branch
**Method 1: In GitKraken**
- Right-click on `main` branch
- Select "Create branch here"
- Name: `feature/tier0-integration`
- Click "Create branch"

**Method 2: Using Script**
```bash
python scripts/gitkraken_workflow_helper.py feature tier0-integration
```

### 3. Stage and Commit
**In GitKraken:**
- Click files to stage (or "Stage all")
- Write commit message: `feat(api): Add Tier 0 API endpoints`
- Click "Commit"

**Using Script:**
```bash
python scripts/gitkraken_workflow_helper.py commit "Add Tier 0 API endpoints" --type feat
```

### 4. Push Branch
- Click "Push" button
- Or right-click branch → Push

### 5. Create Pull Request
**In GitKraken:**
- Right-click branch → "Create Pull Request"
- Fill PR template
- Link to issue (if applicable)
- Click "Create Pull Request"

**Or on GitHub:**
- Go to repository
- Click "Compare & pull request"
- Fill PR template

### 6. Review and Merge
- Reviewers comment in GitKraken or GitHub
- Address feedback
- Merge when approved

## Useful GitKraken Features

### Visual Branch Graph
- See all branches at once
- Understand branch relationships
- Identify merge conflicts early

### Commit History
- Visual commit graph
- Filter by author/date/branch
- Search commits
- Compare branches

### Issue Integration
- View issues in GitKraken
- Link commits to issues
- Auto-close issues on merge
- Track issue progress

### Pull Request Management
- Create PRs easily
- Review code visually
- Comment on changes
- Approve/reject PRs

## Recommended Workflow

### Daily Development
1. **Start:** Pull latest changes
2. **Create Branch:** Feature branch for your work
3. **Work:** Make changes, commit frequently
4. **Push:** Push branch when ready
5. **Create PR:** Create pull request
6. **Review:** Address feedback
7. **Merge:** Merge when approved

### Feature Development
1. Create issue in GitHub
2. Create branch: `feature/description-#issue`
3. Develop feature
4. Commit: `feat(scope): Description\n\nFixes #issue`
5. Push branch
6. Create PR linked to issue
7. Review and merge
8. Issue auto-closes

### Bug Fixes
1. Create issue in GitHub
2. Create branch: `hotfix/description-#issue`
3. Fix bug
4. Commit: `fix(scope): Description\n\nFixes #issue`
5. Create PR (urgent)
6. Review and merge
7. Issue auto-closes

## Tips

### 1. Use Conventional Commits
```
feat(api): Add Tier 0 endpoints
fix(startup): Resolve Python path issue
test(integration): Add interactive workspace monitor
docs: Add GitKraken workflow guide
```

### 2. Link to Issues
Add to commit message footer:
```
Fixes #123
Closes #456
Relates to #789
```

### 3. Small, Frequent Commits
- Commit after each logical change
- Don't wait until feature is complete
- Makes history easier to understand

### 4. Descriptive Branch Names
- `feature/tier0-integration`
- `fix/startup-import-error`
- `test/interactive-workspace-monitor`
- `docs/gitkraken-guide`

### 5. Use PR Templates
- Fill out PR template completely
- Link to issues
- Include test results
- Request specific reviewers

## Troubleshooting

### Can't see repository
- Check repository path
- Verify Git is initialized
- Check permissions

### Can't connect to GitHub
- Check internet connection
- Verify GitHub credentials
- Re-authorize GitKraken

### Merge conflicts
- Use GitKraken's visual merge tool
- Resolve conflicts visually
- Test after resolving

### Can't push
- Check remote configuration
- Verify permissions
- Check for force push restrictions

## Next Steps

1. **Install GitKraken**
2. **Open repository**
3. **Connect GitHub** (optional)
4. **Try creating a branch**
5. **Make a commit**
6. **Create a PR**

## Resources

- GitKraken Documentation: https://help.gitkraken.com/
- GitKraken Tutorials: https://www.gitkraken.com/learn/git
- Conventional Commits: https://www.conventionalcommits.org/

