# Polylog6 Development Guide

## Quick Start

```bash
# Start integrated development (everything in one command)
python scripts/unified_launcher.py dev
```

**This starts:**
- ✅ API server (http://localhost:8000)
- ✅ Frontend dev server (http://localhost:5173) 
- ✅ Visual test watcher
- ✅ Opens browser automatically

**No desktop app needed** - everything runs in browser with hot reload.

---

## Development Commands

### Core Development
```bash
python scripts/unified_launcher.py dev          # Integrated dev environment
python scripts/unified_launcher.py desktop     # Desktop app (if needed)
```

### Testing
```bash
python scripts/unified_launcher.py test              # All tests
python scripts/unified_launcher.py test:visual        # Visual tests
python scripts/unified_launcher.py test:integration  # Integration tests
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

## Project Structure

```
src/
  polylog6/          # Python backend
    api/             # FastAPI endpoints
    detection/       # Pattern detection
    simulation/      # Geometry simulation
    compression/     # Unicode compression
  frontend/          # React + Babylon.js
    src/
      components/    # React components
      services/      # API services
      tests/         # Test suites
  desktop/           # Tauri desktop app
    src-tauri/       # Rust backend

scripts/
  unified_launcher.py    # Main launcher
  dev_integrated.py      # Integrated dev script
  optimization_tasks.py  # Optimization tools

tests/               # Backend tests
docs/                # Documentation
```

---

## Polyform Generator Development

See `POLYFORM_GENERATOR_DEV.md` for focused generator development guide.

**Key Areas:**
- Attachment validation
- Edge matching
- Stability scoring
- Tier promotion
- 3D visualization

---

## Testing Strategy

### Visual Tests (Continuous)
- Run automatically during development
- Screenshot comparison
- Component rendering validation

### Integration Tests
- Full system workflows
- API integration
- Data flow validation

### Performance Tests
- FPS monitoring
- API latency
- Memory usage

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Rendering FPS | 60+ |
| API Response | < 100ms |
| Memory Usage | < 500MB |
| LOD Transition | < 20ms |

---

## Tips

- **Hot Reload**: Changes appear instantly in browser
- **Console**: Check browser DevTools for errors
- **Network Tab**: Monitor API calls
- **Visual Tests**: Run continuously for feedback

---

**Focus**: Develop with continuous visual feedback in Cursor

