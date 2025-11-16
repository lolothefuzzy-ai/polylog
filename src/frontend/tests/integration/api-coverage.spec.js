/**
 * API Coverage Tests
 * Tests all backend API endpoints to ensure full coverage
 */

import { expect, test } from '@playwright/test';

test.describe('API Coverage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
  });

  test('Health Endpoint', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/health');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('Geometry API - Primitives', async ({ page }) => {
    const testSides = [3, 4, 5, 6, 7, 8];
    
    for (const sides of testSides) {
      const response = await page.request.get(`http://localhost:8000/api/geometry/primitive/${sides}`);
      expect(response.status()).toBe(200);
      const geometry = await response.json();
      expect(geometry.vertices).toBeDefined();
      expect(geometry.vertices.length).toBeGreaterThan(0);
      expect(geometry.faces).toBeDefined();
    }
  });

  test('Geometry API - Fold Angles', async ({ page }) => {
    const testPairs = [
      [3, 4], [4, 4], [3, 5], [5, 6], [4, 6]
    ];
    
    for (const [sidesA, sidesB] of testPairs) {
      const response = await page.request.get(
        `http://localhost:8000/api/geometry/fold-angle/${sidesA}/${sidesB}`
      );
      expect(response.status()).toBe(200);
      const foldAngle = await response.json();
      expect(typeof foldAngle).toBe('number');
      expect(foldAngle).toBeGreaterThan(0);
      expect(foldAngle).toBeLessThan(Math.PI * 2);
    }
  });

  test('Tier 1 API - Polyhedra', async ({ page }) => {
    const symbols = ['Ω1', 'Ω2', 'Ω3', 'Ω4', 'Ω5']; // Platonic solids
    
    for (const symbol of symbols) {
      const response = await page.request.get(
        `http://localhost:8000/api/tier1/polyhedra/${symbol}`
      );
      expect(response.status()).toBe(200);
      const polyhedra = await response.json();
      expect(polyhedra.vertices).toBeDefined();
      expect(polyhedra.faces).toBeDefined();
      expect(polyhedra.symbol).toBe(symbol);
    }
  });

  test('Tier 0 API - Symbol Decoding', async ({ page }) => {
    const testSymbols = ['A11', 'B11', 'A111', 'B111', 'A112'];
    
    for (const symbol of testSymbols) {
      const response = await page.request.get(
        `http://localhost:8000/tier0/symbols/${symbol}`
      );
      expect(response.status()).toBe(200);
      const decoded = await response.json();
      expect(decoded.polygons).toBeDefined();
      expect(Array.isArray(decoded.polygons)).toBe(true);
      expect(decoded.polygons.length).toBeGreaterThan(0);
      expect(decoded.symbol).toBe(symbol);
    }
  });

  test('Tier 0 API - Atomic Chains', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/tier0/atomic-chains/library');
    expect(response.status()).toBe(200);
    const library = await response.json();
    expect(library).toBeDefined();
    // Library may be empty initially, but structure should exist
    expect(typeof library).toBe('object');
  });

  test('Error Handling - Invalid Requests', async ({ page }) => {
    const invalidRequests = [
      { url: '/api/geometry/primitive/999', expectedStatus: 404 },
      { url: '/api/tier1/polyhedra/INVALID', expectedStatus: 404 },
      { url: '/tier0/symbols/INVALID', expectedStatus: 404 },
      { url: '/api/geometry/fold-angle/999/999', expectedStatus: 404 }
    ];
    
    for (const testCase of invalidRequests) {
      const response = await page.request.get(`http://localhost:8000${testCase.url}`);
      expect(response.status()).toBe(testCase.expectedStatus);
      
      // Verify error response is valid JSON
      const errorData = await response.json();
      expect(errorData).toBeDefined();
    }
  });

  test('API Response Times', async ({ page }) => {
    const endpoints = [
      '/health',
      '/api/geometry/primitive/4',
      '/api/geometry/fold-angle/3/4',
      '/api/tier1/polyhedra/Ω1',
      '/tier0/symbols/A11'
    ];
    
    const responseTimes = [];
    
    for (const endpoint of endpoints) {
      const startTime = Date.now();
      const response = await page.request.get(`http://localhost:8000${endpoint}`);
      const endTime = Date.now();
      
      expect(response.status()).toBe(200);
      responseTimes.push({
        endpoint,
        time: endTime - startTime
      });
    }
    
    // Verify all responses are reasonably fast (< 500ms)
    const slowResponses = responseTimes.filter(r => r.time > 500);
    expect(slowResponses.length).toBe(0);
    
    console.log('[API COVERAGE] Response times:', responseTimes);
  });
});

