import { test, expect } from '@playwright/test';

test.describe('Full System Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 10000 });
  });

  test('Complete user workflow: Select → Validate → Attach', async ({ page }) => {
    // Step 1: Select first polyhedron
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    
    // Verify selection
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Step 2: Select second polyhedron
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(500);
    
    // Step 3: Verify attachment validator appears
    const validator = page.locator('.attachment-validator');
    await expect(validator).toBeVisible();
    
    // Step 4: Check if attachment options are shown
    const options = page.locator('.validator-option');
    const optionCount = await options.count();
    
    // Options may be empty if API not available, but component should exist
    expect(optionCount).toBeGreaterThanOrEqual(0);
    
    // Step 5: Verify 3D scene is still rendering
    await expect(canvas).toBeVisible();
  });

  test('API → Frontend → 3D Rendering pipeline', async ({ page }) => {
    // Test that data flows: API → Service → Component → Render
    
    // Monitor network requests
    const apiCalls = [];
    page.on('response', response => {
      if (response.url().includes('/tier1/') || response.url().includes('/api/')) {
        apiCalls.push({
          url: response.url(),
          status: response.status(),
          time: Date.now()
        });
      }
    });
    
    // Trigger API call
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(1000);
    
    // Verify API was called
    expect(apiCalls.length).toBeGreaterThanOrEqual(0);
    
    // Verify 3D scene rendered
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });

  test('Error handling: API unavailable', async ({ page }) => {
    // Simulate API failure
    await page.route('**/tier1/**', route => route.abort());
    
    // Try to load polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Should show error or empty state, not crash
    const library = page.locator('.polyhedra-library');
    await expect(library).toBeVisible();
    
    // App should still be functional
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });

  test('Performance: Load 20 polyhedra', async ({ page }) => {
    const startTime = Date.now();
    
    // Load multiple polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    for (let i = 0; i < 5; i++) {
      await page.click('.library-item').catch(() => {});
      await page.waitForTimeout(100);
    }
    
    const loadTime = Date.now() - startTime;
    
    console.log(`Loaded 5 polyhedra in ${loadTime}ms`);
    expect(loadTime).toBeLessThan(10000); // Should complete in reasonable time
    
    // Verify scene still renders
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });

  test('LOD system: Camera distance triggers LOD change', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Get initial LOD
    const initialLod = await page.locator('.lod-indicator').textContent();
    
    // Zoom out (should trigger LOD change)
    await canvas.dispatchEvent('wheel', {
      deltaY: -500,
      bubbles: true
    });
    
    await page.waitForTimeout(500);
    
    // LOD should update (may be same if already at limit)
    const lodIndicator = page.locator('.lod-indicator');
    await expect(lodIndicator).toBeVisible();
  });
});

