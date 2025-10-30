# Polylog Simulator - Documentation

**Version:** 0.1.0  
**Last Updated:** 2024

Welcome to Polylog Simulator documentation. Start with the guide for your role.

---

## 🚀 Quick Start (30 seconds)

```bash
python main.py
```

**That's it!** You're running Polylog Simulator.

See mode options: `python main.py -h`

---

## 📖 Documentation by Role

### 👤 New Users / First Time
1. **Start here:** [Quick Start](QUICK_START.md)
2. **Learn modes:** `python main.py -h`
3. **Try demo:** `python main.py demo`
4. **Explore:** Try `python main.py api` and visit http://localhost:8000/docs

### 👨‍💻 Developers
1. **Architecture:** [Entry Point Guide](ENTRY_POINT_CLARIFICATION.md)
2. **Code structure:** See `main.py` and `_archive_legacy_code/`
3. **API docs:** Run `python main.py api` → http://localhost:8000/docs
4. **Testing:** `pytest tests/ -v`

### 🔨 Maintainers
1. **Code pruning:** [Phase 1 Pruning](PHASE1_COMPLETE_SUMMARY.md)
2. **System status:** Check git logs and recent commits
3. **Future phases:** [Planning document](PRUNING_ACTION_PLAN.md)

---

## 📚 Documentation Pages

### Getting Started
| Page | Purpose |
|------|---------|
| [QUICK_START.md](QUICK_START.md) | 30-second getting started guide |
| [ENTRY_POINT_CLARIFICATION.md](ENTRY_POINT_CLARIFICATION.md) | How to run Polylog Simulator |

### System Architecture
| Page | Purpose |
|------|---------|
| [ENTRY_POINT_ARCHITECTURE.md](ENTRY_POINT_ARCHITECTURE.md) | Entry point design rationale |
| [USER_EXPERIENCE.md](USER_EXPERIENCE.md) | What users see when they run it |

### Operations & Maintenance
| Page | Purpose |
|------|---------|
| [PHASE1_COMPLETE_SUMMARY.md](PHASE1_COMPLETE_SUMMARY.md) | Code pruning Phase 1 details |
| [PRUNING_ACTION_PLAN.md](PRUNING_ACTION_PLAN.md) | Future cleanup phases |

---

## ⏱️ Common Tasks

### "I want to start Polylog"
```bash
python main.py
```
→ See [QUICK_START.md](QUICK_START.md)

### "I want to use the API"
```bash
python main.py api
```
Then visit: http://127.0.0.1:8000/docs

### "I want to understand the system"
→ Read [ENTRY_POINT_CLARIFICATION.md](ENTRY_POINT_CLARIFICATION.md)

### "I want to run tests"
```bash
pytest tests/ -v
```

### "I want to check code quality"
```bash
ruff check .
black --check .
```

---

## 📂 File Structure

```
Polylog6/
├── main.py                          ← PRIMARY ENTRY POINT
├── DOCS.md                          ← YOU ARE HERE
├── QUICK_START.md
├── ENTRY_POINT_CLARIFICATION.md
├── ENTRY_POINT_ARCHITECTURE.md
├── USER_EXPERIENCE.md
├── PHASE1_COMPLETE_SUMMARY.md
├── PRUNING_ACTION_PLAN.md
│
├── demo_library_integration.py      (Demo mode)
├── polylog_main.py                  (API mode)
├── desktop_app.py                   (GUI - in development)
│
├── tests/                           (Test suite)
├── _archive_legacy_code/            (Old code - for reference)
└── [other modules]
```

---

## ❓ Help

**Don't know where to start?**
→ Run `python main.py` and check the banner

**Need help with a mode?**
→ Run `python main.py -h`

**Want to understand the design?**
→ Read [ENTRY_POINT_ARCHITECTURE.md](ENTRY_POINT_ARCHITECTURE.md)

**Looking for old documentation?**
→ Check git history: `git log --all --oneline --graph`

---

## 🔍 What NOT to Read

The following are outdated work logs and can be ignored:
- `*SESSION*.md` files (work logs, no longer relevant)
- `*STATUS*.md` files (dated progress, check git instead)
- `PHASE_*` numbered files (superseded by Phase 1 summary)
- `*TEST_REPORT*.md` files (check test results instead)

---

## ✅ Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Entry Point | ✅ Clear | Use `main.py` |
| API Server | ✅ Ready | `python main.py api` |
| Demo Mode | ✅ Ready | `python main.py demo` |
| GUI | ⏳ In Progress | Coming soon |
| Tests | ✅ Available | `pytest tests/` |

---

## 🎯 One Command to Remember

```bash
python main.py
```

Everything else flows from there. Questions? Read [QUICK_START.md](QUICK_START.md).
