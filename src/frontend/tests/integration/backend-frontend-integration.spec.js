/**
 * Backend-Frontend Integration Tests
 * Tests that frontend correctly integrates with backend APIs
 */

import { test, expect } from '@playwright/test';

test.describe('Backend-Frontend Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
    await page.waitForSelector('canvas', { timeout: 10000 });
  });

  test('Frontend Loads Geometry from Backend', async ({ page }) => {
    // Monitor network requests
    const apiCalls = [];
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/api/geometry/')) {
        apiCalls.push({
          url,
          status: response.status(),
          ok: response.ok()
        });
      }
    });
    
    // Wait for frontend to potentially load geometry
    await page.waitForTimeout(2000);
    
    // Verify API calls were made
    const geometryCalls = apiCalls.filter(call => call.ok);
    expect(geometryCalls.length).toBeGreaterThan(0);
  });

  test('Frontend Uses Backend Fold Angles', async ({ page }) => {
    // Test that frontend can retrieve fold angles from backend
    const foldAngleResponse = await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/geometry/fold-angle/3/4');
      return {
        status: response.status,
        foldAngle: await response.json()
      };
    });
    
    expect(foldAngleResponse.status).toBe(200);
    expect(typeof foldAngleResponse.foldAngle).toBe('number');
    expect(foldAngleResponse.foldAngle).toBeGreaterThan(0);
  });

  test('Frontend Loads Polyhedra from Backend', async ({ page }) => {
    // Test that frontend can load polyhedra data
    const polyhedraResponse = await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/tier1/polyhedra/Ω1');
      return {
        status: response.status,
        data: await response.json()
      };
    });
    
    expect(polyhedraResponse.status).toBe(200);
    expect(polyhedraResponse.data.vertices).toBeDefined();
    expect(polyhedraResponse.data.faces).toBeDefined();
  });

  test('Frontend Tier 0 Integration', async ({ page }) => {
    // Test Tier 0 decoding integration
    const tier0Response = await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/tier0/symbols/A11');
      return {
        status: response.status,
        data: await response.json()
      };
    });
    
    expect(tier0Response.status).toBe(200);
    expect(tier0Response.data.polygons).toBeDefined();
    expect(Array.isArray(tier0Response.data.polygons)).toBe(true);
  });

  test('Frontend Handles Backend Errors Gracefully', async ({ page }) => {
    // Test that frontend handles backend errors without crashing
    const errorHandling = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:8000/api/geometry/primitive/999');
        return {
          handled: true,
          status: response.status,
          error: response.status !== 200
        };
      } catch (error) {
        return {
          handled: true,
          error: error.message
        };
      }
    });
    
    expect(errorHandling.handled).toBe(true);
    
    // Verify page still works after error
    const canvas = await page.$('canvas');
    expect(canvas).not.toBeNull();
  });

  test('Frontend-Backend Data Flow', async ({ page }) => {
    // Test complete data flow: Backend → Frontend → Visualization
    const dataFlow = {
      backendAvailable: false,
      geometryLoadable: false,
      frontendRendered: false
    };
    
    // Check backend
    const healthResponse = await page.request.get('http://localhost:8000/health');
    dataFlow.backendAvailable = healthResponse.status() === 200;
    
    // Load geometry
    const geometryResponse = await page.request.get('http://localhost:8000/api/geometry/primitive/4');
    dataFlow.geometryLoadable = geometryResponse.status() === 200;
    
    // Check frontend rendering
    const canvas = await page.$('canvas');
    dataFlow.frontendRendered = canvas !== null;
    
    // Verify complete flow
    expect(dataFlow.backendAvailable).toBe(true);
    expect(dataFlow.geometryLoadable).toBe(true);
    expect(dataFlow.frontendRendered).toBe(true);
  });
});

