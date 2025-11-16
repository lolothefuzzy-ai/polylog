# Visualizing Test Results in Cursor

## How Tests Work in Cursor

### 1. Visual Tests (Playwright)
When you run visual tests, here's what happens:

```bash
python scripts/unified_launcher.py test:visual
```

**What you'll see:**
- **Terminal output**: Test progress, pass/fail status
- **Browser window**: Opens automatically (headed mode) showing:
  - Your app running
  - Test interactions happening
  - Screenshots being taken
- **HTML Report**: Generated after tests complete

**To see browser:**
- Tests run with `--headed` flag automatically
- Browser window pops up showing your app
- You can watch tests execute in real-time

### 2. Integration Tests
```bash
python scripts/unified_launcher.py test:integration
```

**What you'll see:**
- Terminal output with test results
- Browser opens showing full user workflows
- Network requests visible in DevTools

### 3. Development Mode (Best for Visual Feedback)
```bash
python scripts/unified_launcher.py dev
```

**What happens:**
- Browser opens automatically at http://localhost:5173
- You see your app running live
- Changes appear instantly (hot reload)
- Visual tests run in background (watch mode)
- Console shows test results

### 4. Viewing Test Reports

After tests run, HTML reports are generated:

```bash
# Reports are in:
src/frontend/playwright-report/
```

**To view:**
- Open `playwright-report/index.html` in browser
- Shows all test results with screenshots
- Click any test to see details

### 5. Continuous Testing

During development with `dev` command:
- Visual tests run automatically on file changes
- Results appear in terminal
- Browser stays open showing your app
- No need to manually check - just code and watch terminal

---

## Quick Reference

| Command | What You See |
|---------|-------------|
| `python scripts/unified_launcher.py dev` | Browser opens, app runs, tests watch |
| `python scripts/unified_launcher.py test:visual` | Browser opens, tests run, HTML report |
| `python scripts/unified_launcher.py test:integration` | Browser opens, full workflows tested |

**Best Practice**: Use `dev` command - you get everything in one place with continuous feedback.

