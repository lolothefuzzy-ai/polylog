# Quick Start: Optimization & Continuous Testing

## 🚀 Get Started in 30 Seconds

```bash
# Install everything
python scripts/unified_launcher.py install

# Start development with visual testing
python scripts/unified_launcher.py desktop
```

---

## 📋 Essential Commands

### Development
```bash
python scripts/unified_launcher.py desktop      # Start dev environment
python scripts/unified_launcher.py monitor      # Monitor metrics (separate terminal)
```

### Testing (Run Continuously)
```bash
python scripts/unified_launcher.py test:visual      # Visual regression tests
python scripts/unified_launcher.py test:integration # Full system tests
python scripts/unified_launcher.py test            # All tests
```

### Optimization
```bash
python scripts/unified_launcher.py benchmark   # Performance benchmarks
python scripts/unified_launcher.py optimize     # Validate optimizations
python scripts/unified_launcher.py profile     # Performance profiler
```

---

## 🎯 Daily Workflow

### Morning
1. `git pull origin main`
2. `python scripts/unified_launcher.py test`
3. `python scripts/unified_launcher.py desktop`

### During Development
- **Terminal 1**: `python scripts/unified_launcher.py desktop`
- **Terminal 2**: `python scripts/unified_launcher.py test:visual --watch`
- **Terminal 3**: `python scripts/unified_launcher.py monitor`

### Before Commit
1. `python scripts/unified_launcher.py test`
2. `python scripts/unified_launcher.py benchmark`
3. `python scripts/unified_launcher.py optimize`

---

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Rendering FPS | 60+ |
| API Response | < 100ms |
| Memory Usage | < 500MB |
| LOD Transition | < 20ms |
| Edge Validation | < 5ms |

---

## 🧪 Test Coverage

- ✅ **Visual Tests**: Component rendering, interactions, layouts
- ✅ **Integration Tests**: Full system workflows, API integration
- ✅ **Performance Tests**: FPS, API latency, memory usage
- ✅ **Regression Tests**: Screenshot comparison

---

## 📚 Full Documentation

- `DEVELOPMENT_WORKFLOW.md` - Complete development guide
- `CONTINUOUS_DEVELOPMENT_GUIDE.md` - Continuous testing strategy
- `DESKTOP_APP_README.md` - Desktop application guide

---

**Focus**: Continuous optimization with visual validation for novel systems

