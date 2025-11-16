# File-by-File Migration Instructions

## 📋 Quick Reference

### Files from Manus (Keep As-Is) ✅

These files work correctly and should be copied directly:

```
✅ App.tsx                    - Main app component
✅ BabylonWorkspace.tsx       - 3D scene setup
✅ Canvas3D.tsx               - Canvas wrapper
✅ Home.tsx                   - Home page
✅ PolygonPalette.tsx         - Polygon selector UI
✅ PolygonSlider.tsx          - Polygon range slider
✅ SnapGuide.tsx              - Visual snap feedback
✅ Workspace.tsx              - Workspace container
✅ Workspace3D.tsx            - 3D workspace logic
✅ attachmentMatrix.ts        - Attachment validation
✅ attachmentResolver.ts      - Edge attachment logic
✅ autoSnap.ts                - Auto-snapping system
✅ edgeSnapping.ts            - Edge snap utilities
✅ edgeSnappingBabylon.ts     - Babylon.js edge snapping
✅ index.css                  - Styles
✅ liaisonGraph.ts            - Polygon connection tracking
✅ main.tsx                   - React entry point
✅ polygon3D.ts               - 3D polygon utilities
✅ polygonGeometry.ts         - Geometry generation
✅ precisePolygonGeometry.ts  - Precise unit polygon gen
```

### Files to REPLACE ⚠️

**CRITICAL**: These files need to be replaced with fixed versions:

```
⚠️  polygonSymbolsV2.ts       - INCOMPLETE in Manus
    Replace with: /outputs/polylog-cursor-migration/src/core/polygonSymbolsV2.ts
    Reason: Missing ALL_SERIES definition, incomplete functions

❓ polygonSymbols.ts          - OLD SYSTEM (A-R sequential)
    Decision: Keep for backward compatibility OR delete
    Recommendation: Keep but mark deprecated
```

### Files to ADD (New) 🆕

These files don't exist in Manus and should be added:

```
🆕 tests/seriesValidation.test.ts - Test suite for ABCD series
🆕 .cursorrules                    - Cursor AI project context
🆕 package.json                    - Dependencies (may exist in Manus)
🆕 tsconfig.json                   - TypeScript config
🆕 vite.config.ts                  - Vite build config
🆕 vitest.config.ts                - Vitest test config
🆕 .gitignore                      - Git ignore patterns
```

---

## 🔧 Detailed Migration Steps

### Step 1: Create Project Structure

```bash
mkdir -p ~/Projects/polylog-visualizer
cd ~/Projects/polylog-visualizer

# Create folder structure
mkdir -p src/components
mkdir -p src/core
mkdir -p src/utils
mkdir -p src/styles
mkdir -p tests
mkdir -p public
```

### Step 2: Copy Manus Files

```bash
# Extract Manus ZIP
unzip ~/Downloads/Polylog6_Architecture_and_Development_code1_.zip -d temp_manus

# Copy to correct locations
cp temp_manus/App.tsx src/components/
cp temp_manus/BabylonWorkspace.tsx src/components/
cp temp_manus/PolygonPalette.tsx src/components/
cp temp_manus/PolygonSlider.tsx src/components/
cp temp_manus/SnapGuide.tsx src/components/
cp temp_manus/Workspace.tsx src/components/
cp temp_manus/Workspace3D.tsx src/components/

# Copy utilities
cp temp_manus/attachmentMatrix.ts src/utils/
cp temp_manus/attachmentResolver.ts src/utils/
cp temp_manus/autoSnap.ts src/utils/
cp temp_manus/edgeSnapping.ts src/utils/
cp temp_manus/edgeSnappingBabylon.ts src/utils/
cp temp_manus/liaisonGraph.ts src/utils/

# Copy core (EXCEPT polygonSymbolsV2.ts - we'll replace that)
cp temp_manus/polygon3D.ts src/core/
cp temp_manus/polygonGeometry.ts src/core/
cp temp_manus/precisePolygonGeometry.ts src/core/
# Skip: temp_manus/polygonSymbolsV2.ts (incomplete)

# Copy styles
cp temp_manus/index.css src/styles/
cp temp_manus/main.tsx src/

# Clean up
rm -rf temp_manus
```

### Step 3: Add Fixed Files from Migration Package

```bash
# Copy the CORRECTED files
cp /mnt/user-data/outputs/polylog-cursor-migration/src/core/polygonSymbolsV2.ts src/core/
cp /mnt/user-data/outputs/polylog-cursor-migration/tests/seriesValidation.test.ts tests/
cp /mnt/user-data/outputs/polylog-cursor-migration/.cursorrules .
cp /mnt/user-data/outputs/polylog-cursor-migration/package.json .
```

### Step 4: Create Configuration Files

**Create `tsconfig.json`**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Create `vite.config.ts`**:
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true
  }
});
```

**Create `vitest.config.ts`**:
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
  },
});
```

**Create `.gitignore`**:
```
node_modules
dist
.DS_Store
*.log
.env
.vite
```

### Step 5: Install Dependencies

```bash
npm install
```

### Step 6: Verify Everything Works

```bash
# Run tests
npm test

# Should see:
# ✓ tests/seriesValidation.test.ts (36 tests)

# Start dev server
npm run dev

# Should open browser at http://localhost:5173
```

---

## 🔍 File Comparison: Old vs New

### polygonSymbolsV2.ts

**Manus Version (BROKEN)**:
```typescript
// ❌ Problem 1: ALL_SERIES not defined
export function getPolygonSides(series: 'A' | 'B' | 'C' | 'D', subscript: number): number {
  const seriesData = ALL_SERIES[series];  // ❌ Undefined!
  return seriesData[subscript - 1];
}

// ❌ Problem 2: toSubscript() not implemented
// Referenced but doesn't exist

// ❌ Problem 3: Series data is in wrong file (polygonSymbols.ts)
// Uses old A-R system, not ABCD
```

**Cursor Version (FIXED)**:
```typescript
// ✅ Series defined at top of file
const SERIES_A = [3, 5, 7, 9, 11, 13, 15, 17, 19];
const SERIES_B = [4, 6, 8, 10, 12, 14, 16, 18, 20];
const SERIES_C = [3, 6, 9, 12, 15, 18, 7, 8, 10];
const SERIES_D = [4, 5, 11, 13, 14, 16, 17, 19, 20];

export const ALL_SERIES = { A: SERIES_A, B: SERIES_B, C: SERIES_C, D: SERIES_D };

// ✅ toSubscript() implemented
export function toSubscript(num: number): string {
  // Full implementation
}

// ✅ Validation function
export function validateSeriesTables(): boolean {
  // Runs on module load
}
```

---

## ⚙️ Import Path Updates Needed

Some files in Manus may have incorrect import paths. Check these:

### BabylonWorkspace.tsx
```typescript
// If you see:
import { getPolygonSides } from './polygonSymbols';  // ❌ Wrong file

// Change to:
import { getPolygonSides } from '../core/polygonSymbolsV2';  // ✅ Correct
```

### PolygonPalette.tsx
```typescript
// If you see:
import { POLYGON_SYMBOLS } from './polygonSymbols';  // ❌ Old system

// Change to:
import { ALL_SERIES, generateSingleSymbol } from '../core/polygonSymbolsV2';  // ✅ New system
```

---

## 🧪 Testing Checklist

After migration, verify each of these works:

### Unit Tests
```bash
npm test

# Should pass:
✓ ABCD Series Tables (5 tests)
✓ Series Lookup Functions (4 tests)
✓ Symbol Generation (4 tests)
✓ Subscript Utilities (3 tests)
✓ Attachment Stability (3 tests)
```

### Visual Tests (in browser)
1. Open http://localhost:5173
2. Polygon palette displays 36 symbols
3. Click A₁ button → Places 3-sided polygon (triangle)
4. Click D₁ button → Places 4-sided polygon (square)
5. Drag polygon → Auto-rotates near edges
6. Right-click edge → Snaps polygon to edge
7. Export button → Downloads JSON

### Console Validation
```javascript
// In browser console:
✅ ABCD Series tables validated successfully
   A₁ = 3 sides (triangle)
   B₁ = 4 sides (square)
   D₁ = 4 sides (square)
```

---

## 🚨 Common Errors & Fixes

### Error 1: "Cannot find module '@babylonjs/core'"
```bash
# Fix:
npm install @babylonjs/core @babylonjs/gui
```

### Error 2: "ALL_SERIES is not defined"
```bash
# Fix: You're using old polygonSymbolsV2.ts
# Replace with fixed version from migration package
```

### Error 3: Tests fail with "A₁ should be 3"
```bash
# Fix: Series tables are in wrong order
# Make sure SERIES_A = [3, 5, 7, ...] not [11, 13, 3, ...]
```

### Error 4: Polygons not visible in scene
```typescript
// Fix in component:
material.backFaceCulling = false;  // Add this line
mesh.material = material;
```

---

## 📦 Final File Manifest

Your completed Cursor project should have:

```
polylog-visualizer/
├── .cursorrules                                ← 🆕 AI context
├── .gitignore                                  ← 🆕 Git ignore
├── package.json                                ← 🆕 Dependencies
├── tsconfig.json                               ← 🆕 TS config
├── vite.config.ts                              ← 🆕 Build config
├── vitest.config.ts                            ← 🆕 Test config
├── README.md                                   ← Update from Manus
├── src/
│   ├── main.tsx                                ← ✅ From Manus
│   ├── components/
│   │   ├── App.tsx                             ← ✅ From Manus
│   │   ├── BabylonWorkspace.tsx                ← ✅ From Manus
│   │   ├── PolygonPalette.tsx                  ← ✅ From Manus (may need import fix)
│   │   ├── PolygonSlider.tsx                   ← ✅ From Manus
│   │   ├── SnapGuide.tsx                       ← ✅ From Manus
│   │   ├── Workspace.tsx                       ← ✅ From Manus
│   │   └── Workspace3D.tsx                     ← ✅ From Manus
│   ├── core/
│   │   ├── polygonSymbolsV2.ts                 ← ⚠️  REPLACE with fixed version
│   │   ├── polygonGeometry.ts                  ← ✅ From Manus
│   │   ├── polygon3D.ts                        ← ✅ From Manus
│   │   └── precisePolygonGeometry.ts           ← ✅ From Manus
│   ├── utils/
│   │   ├── attachmentMatrix.ts                 ← ✅ From Manus
│   │   ├── attachmentResolver.ts               ← ✅ From Manus
│   │   ├── autoSnap.ts                         ← ✅ From Manus
│   │   ├── edgeSnapping.ts                     ← ✅ From Manus
│   │   ├── edgeSnappingBabylon.ts              ← ✅ From Manus
│   │   └── liaisonGraph.ts                     ← ✅ From Manus
│   └── styles/
│       └── index.css                           ← ✅ From Manus
├── tests/
│   └── seriesValidation.test.ts                ← 🆕 From migration package
└── public/                                     ← Create empty folder
```

**File Count**: 
- From Manus (as-is): 21 files
- Fixed/Replaced: 1 file (polygonSymbolsV2.ts)
- New files: 7 files (configs + tests)
- **Total**: 29 files

---

## ✅ Migration Complete Checklist

Before you start developing:

- [ ] All 21 Manus files copied to correct folders
- [ ] Fixed `polygonSymbolsV2.ts` in place
- [ ] New test file added
- [ ] `.cursorrules` file created
- [ ] Configuration files created (tsconfig, vite, vitest)
- [ ] `npm install` completed successfully
- [ ] `npm test` shows 36 passing tests
- [ ] `npm run dev` opens working application
- [ ] Polygon palette shows correct symbols
- [ ] A₁ generates triangle, D₁ generates square
- [ ] Git repository initialized
- [ ] First commit made

**If all checked**: You're ready to develop in Cursor! 🎉

---

**Next Step**: Open project in Cursor and press `Cmd+L` to start chatting with Claude about your code!
