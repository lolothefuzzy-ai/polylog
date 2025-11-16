# Desktop Application Launcher Guide

## Quick Start

### 1. Install Everything
```bash
python scripts/unified_launcher.py install
```

### 2. Launch Desktop App
```bash
python scripts/unified_launcher.py desktop
```

This single command:
- ✅ Starts Python API server (background)
- ✅ Starts frontend dev server
- ✅ Launches Tauri desktop window
- ✅ Opens visual testing environment

---

## Available Commands

### Development
```bash
python scripts/unified_launcher.py desktop      # Full desktop app
python scripts/unified_launcher.py dev:api     # API only
python scripts/unified_launcher.py dev:frontend # Frontend only
```

### Building
```bash
python scripts/unified_launcher.py build        # Build everything
python scripts/unified_launcher.py build:frontend
python scripts/unified_launcher.py build:tauri
```

### Testing
```bash
python scripts/unified_launcher.py test        # All tests
python scripts/unified_launcher.py test:visual  # Visual tests with window
```

### Packaging
```bash
python scripts/unified_launcher.py package     # Create distributable
```

### Utilities
```bash
python scripts/unified_launcher.py clean       # Clean build artifacts
```

---

## Visual Testing

The launcher includes built-in visual testing that opens a browser window:

```bash
python scripts/unified_launcher.py test:visual
```

**What it does:**
1. Starts API server
2. Builds frontend
3. Launches Playwright with headed browser
4. Runs visual tests
5. Shows browser window for debugging

**Test files:**
- `src/frontend/tests/visual/polyhedra-library.spec.js`

---

## Packaging Constraints

### Single Executable
The Tauri build creates a single executable that includes:
- ✅ Frontend (React app)
- ✅ Backend (Python API via sidecar)
- ✅ All dependencies
- ✅ Data catalogs

### File Size
- Expected: ~50-100 MB (depending on platform)
- Includes: Node.js runtime, Python runtime, all assets

### Distribution
After packaging:
```bash
python scripts/unified_launcher.py package
```

**Output:**
- Windows: `.exe` installer
- macOS: `.dmg` or `.app`
- Linux: `.AppImage` or `.deb`

---

## Troubleshooting

### API Not Starting
**Issue**: API server fails to start
**Solution**: 
```bash
# Check Python environment
python scripts/unified_launcher.py install

# Start API manually to see errors
python scripts/unified_launcher.py dev:api
```

### Frontend Build Fails
**Issue**: Frontend won't build
**Solution**:
```bash
cd src/frontend
npm install
npm run build
```

### Tauri Won't Launch
**Issue**: Desktop app doesn't open
**Solution**:
```bash
# Check Rust installation
cargo --version

# Rebuild Tauri
python scripts/unified_launcher.py build:tauri
```

### Visual Tests Fail
**Issue**: Playwright tests fail
**Solution**:
```bash
cd src/frontend
npx playwright install
npm run test:visual
```

---

## Development Workflow

### Daily Development
1. **Start**: `python scripts/unified_launcher.py desktop`
2. **Make changes** in Cursor
3. **See updates** automatically (hot reload)
4. **Test visually** in the window
5. **Commit**: `.\push-to-github.ps1 "Your changes"`

### Before Committing
1. **Run tests**: `python scripts/unified_launcher.py test`
2. **Check linting**: `cd src/frontend && npm run lint`
3. **Verify build**: `python scripts/unified_launcher.py build`

---

## Architecture

```
Desktop App (Tauri)
    ↓
Frontend (React + Babylon.js)
    ↓ HTTP
Backend API (FastAPI)
    ↓
Data Layer (JSONL + SQLite)
```

**All launched by single command!**

---

## Next Steps

1. ✅ Launcher created
2. ✅ Components implemented
3. ⏳ Test with real API
4. ⏳ Verify polyhedron rendering
5. ⏳ Test attachment logic
6. ⏳ Package for distribution

---

**Ready to launch!** 🚀

Run: `python scripts/unified_launcher.py desktop`

