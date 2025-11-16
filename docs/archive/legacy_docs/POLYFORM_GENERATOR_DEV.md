# Polyform Generator Development Guide

## Quick Start

```bash
# Start integrated development (everything in one command)
python scripts/dev_integrated.py
```

This starts:
- ✅ API server (http://localhost:8000)
- ✅ Frontend dev server (http://localhost:5173)
- ✅ Visual test watcher
- ✅ Opens browser automatically

**No need to launch desktop app** - everything runs in browser with hot reload.

---

## Development Workflow

### 1. Start Development
```bash
python scripts/dev_integrated.py
```

### 2. Make Changes
- Edit files in `src/frontend/src/`
- Edit API in `src/polylog6/api/`
- Changes auto-reload in browser

### 3. Visual Feedback
- Browser shows live updates
- Visual tests run automatically
- Console shows errors/warnings

### 4. Test Polyform Generator
- Select polygons from library
- Validate attachments
- Generate new polyforms
- Visual feedback in 3D scene

---

## Key Components

### Frontend (`src/frontend/src/`)
- `App.jsx` - Main application
- `components/BabylonScene.jsx` - 3D visualization
- `components/PolyhedraLibrary.jsx` - Polygon selector
- `components/AttachmentValidator.jsx` - Attachment validation
- `services/storageService.ts` - API communication

### Backend (`src/polylog6/api/`)
- `main.py` - FastAPI server
- `tier1_polyhedra.py` - Polyhedra endpoints
- `storage.py` - Storage endpoints

### Generator Logic
- Attachment validation
- Edge matching
- Stability scoring
- Tier promotion

---

## Testing

### Visual Tests (Auto-run)
```bash
# Already running via dev_integrated.py
# Or manually:
cd src/frontend && npm run test:visual
```

### Integration Tests
```bash
python scripts/unified_launcher.py test:integration
```

### Performance
```bash
python scripts/unified_launcher.py benchmark
```

---

## Focus Areas

### 1. Attachment Validation
- Edge-to-edge matching
- Fold angle calculation
- Stability scoring

### 2. Generation Pipeline
- Candidate creation
- Validation
- Tier promotion

### 3. Visualization
- 3D rendering
- LOD switching
- Interactive manipulation

---

## Tips

- **Hot Reload**: Changes appear instantly
- **Console**: Check browser console for errors
- **Network Tab**: Monitor API calls
- **Performance**: Use DevTools profiler

---

**Focus**: Develop polyform generator with continuous visual feedback

