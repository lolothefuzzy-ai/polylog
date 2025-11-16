/**
 * Full System Integration Tests
 * Tests complete backend-frontend integration workflow
 */

import { expect, test } from '@playwright/test';

test.describe('Full System Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
    await page.waitForSelector('canvas', { timeout: 10000 });
  });

  test('Complete Backend-Frontend Data Flow', async ({ page }) => {
    // Test 1: Backend API is accessible
    const healthCheck = await page.request.get('http://localhost:8000/health');
    expect(healthCheck.status()).toBe(200);
    
    // Test 2: Frontend can load geometry from backend
    const geometryResponse = await page.request.get('http://localhost:8000/api/geometry/primitive/4');
    expect(geometryResponse.status()).toBe(200);
    const geometry = await geometryResponse.json();
    expect(geometry.vertices).toBeDefined();
    expect(geometry.vertices.length).toBeGreaterThan(0);
    
    // Test 3: Frontend can retrieve fold angles
    const foldAngleResponse = await page.request.get('http://localhost:8000/api/geometry/fold-angle/3/4');
    expect(foldAngleResponse.status()).toBe(200);
    const foldAngle = await foldAngleResponse.json();
    expect(typeof foldAngle).toBe('number');
    
    // Test 4: Frontend can load polyhedra
    const polyhedraResponse = await page.request.get('http://localhost:8000/api/tier1/polyhedra/Ω1');
    expect(polyhedraResponse.status()).toBe(200);
    const polyhedra = await polyhedraResponse.json();
    expect(polyhedra.vertices).toBeDefined();
    expect(polyhedra.faces).toBeDefined();
    
    // Test 5: Frontend renders canvas (visualization works)
    const canvas = await page.$('canvas');
    expect(canvas).not.toBeNull();
  });

  test('Backend-Frontend Error Handling', async ({ page }) => {
    // Test that errors are handled gracefully
    const errorTests = [
      { url: 'http://localhost:8000/api/geometry/primitive/999', expectedStatus: 404 },
      { url: 'http://localhost:8000/api/tier1/polyhedra/INVALID', expectedStatus: 404 },
      { url: 'http://localhost:8000/tier0/symbols/INVALID', expectedStatus: 404 }
    ];
    
    for (const testCase of errorTests) {
      const response = await page.request.get(testCase.url);
      expect(response.status()).toBe(testCase.expectedStatus);
      
      // Verify error response is valid
      const errorData = await response.json();
      expect(errorData).toBeDefined();
    }
    
    // Verify frontend still works after errors
    const canvas = await page.$('canvas');
    expect(canvas).not.toBeNull();
  });

  test('Backend API Response Consistency', async ({ page }) => {
    // Test that backend returns consistent data
    const endpoint = 'http://localhost:8000/api/geometry/primitive/4';
    const responses = [];
    
    // Make multiple requests
    for (let i = 0; i < 3; i++) {
      const response = await page.request.get(endpoint);
      const data = await response.json();
      responses.push(data);
    }
    
    // Verify all responses are identical
    const first = JSON.stringify(responses[0]);
    for (let i = 1; i < responses.length; i++) {
      expect(JSON.stringify(responses[i])).toBe(first);
    }
  });

  test('Backend Performance Under Load', async ({ page }) => {
    // Test backend handles multiple concurrent requests
    const requests = Array.from({ length: 10 }, (_, i) => {
      const endpoints = [
        'http://localhost:8000/health',
        'http://localhost:8000/api/geometry/primitive/3',
        'http://localhost:8000/api/geometry/primitive/4',
        'http://localhost:8000/api/geometry/fold-angle/3/4'
      ];
      return page.request.get(endpoints[i % endpoints.length]);
    });
    
    const responses = await Promise.all(requests);
    
    // Verify all succeeded
    const failures = responses.filter(r => r.status() !== 200);
    expect(failures.length).toBe(0);
  });
});

