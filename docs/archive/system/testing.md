# Testing System Documentation

## Automated Test Suite

The project uses an automated test suite focused on backend-frontend integration.

### Test Runner

`scripts/automated_test_suite.py` - Main test runner with:
- Process lifecycle management
- Server startup/cleanup
- Multiple test suite support
- Signal handling for graceful shutdown

### Test Suites

1. **Backend Stability** (`backend-stability.spec.js`)
   - API health checks
   - Response time monitoring
   - Error handling
   - Concurrent request stability

2. **Backend Integration** (`backend-integration-stability.spec.js`)
   - Data consistency
   - Tier 0 encoding/decoding
   - Workspace-backend integration
   - Error recovery

3. **Frontend Integration** (`backend-frontend-integration.spec.js`)
   - Frontend loads geometry from backend
   - Frontend uses backend fold angles
   - Frontend loads polyhedra from backend
   - Frontend Tier 0 integration
   - Error handling

4. **Full System Integration** (`full-system-integration.spec.js`)
   - Complete backend-frontend data flow
   - Error handling
   - Response consistency
   - Performance under load

## Running Tests

```bash
# Run all tests
python scripts/automated_test_suite.py --type all

# Run specific test suite
python scripts/automated_test_suite.py --type backend-stability
python scripts/automated_test_suite.py --type frontend-integration

# Or use npm scripts
npm test
npm run test:backend
npm run test:integration
```

## API Endpoints

### Correct Endpoints
- Health: `/health` (not `/api/health`)
- Tier 0: `/tier0/symbols/{symbol}` (not `/api/tier0/decode/`)
- Geometry: `/api/geometry/primitive/{sides}`
- Fold Angle: `/api/geometry/fold-angle/{sidesA}/{sidesB}`
- Polyhedra: `/api/tier1/polyhedra/{symbol}`

## Process Management

The test suite uses global process references with cleanup handlers:
- `atexit` handlers for cleanup
- Signal handlers for graceful shutdown
- Proper subprocess management

See `scripts/automated_test_suite.py` for implementation details.

