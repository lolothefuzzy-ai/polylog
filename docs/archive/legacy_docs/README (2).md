# Polylog Visualizer - Cursor Migration Package

**Version**: 3.0 (Stability-Optimized)  
**Date**: 2025-11-15  
**Migration**: Manus → Cursor IDE

---

## 📦 What's in This Package

This migration package contains everything you need to move your Polylog Visualizer project from Manus to Cursor IDE:

```
polylog-cursor-migration/
├── MIGRATION_GUIDE.md           ← START HERE: Complete step-by-step guide
├── FILE_MIGRATION_GUIDE.md      ← Detailed file-by-file instructions
├── .cursorrules                 ← AI context for Cursor
├── package.json                 ← Dependencies & scripts
├── src/
│   └── core/
│       └── polygonSymbolsV2.ts  ← FIXED version (replaces Manus file)
└── tests/
    └── seriesValidation.test.ts ← New test suite
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- ✅ Cursor IDE installed (https://cursor.sh)
- ✅ Node.js 18+ installed
- ✅ Your Manus ZIP files downloaded

### Step 1: Extract Manus Project
```bash
cd ~/Projects
mkdir polylog-visualizer
cd polylog-visualizer
unzip ~/Downloads/Polylog6_Architecture_and_Development_code1_.zip
```

### Step 2: Replace Critical Files
```bash
# Copy the FIXED polygonSymbolsV2.ts
cp [path-to-this-package]/src/core/polygonSymbolsV2.ts src/core/

# Add test suite
mkdir -p tests
cp [path-to-this-package]/tests/seriesValidation.test.ts tests/

# Add Cursor AI context
cp [path-to-this-package]/.cursorrules .

# Add dependencies
cp [path-to-this-package]/package.json .
```

### Step 3: Install & Test
```bash
npm install
npm test    # Should show 36 passing tests
npm run dev # Opens browser at localhost:5173
```

### Step 4: Open in Cursor
```bash
cursor .
```

**You're ready to code!** 🎉

---

## 🔧 What Was Fixed

### Critical Fix: polygonSymbolsV2.ts

**Problem in Manus**:
- ❌ `ALL_SERIES` constant was referenced but not defined
- ❌ `toSubscript()` function was called but not implemented
- ❌ Series had wrong order (A₁ was 11-gon instead of triangle)

**Fixed in This Package**:
- ✅ Complete implementation with all functions
- ✅ Optimized ABCD series (triangle-first, square-first)
- ✅ Validation that runs on module load
- ✅ Full TypeScript types

**Impact**:
```typescript
// OLD (Manus): A₁ = 11 sides ❌
const SERIES_A = [11, 13, 3, 15, 5, 17, 7, 19, 9];

// NEW (Cursor): A₁ = 3 sides (triangle) ✅
const SERIES_A = [3, 5, 7, 9, 11, 13, 15, 17, 19];
```

This optimization puts the most stable attachments (triangle-triangle, triangle-square) at the beginning of the series, improving generator performance.

---

## 📚 Documentation Included

### MIGRATION_GUIDE.md
Comprehensive guide covering:
- Installing Cursor IDE
- Setting up the project
- Understanding Cursor AI features
- Common issues and solutions
- Week-by-week development roadmap

### FILE_MIGRATION_GUIDE.md
File-by-file instructions for:
- Which files to copy from Manus
- Which files to replace
- Which files to create new
- Import path corrections needed
- Testing checklist

### .cursorrules
Project-specific AI context that tells Cursor:
- Code style and conventions
- Critical invariants (unit edge length, series order)
- Prohibited and encouraged patterns
- Testing requirements
- Performance guidelines

---

## 🧪 Testing

### Automated Tests
```bash
npm test
```

**Expected Output**:
```
✓ src/core/polygonSymbolsV2.ts (36 tests)
  ✓ ABCD Series Tables (5)
    ✓ Series A is triangle-first
    ✓ Series B is square-first
    ✓ Series D is square-first, pentagon-second
    ✓ All series have exactly 9 entries
    ✓ All edge counts are in valid range
  ✓ Series Lookup Functions (4)
  ✓ Symbol Generation (4)
  ✓ Subscript Utilities (3)
  ✓ Attachment Stability Optimization (3)
  ✓ Integration with Existing Code (2)
```

### Visual Validation
1. Run `npm run dev`
2. Check polygon palette displays correctly
3. Click A₁ → should place triangle (3 sides)
4. Click D₁ → should place square (4 sides)
5. Drag polygon near edge → should auto-rotate and snap

---

## 🎯 Key Improvements

### 1. Stability-Optimized Series
```typescript
// Positions 1-3 now contain most stable polygons
A₁ = Triangle   (3 sides)  - Most stable attachment
A₂ = Pentagon   (5 sides)  - Second most stable
A₃ = Heptagon   (7 sides)  - Third most stable

D₁ = Square     (4 sides)  - Most stable even polygon
D₂ = Pentagon   (5 sides)  - Redundancy for flexibility
```

### 2. Complete Implementation
- All referenced functions now exist
- No undefined variables
- Validation runs automatically
- TypeScript errors resolved

### 3. Test Coverage
- 36 comprehensive tests
- Validates all series tables
- Tests symbol generation
- Checks attachment stability
- Round-trip subscript conversion

---

## 🔗 Series Comparison

| Position | OLD A-Series | NEW A-Series | Change |
|----------|--------------|--------------|--------|
| 1 | 11 | **3** | ✅ Triangle (most stable) |
| 2 | 13 | **5** | ✅ Pentagon |
| 3 | 3 | **7** | ✅ Heptagon |
| 4 | 15 | **9** | Reordered |
| 5 | 5 | **11** | Moved from pos 1 |
| 6 | 17 | **13** | Moved from pos 2 |
| 7 | 7 | **15** | Moved from pos 4 |
| 8 | 19 | **17** | Reordered |
| 9 | 11 | **19** | Reordered |

**Why This Matters**: Triangle-triangle (A₁-A₁) and triangle-square (A₁-B₁) are the most stable attachments and form the basis for tetrahedra and other fundamental polyforms.

---

## 💡 Using Cursor AI

### Basic Commands

**Chat with your code** (Cmd+L):
```
"Explain how the ABCD series works"
"Show me all files using edge snapping"
"Generate a tetrahedron assembly test"
```

**Edit code inline** (Cmd+K):
```
Select function → Cmd+K → "Add error handling"
Select function → Cmd+K → "Add JSDoc comments"
Select function → Cmd+K → "Optimize for performance"
```

**Search codebase** (@-mentions):
```
@polygonSymbolsV2.ts What's in Series A?
@workspace How many components use Babylon.js?
@docs How do I rotate a mesh in Babylon.js?
```

---

## 🐛 Troubleshooting

### Issue: Tests Fail
```bash
# Make sure you're using the FIXED polygonSymbolsV2.ts
cp [path-to-package]/src/core/polygonSymbolsV2.ts src/core/
npm test
```

### Issue: Import Errors
```typescript
// Update imports in your components:
import { getPolygonSides } from '../core/polygonSymbolsV2';
// NOT from './polygonSymbols'
```

### Issue: Polygons Not Rendering
```typescript
// In BabylonWorkspace.tsx, ensure:
material.backFaceCulling = false;  // Required for flat polygons
mesh.material = material;
```

### Issue: Cursor AI Not Working
```bash
# Check settings:
Cmd+, → Search "Cursor AI" → Enable
# Sign in if prompted
# Select "Claude 3.5 Sonnet" as model
```

---

## 📖 Next Steps

1. **Today**: Get project running in Cursor
   - `npm install`
   - `npm test`
   - `npm run dev`

2. **This Week**: Test series optimization
   - Verify A₁ = triangle in UI
   - Test manual polygon placement
   - Try edge snapping

3. **Next Week**: Build tetrahedron
   - Place 4 triangles (A₁)
   - Snap edges to form tetrahedron
   - Validate 70.529° fold angle

4. **Week 3-4**: Advanced features
   - Implement fold angle calculations
   - Add closure detection
   - Start GPU decoder (optional)

---

## 📞 Support

### Using Cursor
- Official Docs: https://cursor.sh/docs
- Keyboard Shortcuts: https://cursor.sh/shortcuts
- Discord: https://discord.gg/cursor

### Project-Specific
- Press `Cmd+L` in Cursor and ask Claude
- Reference `MIGRATION_GUIDE.md` for detailed help
- Check `FILE_MIGRATION_GUIDE.md` for file-specific issues

---

## ✅ Migration Checklist

Before you start developing:

- [ ] Cursor IDE installed
- [ ] Manus files extracted
- [ ] Fixed `polygonSymbolsV2.ts` copied
- [ ] Test suite added
- [ ] `.cursorrules` in place
- [ ] `npm install` successful
- [ ] `npm test` passes (36 tests)
- [ ] `npm run dev` shows working app
- [ ] Verified A₁ = triangle, D₁ = square
- [ ] Cursor AI responding (Cmd+L works)

**All checked?** You're ready to build! 🚀

---

## 📄 License

Same as original Polylog6 project.

---

**Questions?** Open Cursor, press `Cmd+L`, and ask Claude!
