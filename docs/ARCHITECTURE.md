# Polylog6 Architecture

**Single source of truth for system architecture. Links to code, not more docs.**

## CPU/GPU Boundary

```
┌─────────────────────────────────────────────────────────┐
│ CPU (Backend - Python FastAPI :8000)                    │
│ - Tier0 encoding/decoding (Series A/B/C/D)              │
│ - Geometry computation (Netlib)                         │
│ - Storage (Unicode compression)                         │
│ - Detection pipeline (Track A)                          │
│ - Monitoring loop (Track B)                              │
├─────────────────────────────────────────────────────────┤
│ GPU (Frontend - React + Babylon.js :5173)                │
│ - 3D rendering (BabylonScene.jsx)                       │
│ - Workspace state (workspaceManager.js)                 │
│ - GPU buffer management (gpuBufferManager.js)           │
│ - Polygon interaction (polygonInteraction.js)            │
└─────────────────────────────────────────────────────────┘
```

**Key Files:**

- Backend API: `src/polylog6/api/main.py`
- Frontend renderer: `src/frontend/src/components/BabylonScene.jsx`
- GPU buffers: `src/frontend/src/utils/gpuBufferManager.js`

## Tier0 Symbol Flow

```
User Input → Tier0 Encoder → Backend API → Unicode Decode → Babylon.js Render
    ↓              ↓              ↓              ↓                ↓
  Polygon      Series A/B    POST /tier0/   decode()      PolyformMesh
  placement    encoding      encode        Unicode →      .getMesh()
                                    geometry
```

**Code Path:**

1. **Input**: `src/frontend/src/utils/tier0Encoder.js` - User places polygon
2. **Encode**: `src/polylog6/storage/tier0_generator.py` - Series A/B/C/D encoding
3. **API**: `src/polylog6/api/tier0.py` - `/tier0/encode` endpoint
4. **Decode**: `src/frontend/src/utils/UnicodeDecoder.ts` - Unicode → geometry
5. **Render**: `src/frontend/src/components/BabylonScene.jsx` - Babylon.js mesh

**Current Blocker**: `UnicodeDecoder.ts` line 107 uses port `8008` instead of `8000`.

## Track A & Track B

```
┌─────────────────────────────────────────────────────────┐
│ Track A: Detection Pipeline (CPU)                      │
│                                                          │
│ Image → Segment → Pattern → Candidate → Optimize       │
│   ↓         ↓         ↓          ↓           ↓          │
│ ImageSeg  Pattern  Candidate  Optimizer  Result         │
│ menter    Analyzer Generator                            │
│                                                          │
│ Code: src/polylog6/detection/service.py                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Track B: Monitoring Loop (CPU)                          │
│                                                          │
│ ContextBrief → LibraryRefresh → Telemetry → Alerts     │
│     ↓              ↓             ↓           ↓          │
│  Tailer      RefreshWorker  Telemetry  AlertSink       │
│                          Bridge                         │
│                                                          │
│ Code: src/polylog6/monitoring/loop.py                  │
└─────────────────────────────────────────────────────────┘
```

**Track A** = Image-to-polygon detection (active development)  
**Track B** = Background monitoring/telemetry (runs alongside)

## File Structure

```
polylog6/
├── scripts/
│   ├── dev.py          # Start API + Frontend
│   ├── test.py         # Run all tests
│   └── build.py        # Build for production
├── src/
│   ├── polylog6/       # Backend (Python)
│   │   ├── api/        # FastAPI endpoints
│   │   ├── detection/  # Track A
│   │   ├── monitoring/ # Track B
│   │   └── storage/    # Tier0/1/2/3 encoding
│   ├── frontend/       # Frontend (React + Babylon.js)
│   │   └── src/
│   │       ├── components/  # BabylonScene, etc.
│   │       └── utils/      # UnicodeDecoder, tier0Encoder
│   └── desktop/        # Tauri wrapper (Rust)
├── data/
│   └── catalogs/       # Single source: tier0, tier1, attachments
└── docs/
    └── ARCHITECTURE.md # This file (only essential doc)
```

## Critical Code References

**Tier0 Encoding:**

- `src/polylog6/storage/tier0_generator.py` - Series A/B/C/D encoding
- `src/frontend/src/utils/tier0Encoder.js` - Frontend encoder

**Unicode Decoding:**

- `src/frontend/src/utils/UnicodeDecoder.ts` - **FIX: port 8008 → 8000**
- `src/polylog6/storage/unicode_library.py` - Backend decoder

**3D Rendering:**

- `src/frontend/src/components/BabylonScene.jsx` - Main renderer
- `src/frontend/src/utils/PolyformMesh.ts` - Mesh creation

**API Endpoints:**

- `src/polylog6/api/main.py` - FastAPI app
- `src/polylog6/api/tier0.py` - Tier0 endpoints

**Detection (Track A):**

- `src/polylog6/detection/service.py` - Main detection service

**Monitoring (Track B):**

- `src/polylog6/monitoring/loop.py` - Monitoring dispatcher

## Next Steps

1. **Fix UnicodeDecoder port** (line 107: `8008` → `8000`)
2. **Remove duplicate `src/UnicodeDecoder.ts`** (root level)
3. **Consolidate `catalogs/` → `data/catalogs/`**
4. **Archive 50+ scripts → 3 scripts** (dev, test, build)
