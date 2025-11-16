/**
 * Backend System Stability Visual Tests
 * Tests backend API stability, response times, and error handling
 */

import { test, expect } from '@playwright/test';

test.describe('Backend System Stability', () => {
  let apiResponseTimes = [];
  let apiErrors = [];

  test.beforeEach(async ({ page }) => {
    apiResponseTimes = [];
    apiErrors = [];
    
    // Monitor API calls
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/api/')) {
        const timing = response.timing();
        const responseTime = timing.responseEnd - timing.requestStart;
        apiResponseTimes.push({
          url,
          status: response.status(),
          responseTime,
          timestamp: Date.now()
        });
        
        if (!response.ok()) {
          apiErrors.push({
            url,
            status: response.status(),
            statusText: response.statusText(),
            timestamp: Date.now()
          });
        }
      }
    });
    
    page.on('pageerror', (error) => {
      apiErrors.push({
        type: 'page_error',
        message: error.message,
        timestamp: Date.now()
      });
    });
    
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
  });

  test('API Health Check Stability', async ({ page }) => {
    const healthChecks = [];
    const iterations = 10;
    
    for (let i = 0; i < iterations; i++) {
      const startTime = Date.now();
      const response = await page.request.get('http://localhost:8000/health');
      const endTime = Date.now();
      
      healthChecks.push({
        iteration: i + 1,
        status: response.status(),
        responseTime: endTime - startTime,
        timestamp: Date.now()
      });
      
      expect(response.status()).toBe(200);
      await page.waitForTimeout(100); // Small delay between checks
    }
    
    // Calculate statistics
    const responseTimes = healthChecks.map(h => h.responseTime);
    const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    const maxResponseTime = Math.max(...responseTimes);
    const minResponseTime = Math.min(...responseTimes);
    
    console.log('[BACKEND STABILITY] Health Check Stats:');
    console.log(`  Average: ${avgResponseTime.toFixed(2)}ms`);
    console.log(`  Min: ${minResponseTime}ms`);
    console.log(`  Max: ${maxResponseTime}ms`);
    
    // Assertions
    expect(avgResponseTime).toBeLessThan(100); // Should be fast
    expect(maxResponseTime).toBeLessThan(500); // No outliers
    expect(apiErrors.length).toBe(0);
  });

  test('Geometry API Stability', async ({ page }) => {
    const geometryTests = [];
    const testCases = [
      { endpoint: '/api/geometry/primitive/3', name: 'Triangle' },
      { endpoint: '/api/geometry/primitive/4', name: 'Square' },
      { endpoint: '/api/geometry/primitive/5', name: 'Pentagon' },
      { endpoint: '/api/geometry/fold-angle/3/4', name: 'Triangle-Square fold' },
      { endpoint: '/api/geometry/fold-angle/4/4', name: 'Square-Square fold' },
    ];
    
    for (const testCase of testCases) {
      const startTime = Date.now();
      const response = await page.request.get(`http://localhost:8000${testCase.endpoint}`);
      const endTime = Date.now();
      
      geometryTests.push({
        endpoint: testCase.endpoint,
        name: testCase.name,
        status: response.status(),
        responseTime: endTime - startTime,
        hasData: (await response.json()) !== null
      });
      
      expect(response.status()).toBe(200);
    }
    
    // Verify all responses are fast
    const slowResponses = geometryTests.filter(t => t.responseTime > 200);
    expect(slowResponses.length).toBe(0);
    
    console.log('[BACKEND STABILITY] Geometry API Stats:');
    geometryTests.forEach(test => {
      console.log(`  ${test.name}: ${test.responseTime}ms`);
    });
  });

  test('Tier 1 Polyhedra API Stability', async ({ page }) => {
    const polyhedraTests = [];
    const symbols = ['Ω1', 'Ω2', 'Ω3', 'Ω4', 'Ω5']; // Platonic solids
    
    for (const symbol of symbols) {
      const startTime = Date.now();
      const response = await page.request.get(`http://localhost:8000/api/tier1/polyhedra/${symbol}`);
      const endTime = Date.now();
      
      const data = await response.json();
      polyhedraTests.push({
        symbol,
        status: response.status(),
        responseTime: endTime - startTime,
        hasVertices: data.vertices && data.vertices.length > 0,
        hasFaces: data.faces && data.faces.length > 0
      });
      
      expect(response.status()).toBe(200);
      expect(data.vertices).toBeDefined();
      expect(data.faces).toBeDefined();
    }
    
    // Verify response times
    const avgResponseTime = polyhedraTests.reduce((sum, t) => sum + t.responseTime, 0) / polyhedraTests.length;
    expect(avgResponseTime).toBeLessThan(300); // Should be fast with Netlib
    
    console.log('[BACKEND STABILITY] Tier 1 API Stats:');
    polyhedraTests.forEach(test => {
      console.log(`  ${test.symbol}: ${test.responseTime}ms`);
    });
  });

  test('Concurrent API Request Stability', async ({ page }) => {
    const concurrentRequests = 20;
    const endpoints = [
      '/api/health',
      '/api/geometry/primitive/3',
      '/api/geometry/primitive/4',
      '/api/geometry/fold-angle/3/4',
      '/api/tier1/polyhedra/Ω1'
    ];
    
    const promises = [];
    for (let i = 0; i < concurrentRequests; i++) {
      const endpoint = endpoints[i % endpoints.length];
      promises.push(
        page.request.get(`http://localhost:8000${endpoint}`).then(async (response) => {
          const data = await response.json().catch(() => null);
          return {
            endpoint,
            status: response.status(),
            hasData: data !== null,
            timestamp: Date.now()
          };
        })
      );
    }
    
    const results = await Promise.all(promises);
    
    // Verify all requests succeeded
    const failures = results.filter(r => r.status !== 200);
    expect(failures.length).toBe(0);
    
    // Verify no errors in error log
    expect(apiErrors.length).toBe(0);
    
    console.log(`[BACKEND STABILITY] Concurrent Requests: ${concurrentRequests} requests, ${failures.length} failures`);
  });

  test('Error Handling Stability', async ({ page }) => {
    const errorTests = [
      { endpoint: '/api/geometry/primitive/999', expectedStatus: 404 },
      { endpoint: '/api/tier1/polyhedra/INVALID', expectedStatus: 404 },
      { endpoint: '/api/geometry/fold-angle/999/999', expectedStatus: 404 },
    ];
    
    for (const testCase of errorTests) {
      const response = await page.request.get(`http://localhost:8000${testCase.endpoint}`);
      expect(response.status()).toBe(testCase.expectedStatus);
      
      // Verify error response is valid JSON
      const errorData = await response.json();
      expect(errorData).toBeDefined();
    }
    
    // Verify no unhandled errors
    expect(apiErrors.filter(e => e.type === 'page_error').length).toBe(0);
  });

  test('API Response Consistency', async ({ page }) => {
    const endpoint = '/api/geometry/primitive/4';
    const responses = [];
    
    // Make same request multiple times
    for (let i = 0; i < 5; i++) {
      const response = await page.request.get(`http://localhost:8000${endpoint}`);
      const data = await response.json();
      responses.push(data);
      await page.waitForTimeout(50);
    }
    
    // Verify all responses are identical
    const firstResponse = JSON.stringify(responses[0]);
    for (let i = 1; i < responses.length; i++) {
      expect(JSON.stringify(responses[i])).toBe(firstResponse);
    }
  });

  test('Backend Memory and Performance', async ({ page }) => {
    // Load multiple polyhedra to test backend performance
    const symbols = ['Ω1', 'Ω2', 'Ω3', 'Ω4', 'Ω5', 'Ω6', 'Ω7', 'Ω8', 'Ω9', 'Ω10'];
    const startTime = Date.now();
    
    const promises = symbols.map(symbol =>
      page.request.get(`http://localhost:8000/api/tier1/polyhedra/${symbol}`)
    );
    
    const responses = await Promise.all(promises);
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    // Verify all succeeded
    responses.forEach(response => {
      expect(response.status()).toBe(200);
    });
    
    // Verify reasonable performance
    const avgTimePerRequest = totalTime / symbols.length;
    expect(avgTimePerRequest).toBeLessThan(500); // Should handle multiple requests efficiently
    
    console.log(`[BACKEND STABILITY] Loaded ${symbols.length} polyhedra in ${totalTime}ms (avg: ${avgTimePerRequest.toFixed(2)}ms)`);
  });
});

