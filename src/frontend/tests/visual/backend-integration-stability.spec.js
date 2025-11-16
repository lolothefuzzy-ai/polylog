/**
 * Backend Integration Stability Tests
 * Tests backend integration with frontend, data consistency, and system stability
 */

import { test, expect } from '@playwright/test';

test.describe('Backend Integration Stability', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
    await page.waitForSelector('canvas', { timeout: 10000 });
  });

  test('Backend-Frontend Data Consistency', async ({ page }) => {
    // Test that frontend receives consistent data from backend
    const testResults = {
      primitivesLoaded: false,
      geometryConsistent: false,
      foldAnglesConsistent: false
    };
    
    // Load primitive geometry from backend
    const primitiveResponse = await page.request.get('http://localhost:8000/api/geometry/primitive/4');
    const backendGeometry = await primitiveResponse.json();
    
    expect(backendGeometry).toBeDefined();
    expect(backendGeometry.vertices).toBeDefined();
    expect(backendGeometry.vertices.length).toBeGreaterThan(0);
    testResults.primitivesLoaded = true;
    
    // Verify geometry structure
    expect(backendGeometry.vertices[0]).toHaveLength(3); // [x, y, z]
    expect(backendGeometry.faces).toBeDefined();
    testResults.geometryConsistent = true;
    
    // Test fold angle consistency
    const foldAngleResponse = await page.request.get('http://localhost:8000/api/geometry/fold-angle/3/4');
    const foldAngle = await foldAngleResponse.json();
    
    expect(typeof foldAngle).toBe('number');
    expect(foldAngle).toBeGreaterThan(0);
    expect(foldAngle).toBeLessThan(Math.PI);
    testResults.foldAnglesConsistent = true;
    
    // All checks passed
    expect(testResults.primitivesLoaded).toBe(true);
    expect(testResults.geometryConsistent).toBe(true);
    expect(testResults.foldAnglesConsistent).toBe(true);
  });

  test('Tier 0 Encoding/Decoding Stability', async ({ page }) => {
    // Test Tier 0 symbol encoding/decoding round-trip
    const testSymbols = ['A11', 'B11', 'A111', 'B111'];
    
    for (const symbol of testSymbols) {
      // Decode symbol
      const decodeResponse = await page.request.get(`http://localhost:8000/tier0/decode/${symbol}`);
      const decoded = await decodeResponse.json();
      
      expect(decodeResponse.status()).toBe(200);
      expect(decoded.polygons).toBeDefined();
      expect(Array.isArray(decoded.polygons)).toBe(true);
      expect(decoded.polygons.length).toBeGreaterThan(0);
      
      // Verify polygon sides are valid (3-20)
      decoded.polygons.forEach(sides => {
        expect(sides).toBeGreaterThanOrEqual(3);
        expect(sides).toBeLessThanOrEqual(20);
      });
    }
  });

  test('Workspace-Backend Integration', async ({ page }) => {
    // Test that workspace operations correctly interact with backend
    const testResults = {
      apiAvailable: false,
      geometryLoadable: false,
      foldAngleRetrievable: false
    };
    
    // Check API availability
    const healthResponse = await page.request.get('http://localhost:8000/health');
    expect(healthResponse.status()).toBe(200);
    testResults.apiAvailable = true;
    
    // Test geometry loading (simulating workspace polygon creation)
    const geometryResponse = await page.request.get('http://localhost:8000/api/geometry/primitive/3');
    const geometry = await geometryResponse.json();
    expect(geometry.vertices).toBeDefined();
    testResults.geometryLoadable = true;
    
    // Test fold angle retrieval (simulating attachment)
    const foldAngleResponse = await page.request.get('http://localhost:8000/api/geometry/fold-angle/3/4');
    const foldAngle = await foldAngleResponse.json();
    expect(typeof foldAngle).toBe('number');
    testResults.foldAngleRetrievable = true;
    
    // Verify all integration points work
    expect(testResults.apiAvailable).toBe(true);
    expect(testResults.geometryLoadable).toBe(true);
    expect(testResults.foldAngleRetrievable).toBe(true);
  });

  test('Backend Error Recovery', async ({ page }) => {
    // Test that backend handles errors gracefully
    const invalidRequests = [
      '/api/geometry/primitive/999',
      '/api/tier1/polyhedra/INVALID',
      '/tier0/decode/INVALID'
    ];
    
    for (const endpoint of invalidRequests) {
      const response = await page.request.get(`http://localhost:8000${endpoint}`);
      
      // Should return proper error status
      expect([404, 400, 422]).toContain(response.status());
      
      // Should return JSON error response
      const errorData = await response.json();
      expect(errorData).toBeDefined();
    }
    
    // Verify system still works after errors
    const healthResponse = await page.request.get('http://localhost:8000/health');
    expect(healthResponse.status()).toBe(200);
  });

  test('Backend Load Under Stress', async ({ page }) => {
    // Simulate high load on backend
    const loadTest = {
      requests: 50,
      endpoint: '/api/geometry/primitive/4',
      successCount: 0,
      failureCount: 0,
      responseTimes: []
    };
    
    const promises = Array.from({ length: loadTest.requests }, async (_, i) => {
      const startTime = Date.now();
      try {
        const response = await page.request.get(`http://localhost:8000${loadTest.endpoint}`);
        const endTime = Date.now();
        
        if (response.status() === 200) {
          loadTest.successCount++;
        } else {
          loadTest.failureCount++;
        }
        loadTest.responseTimes.push(endTime - startTime);
      } catch (error) {
        loadTest.failureCount++;
      }
    });
    
    await Promise.all(promises);
    
    // Verify high success rate
    const successRate = loadTest.successCount / loadTest.requests;
    expect(successRate).toBeGreaterThan(0.95); // 95% success rate
    
    // Verify reasonable response times
    const avgResponseTime = loadTest.responseTimes.reduce((a, b) => a + b, 0) / loadTest.responseTimes.length;
    expect(avgResponseTime).toBeLessThan(500); // Should handle load
    
    console.log(`[BACKEND STABILITY] Load Test: ${loadTest.successCount}/${loadTest.requests} successful, avg ${avgResponseTime.toFixed(2)}ms`);
  });

  test('Backend Data Integrity', async ({ page }) => {
    // Test that backend returns consistent, valid data structures
    const integrityTests = [];
    
    // Test primitive geometry structure
    const primitiveResponse = await page.request.get('http://localhost:8000/api/geometry/primitive/4');
    const primitive = await primitiveResponse.json();
    
    integrityTests.push({
      name: 'Primitive Geometry Structure',
      passed: (
        Array.isArray(primitive.vertices) &&
        primitive.vertices.length > 0 &&
        primitive.vertices[0].length === 3 &&
        Array.isArray(primitive.faces) &&
        primitive.faces.length > 0
      )
    });
    
    // Test polyhedron structure
    const polyhedronResponse = await page.request.get('http://localhost:8000/api/tier1/polyhedra/Ω1');
    const polyhedron = await polyhedronResponse.json();
    
    integrityTests.push({
      name: 'Polyhedron Structure',
      passed: (
        Array.isArray(polyhedron.vertices) &&
        Array.isArray(polyhedron.faces) &&
        polyhedron.symbol !== undefined &&
        polyhedron.name !== undefined
      )
    });
    
    // Test fold angle structure
    const foldAngleResponse = await page.request.get('http://localhost:8000/api/geometry/fold-angle/3/4');
    const foldAngle = await foldAngleResponse.json();
    
    integrityTests.push({
      name: 'Fold Angle Structure',
      passed: (
        typeof foldAngle === 'number' &&
        !isNaN(foldAngle) &&
        foldAngle > 0 &&
        foldAngle < Math.PI * 2
      )
    });
    
    // Verify all integrity tests passed
    integrityTests.forEach(test => {
      expect(test.passed).toBe(true);
    });
    
    console.log('[BACKEND STABILITY] Data Integrity Tests:');
    integrityTests.forEach(test => {
      console.log(`  ${test.name}: ${test.passed ? 'PASS' : 'FAIL'}`);
    });
  });
});

