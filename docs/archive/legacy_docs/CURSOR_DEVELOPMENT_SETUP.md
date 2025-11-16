# Cursor Development Setup - Complete Guide

## 🚀 One-Command Development

```bash
python scripts/unified_launcher.py dev
```

**That's it!** This single command:
- ✅ Starts API server (http://localhost:8000)
- ✅ Starts frontend dev server (http://localhost:5173)
- ✅ Runs visual tests in watch mode
- ✅ Opens browser automatically
- ✅ Hot reload on every change

**No desktop app needed** - everything runs in browser with instant visual feedback.

---

## 📋 What You Get

### Visual Feedback
- Browser opens automatically showing your app
- Changes appear instantly (hot reload)
- Visual tests run automatically
- Console shows errors/warnings

### Development Tools
- API server with auto-reload
- Frontend with Vite hot module replacement
- Playwright visual tests watching for changes
- All running in background

### No Context Switching
- Everything in Cursor
- Browser shows live updates
- No need to launch desktop app
- No need to switch workspaces

---

## 🎯 Polyform Generator Development

### Quick Start
```bash
# Start development
python scripts/unified_launcher.py dev

# Browser opens automatically
# Start coding - changes appear instantly
```

### Key Files
- `src/frontend/src/components/BabylonScene.jsx` - 3D visualization
- `src/frontend/src/components/PolyhedraLibrary.jsx` - Polygon selector
- `src/frontend/src/components/AttachmentValidator.jsx` - Attachment validation
- `src/polylog6/api/main.py` - API endpoints

### Testing
- Visual tests run automatically
- Integration tests: `python scripts/unified_launcher.py test:integration`
- Performance: `python scripts/unified_launcher.py benchmark`

---

## 🔧 Additional Commands

### Testing
```bash
python scripts/unified_launcher.py test              # All tests
python scripts/unified_launcher.py test:visual        # Visual tests
python scripts/unified_launcher.py test:integration   # Integration tests
```

### Optimization
```bash
python scripts/unified_launcher.py benchmark   # Performance benchmarks
python scripts/unified_launcher.py optimize     # Validate optimizations
python scripts/unified_launcher.py monitor     # System monitoring
```

### Building
```bash
python scripts/unified_launcher.py build       # Build for production
python scripts/unified_launcher.py package     # Create distributable
```

---

## 📁 Project Structure

```
src/
  polylog6/          # Python backend
    api/             # FastAPI endpoints
  frontend/          # React + Babylon.js
    src/
      components/    # React components
      services/      # API services
      tests/         # Test suites
  desktop/           # Tauri desktop app (optional)

scripts/
  unified_launcher.py    # Main launcher
  dev_integrated.py      # Integrated dev script
  optimization_tasks.py # Optimization tools
```

---

## 💡 Tips

1. **Keep browser open** - It shows live updates
2. **Check console** - Browser DevTools for errors
3. **Network tab** - Monitor API calls
4. **Visual tests** - Run automatically, check terminal
5. **Hot reload** - Changes appear instantly

---

## 🧹 Cleanup (Optional)

To remove legacy files:
```bash
python scripts/cleanup_legacy.py --yes
```

This removes:
- Legacy TypeScript files from root
- Old batch scripts
- Pasted content files
- Duplicate documentation

---

## ✅ Success Checklist

- [ ] `python scripts/unified_launcher.py install` - Dependencies installed
- [ ] `python scripts/unified_launcher.py dev` - Dev environment starts
- [ ] Browser opens automatically
- [ ] Changes appear instantly
- [ ] Visual tests running
- [ ] Ready to develop!

---

**Focus**: Develop polyform generator with continuous visual feedback, all in Cursor

