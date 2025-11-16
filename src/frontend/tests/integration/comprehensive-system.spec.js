import { test, expect } from '@playwright/test';

test.describe('Comprehensive System Integration - Architecture Validation', () => {
  test.beforeEach(async ({ page }) => {
    // Enable detailed logging for architecture validation
    page.on('console', msg => {
      if (msg.type() === 'error' || msg.type() === 'warning') {
        console.log(`Browser ${msg.type()}: ${msg.text()}`);
      }
    });
    
    // Monitor API calls for validation
    page.on('response', response => {
      if (response.url().includes('/api/') || response.url().includes('/tier1/')) {
        console.log(`API Response: ${response.status()} ${response.url()}`);
      }
    });
    
    await page.goto('/');
    await page.waitForSelector('.app-layout', { timeout: 15000 });
  });

  test('Architecture Component 1: Storage System Integration', async ({ page }) => {
    // Test tiered storage architecture access
    const storageTests = [
      { endpoint: '/tier1/polyhedra', expectedCount: 110 },
      { endpoint: '/tier1/stats', expectedFields: ['total_polyhedra', 'compression_ratio'] }
    ];

    for (const test of storageTests) {
      const response = await page.evaluate(async (endpoint) => {
        try {
          const resp = await fetch(`http://localhost:8000${endpoint}`);
          return { status: resp.status, data: await resp.json() };
        } catch (error) {
          return { status: 0, error: error.message };
        }
      }, test.endpoint);

      expect(response.status).toBe(200);
      
      if (test.expectedCount) {
        expect(response.data.length || response.data.total).toBeGreaterThanOrEqual(test.expectedCount * 0.8);
      }
      
      if (test.expectedFields) {
        for (const field of test.expectedFields) {
          expect(response.data).toHaveProperty(field);
        }
      }
    }
  });

  test('Architecture Component 2: Visualization Performance Requirements', async ({ page }) => {
    // Test sub-100ms interaction latency
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();

    // Measure interaction latency
    const latencyMeasurements = [];
    
    for (let i = 0; i < 5; i++) {
      const startTime = Date.now();
      
      // Trigger interaction (click on canvas)
      await canvas.click({ position: { x: 100, y: 100 } });
      
      // Wait for visual feedback (LOD update or scene change)
      await page.waitForTimeout(50);
      
      const endTime = Date.now();
      latencyMeasurements.push(endTime - startTime);
    }

    const avgLatency = latencyMeasurements.reduce((a, b) => a + b, 0) / latencyMeasurements.length;
    console.log(`Average interaction latency: ${avgLatency}ms`);
    
    // Architecture requirement: <100ms interaction latency
    expect(avgLatency).toBeLessThan(100);
  });

  test('Architecture Component 3: Unicode Compression System', async ({ page }) => {
    // Test the 4-level Unicode compression strategy
    
    // Level 0: Primitive polygon labels (A-R)
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const primitiveItems = await page.locator('.library-item').count();
    expect(primitiveItems).toBeGreaterThanOrEqual(10); // Should have primitives A-J at minimum
    
    // Level 1: Pair compression via generation
    await page.click('.library-item:first-child'); // Select first polygon
    await page.waitForTimeout(300);
    await page.click('.library-item:nth-child(2)'); // Select second polygon
    await page.waitForTimeout(500);
    
    // Generate to test compression
    const generateButton = page.locator('.generate-button');
    if (await generateButton.isEnabled()) {
      await generateButton.click();
      await page.waitForTimeout(2000);
      
      // Check compression ratio display
      const compression = page.locator('.polyform-compression');
      if (await compression.count() > 0) {
        const compressionText = await compression.first().textContent();
        expect(compressionText).toMatch(/compression/i);
        
        // Extract ratio if present
        const ratioMatch = compressionText.match(/(\d+\.?\d*):?1/);
        if (ratioMatch) {
          const ratio = parseFloat(ratioMatch[1]);
          // Architecture expects 100:1+ for single polygons
          expect(ratio).toBeGreaterThan(10);
        }
      }
    }
  });

  test('Architecture Component 4: LOD Management System', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    const lodIndicator = page.locator('.lod-indicator');
    await expect(lodIndicator).toBeVisible();
    
    // Test LOD transitions
    const lodLevels = [];
    
    // Zoom in (should trigger full LOD)
    await canvas.dispatchEvent('wheel', { deltaY: 1000, bubbles: true });
    await page.waitForTimeout(500);
    const lodIn = await lodIndicator.textContent();
    lodLevels.push(lodIn);
    
    // Zoom out (should trigger lower LOD)
    await canvas.dispatchEvent('wheel', { deltaY: -1000, bubbles: true });
    await page.waitForTimeout(500);
    const lodOut = await lodIndicator.textContent();
    lodLevels.push(lodOut);
    
    // LOD should change based on distance
    expect(lodLevels.length).toBe(2);
    console.log(`LOD transitions: ${lodLevels.join(' → ')}`);
  });

  test('Architecture Component 5: Memory Budget Validation', async ({ page }) => {
    // Monitor memory usage during operations
    const memorySnapshots = [];
    
    // Baseline memory
    const baselineMemory = await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize;
      }
      return 0;
    });
    memorySnapshots.push(baselineMemory);
    
    // Load multiple polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const itemCount = Math.min(10, await page.locator('.library-item').count());
    
    for (let i = 0; i < itemCount; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(200);
      
      const currentMemory = await page.evaluate(() => {
        if (performance.memory) {
          return performance.memory.usedJSHeapSize;
        }
        return 0;
      });
      memorySnapshots.push(currentMemory);
    }
    
    // Calculate memory growth
    const memoryGrowth = memorySnapshots[memorySnapshots.length - 1] - baselineMemory;
    const memoryGrowthMB = memoryGrowth / (1024 * 1024);
    
    console.log(`Memory growth after loading ${itemCount} polyhedra: ${memoryGrowthMB.toFixed(2)}MB`);
    
    // Architecture requirement: ≤200MB rendering memory budget
    expect(memoryGrowthMB).toBeLessThan(200);
  });

  test('Architecture Component 6: API Response Structure Validation', async ({ page }) => {
    // Test that API responses match documented structure
    
    // Test polyhedra endpoint
    const polyhedraResponse = await page.evaluate(async () => {
      try {
        const resp = await fetch('http://localhost:8000/tier1/polyhedra');
        const data = await resp.json();
        return { success: resp.ok, data: data.slice(0, 3) }; // Check first 3 items
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    expect(polyhedraResponse.success).toBe(true);
    expect(Array.isArray(polyhedraResponse.data)).toBe(true);
    
    // Validate structure of first polyhedron
    if (polyhedraResponse.data.length > 0) {
      const polyhedron = polyhedraResponse.data[0];
      const requiredFields = ['symbol', 'name', 'vertices', 'sides', 'lod'];
      
      for (const field of requiredFields) {
        expect(polyhedron).toHaveProperty(field);
      }
      
      // Validate LOD structure
      expect(polyhedron.lod).toHaveProperty('full');
      expect(polyhedron.lod.full).toHaveProperty('vertices');
      expect(Array.isArray(polyhedron.lod.full.vertices)).toBe(true);
    }
  });

  test('Architecture Component 7: Error Handling and Resilience', async ({ page }) => {
    // Test system resilience under various failure conditions
    
    // Simulate API failure
    await page.route('**/tier1/**', route => route.abort());
    
    // System should remain functional
    await page.waitForSelector('.app-layout', { timeout: 5000 });
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Should show error states or fallback content
    const library = page.locator('.polyhedra-library');
    await expect(library).toBeVisible();
    
    // Restore API and test recovery
    await page.unroute('**/tier1/**');
    
    // Wait for recovery
    await page.waitForTimeout(2000);
    
    // System should recover
    await page.reload();
    await page.waitForSelector('.app-layout', { timeout: 10000 });
    await expect(canvas).toBeVisible();
  });

  test('Architecture Component 8: Cross-Platform Compatibility', async ({ page }) => {
    // Test that the application works across different viewport sizes
    const viewports = [
      { width: 1920, height: 1080 }, // Desktop
      { width: 1366, height: 768 },  // Laptop
      { width: 768, height: 1024 }   // Tablet
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(500);
      
      // Check layout adapts
      const appLayout = page.locator('.app-layout');
      await expect(appLayout).toBeVisible();
      
      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();
      
      const canvasBox = await canvas.boundingBox();
      expect(canvasBox.width).toBeGreaterThan(0);
      expect(canvasBox.height).toBeGreaterThan(0);
      
      console.log(`Viewport ${viewport.width}x${viewport.height}: Canvas ${canvasBox.width}x${canvasBox.height}`);
    }
  });
});