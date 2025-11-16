import { test, expect } from '@playwright/test';

test.describe('End-to-End User Journey Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Enable comprehensive logging for user journey validation
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`Browser error: ${msg.text()}`);
      }
    });
    
    // Monitor all API calls during user journey
    const apiCalls = [];
    page.on('request', request => {
      if (request.url().includes('/api/') || request.url().includes('/tier1/')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          timestamp: Date.now()
        });
      }
    });
    
    // Store API calls for validation
    page.on('load', () => {
      page.evaluate(() => {
        window.apiCalls = [];
      });
    });
    
    await page.goto('/');
    await page.waitForSelector('.app-layout', { timeout: 15000 });
  });

  test('Journey 1: First-time User - Explore and Generate', async ({ page }) => {
    // Complete journey for a first-time user exploring the system
    
    // Step 1: Application loads successfully
    const appLayout = page.locator('.app-layout');
    await expect(appLayout).toBeVisible();
    
    // Verify all main components are present
    await expect(page.locator('.app-sidebar-left')).toBeVisible();
    await expect(page.locator('canvas')).toBeVisible();
    await expect(page.locator('.app-sidebar-right')).toBeVisible();
    
    // Step 2: User explores the polyhedra library
    const library = page.locator('.polyhedra-library');
    await expect(library).toBeVisible();
    
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const libraryItems = page.locator('.library-item');
    const itemCount = await libraryItems.count();
    
    expect(itemCount).toBeGreaterThan(5);
    console.log(`Library contains ${itemCount} polyhedra`);
    
    // Step 3: User selects first polyhedron to explore
    await libraryItems.first().click();
    await page.waitForTimeout(500);
    
    // Verify 3D visualization updates
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Check if polyhedron details appear
    const details = page.locator('.polyhedron-details, .polyhedron-info');
    if (await details.count() > 0) {
      await expect(details.first()).toBeVisible();
    }
    
    // Step 4: User selects second polyhedron
    await libraryItems.nth(1).click();
    await page.waitForTimeout(500);
    
    // Step 5: Attachment validator appears
    const validator = page.locator('.attachment-validator');
    await expect(validator).toBeVisible({ timeout: 5000 });
    
    // Step 6: User generates their first polyform
    const generateButton = page.locator('.generate-button');
    await expect(generateButton).toBeEnabled();
    await generateButton.click();
    
    // Step 7: Wait for generation completion
    await page.waitForTimeout(2000);
    
    // Step 8: Generated polyform appears in results
    const generatedList = page.locator('.generated-polyforms');
    await expect(generatedList).toBeVisible({ timeout: 5000 });
    
    const generatedItem = page.locator('.generated-polyform-item');
    await expect(generatedItem.first()).toBeVisible();
    
    // Step 9: User views compression information
    const compressionInfo = page.locator('.polyform-compression, .compression-ratio');
    if (await compressionInfo.count() > 0) {
      await expect(compressionInfo.first()).toBeVisible();
      const compressionText = await compressionInfo.first().textContent();
      expect(compressionText).toMatch(/compression/i);
    }
    
    // Step 10: User interacts with 3D scene
    await canvas.click({ position: { x: 200, y: 200 } });
    await page.waitForTimeout(300);
    
    // Verify scene is still responsive
    await expect(canvas).toBeVisible();
    
    console.log('First-time user journey completed successfully');
  });

  test('Journey 2: Power User - Complex Assembly Generation', async ({ page }) => {
    // Journey for an experienced user creating complex assemblies
    
    // Step 1: User quickly navigates to library
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const libraryItems = page.locator('.library-item');
    
    // Step 2: User selects multiple polyhedra for complex assembly
    const selections = [1, 2, 3, 4, 5];
    for (const index of selections) {
      await libraryItems.nth(index - 1).click();
      await page.waitForTimeout(200);
    }
    
    // Step 3: User generates multiple variations
    const generateButton = page.locator('.generate-button');
    let generationCount = 0;
    
    for (let i = 0; i < 3; i++) {
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        generationCount++;
        await page.waitForTimeout(1500);
        
        // Check generation results
        const generatedItems = page.locator('.generated-polyform-item');
        const currentCount = await generatedItems.count();
        expect(currentCount).toBeGreaterThan(0);
      }
    }
    
    console.log(`Generated ${generationCount} polyform variations`);
    
    // Step 4: User explores generated polyforms
    const generatedItems = page.locator('.generated-polyform-item');
    const itemCount = await generatedItems.count();
    
    for (let i = 0; i < Math.min(itemCount, 3); i++) {
      await generatedItems.nth(i).click();
      await page.waitForTimeout(300);
      
      // Verify 3D scene updates
      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();
    }
    
    // Step 5: User checks performance metrics
    const lodIndicator = page.locator('.lod-indicator');
    await expect(lodIndicator).toBeVisible();
    
    const lodText = await lodIndicator.textContent();
    expect(lodText).toMatch(/LOD:/i);
    
    // Step 6: User tests different camera views
    const canvas = page.locator('canvas');
    
    // Zoom in
    await canvas.dispatchEvent('wheel', { deltaY: 1000, bubbles: true });
    await page.waitForTimeout(500);
    
    // Zoom out
    await canvas.dispatchEvent('wheel', { deltaY: -1000, bubbles: true });
    await page.waitForTimeout(500);
    
    // Verify LOD updates
    const lodAfterZoom = await lodIndicator.textContent();
    expect(lodAfterZoom).toMatch(/LOD:/i);
    
    console.log('Power user journey completed successfully');
  });

  test('Journey 3: Research User - Data Analysis and Export', async ({ page }) => {
    // Journey for a researcher analyzing polyform properties
    
    // Step 1: User loads the application and checks system stats
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Look for system statistics
    const statsSection = page.locator('.system-stats, .stats-panel');
    if (await statsSection.count() > 0) {
      await expect(statsSection.first()).toBeVisible();
    }
    
    // Step 2: User generates specific polyform combinations for analysis
    const libraryItems = page.locator('.library-item');
    
    // Generate specific combinations for research
    const researchCombinations = [
      [1, 2], // Simple pair
      [1, 2, 3], // Triple
      [4, 5, 6] // Different set
    ];
    
    for (const combination of researchCombinations) {
      // Clear previous selections by clicking outside
      await page.locator('canvas').click();
      await page.waitForTimeout(200);
      
      // Select new combination
      for (const index of combination) {
        await libraryItems.nth(index - 1).click();
        await page.waitForTimeout(200);
      }
      
      // Generate
      const generateButton = page.locator('.generate-button');
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(1500);
        
        // Record generation data
        const generatedItems = page.locator('.generated-polyform-item');
        const count = await generatedItems.count();
        console.log(`Research combination ${combination.join('+')}: Generated ${count} polyforms`);
      }
    }
    
    // Step 3: User analyzes compression ratios
    const compressionInfos = page.locator('.polyform-compression, .compression-ratio');
    const compressionCount = await compressionInfos.count();
    
    if (compressionCount > 0) {
      const ratios = [];
      
      for (let i = 0; i < compressionCount; i++) {
        const text = await compressionInfos.nth(i).textContent();
        const ratioMatch = text.match(/(\d+\.?\d*):?1/);
        if (ratioMatch) {
          ratios.push(parseFloat(ratioMatch[1]));
        }
      }
      
      if (ratios.length > 0) {
        const avgRatio = ratios.reduce((a, b) => a + b, 0) / ratios.length;
        console.log(`Average compression ratio: ${avgRatio.toFixed(2)}:1`);
        expect(avgRatio).toBeGreaterThan(1);
      }
    }
    
    // Step 4: User checks geometric properties
    const generatedItems = page.locator('.generated-polyform-item');
    const itemCount = await generatedItems.count();
    
    if (itemCount > 0) {
      for (let i = 0; i < Math.min(itemCount, 3); i++) {
        await generatedItems.nth(i).click();
        await page.waitForTimeout(300);
        
        // Look for geometric information
        const geometryInfo = page.locator('.geometry-info, .polyform-geometry');
        if (await geometryInfo.count() > 0) {
          const infoText = await geometryInfo.first().textContent();
          expect(infoText).toMatch(/vertices|faces|edges/i);
        }
      }
    }
    
    console.log('Research user journey completed successfully');
  });

  test('Journey 4: Performance Testing User - Stress Testing', async ({ page }) => {
    // Journey for testing system performance under load
    
    // Step 1: User rapidly generates many polyforms
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const libraryItems = page.locator('.library-item');
    
    const startTime = Date.now();
    let successfulGenerations = 0;
    
    // Rapid generation cycle
    for (let cycle = 0; cycle < 10; cycle++) {
      // Select random polyhedra
      const firstIndex = (cycle % 5) + 1;
      const secondIndex = ((cycle + 1) % 5) + 1;
      
      await libraryItems.nth(firstIndex - 1).click();
      await page.waitForTimeout(100);
      await libraryItems.nth(secondIndex - 1).click();
      await page.waitForTimeout(200);
      
      // Generate
      const generateButton = page.locator('.generate-button');
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        successfulGenerations++;
        await page.waitForTimeout(800); // Reduced timeout for stress testing
      }
    }
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    const avgTimePerGeneration = totalTime / successfulGenerations;
    
    console.log(`Stress test: ${successfulGenerations} generations in ${totalTime}ms`);
    console.log(`Average time per generation: ${avgTimePerGeneration.toFixed(2)}ms`);
    
    // Performance should remain reasonable
    expect(avgTimePerGeneration).toBeLessThan(2000); // 2 seconds max per generation
    expect(successfulGenerations).toBeGreaterThan(5); // At least half should succeed
    
    // Step 2: Verify system remains responsive
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Test interaction responsiveness
    const interactionStart = Date.now();
    await canvas.click({ position: { x: 150, y: 150 } });
    await page.waitForTimeout(100);
    const interactionEnd = Date.now();
    
    const interactionLatency = interactionEnd - interactionStart;
    console.log(`Interaction latency during stress: ${interactionLatency}ms`);
    expect(interactionLatency).toBeLessThan(500); // Should remain responsive
    
    // Step 3: Check memory usage (if available)
    const memoryInfo = await page.evaluate(() => {
      if (performance.memory) {
        return {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize,
          limit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    });
    
    if (memoryInfo) {
      const memoryMB = memoryInfo.used / 1024 / 1024;
      console.log(`Memory usage after stress test: ${memoryMB.toFixed(2)}MB`);
      expect(memoryMB).toBeLessThan(300); // Should stay within reasonable bounds
    }
    
    console.log('Performance testing journey completed successfully');
  });

  test('Journey 5: Error Recovery User - System Resilience', async ({ page }) => {
    // Journey testing system behavior under error conditions
    
    // Step 1: Simulate API failure during loading
    await page.route('**/tier1/**', route => route.abort());
    
    // Application should still load with fallback behavior
    await page.goto('/');
    await page.waitForSelector('.app-layout', { timeout: 15000 });
    
    const appLayout = page.locator('.app-layout');
    await expect(appLayout).toBeVisible();
    
    // Canvas should still be available
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Step 2: Restore API and test recovery
    await page.unroute('**/tier1/**');
    
    // Reload to test recovery
    await page.reload();
    await page.waitForSelector('.app-layout', { timeout: 15000 });
    
    // System should recover and load polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const libraryItems = page.locator('.library-item');
    const itemCount = await libraryItems.count();
    
    if (itemCount > 0) {
      console.log(`System recovered: ${itemCount} polyhedra loaded`);
    }
    
    // Step 3: Test generation after recovery
    if (itemCount >= 2) {
      await libraryItems.first().click();
      await page.waitForTimeout(300);
      await libraryItems.nth(1).click();
      await page.waitForTimeout(500);
      
      const generateButton = page.locator('.generate-button');
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(2000);
        
        // Should work after recovery
        const generatedItems = page.locator('.generated-polyform-item');
        await expect(generatedItems.first()).toBeVisible({ timeout: 5000 });
      }
    }
    
    // Step 4: Test network interruption during generation
    if (itemCount >= 2) {
      // Simulate network failure during generation
      await page.route('**/api/polyform/generate', route => route.abort());
      
      await libraryItems.first().click();
      await page.waitForTimeout(300);
      await libraryItems.nth(1).click();
      await page.waitForTimeout(500);
      
      const generateButton = page.locator('.generate-button');
      await generateButton.click();
      await page.waitForTimeout(1000);
      
      // Should show error state, not crash
      const errorElement = page.locator('.generator-error, .error-message');
      if (await errorElement.count() > 0) {
        await expect(errorElement.first()).toBeVisible();
        console.log('Error handling working correctly');
      }
      
      // System should remain functional
      await expect(canvas).toBeVisible();
      await expect(appLayout).toBeVisible();
    }
    
    console.log('Error recovery journey completed successfully');
  });

  test('Journey 6: Accessibility User - Keyboard Navigation', async ({ page }) => {
    // Journey testing accessibility and keyboard navigation
    
    // Step 1: User navigates using keyboard only
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);
    
    // Should focus on interactive elements
    const focusedElement = await page.evaluate(() => document.activeElement.tagName);
    expect(['BUTTON', 'INPUT', 'SELECT', 'A', 'CANVAS'].includes(focusedElement)).toBe(true);
    
    // Step 2: Navigate through library items
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Tab to library items
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);
    }
    
    // Select with keyboard
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);
    
    // Step 3: Navigate to second item
    await page.keyboard.press('Tab');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);
    
    // Step 4: Generate with keyboard
    const generateButton = page.locator('.generate-button');
    await generateButton.focus();
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2000);
    
    // Step 5: Verify generation worked
    const generatedItems = page.locator('.generated-polyform-item');
    if (await generatedItems.count() > 0) {
      await expect(generatedItems.first()).toBeVisible();
      console.log('Keyboard navigation journey completed successfully');
    }
    
    // Step 6: Test keyboard shortcuts if available
    await page.keyboard.press('Escape'); // Common cancel/close shortcut
    await page.waitForTimeout(200);
    
    // System should remain responsive
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });
});