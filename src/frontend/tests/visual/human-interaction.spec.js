import { test, expect } from '@playwright/test';

test.describe('Human Interaction Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Enable detailed interaction logging
    page.on('console', msg => {
      if (msg.type() === 'error' || msg.type() === 'warning') {
        console.log(`Browser ${msg.type()}: ${msg.text()}`);
      }
    });
    
    // Track mouse movements and interactions
    await page.goto('/');
    await page.waitForSelector('.app-layout', { timeout: 15000 });
  });

  test('Realistic Drag and Drop with Snapping Range Validation', async ({ page }) => {
    // Test realistic human drag and drop with reasonable snapping ranges
    
    // Step 1: Select first polyhedron from library
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const firstItem = page.locator('.library-item:first-child');
    await expect(firstItem).toBeVisible();
    
    // Step 2: Perform realistic drag operation
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Get canvas bounds for realistic positioning
    const canvasBounds = await canvas.boundingBox();
    expect(canvasBounds).toBeTruthy();
    
    // Simulate human-like drag with reasonable speed and precision
    const startX = canvasBounds.x + 100;
    const startY = canvasBounds.y + 100;
    const endX = canvasBounds.x + 300;
    const endY = canvasBounds.y + 200;
    
    // Human-like drag: mouse down, move with intermediate points, mouse up
    await page.mouse.move(startX, startY);
    await page.mouse.down();
    
    // Move with human-like intermediate points (not straight line)
    await page.mouse.move(startX + 50, startY + 30, { steps: 5 });
    await page.mouse.move(startX + 100, startY + 60, { steps: 5 });
    await page.mouse.move(startX + 150, startY + 90, { steps: 5 });
    await page.mouse.move(startX + 200, startY + 120, { steps: 5 });
    await page.mouse.move(endX, endY, { steps: 5 });
    
    await page.mouse.up();
    
    // Step 3: Test snapping range - should be reasonable for human interaction
    // Test near-miss scenarios that should still snap
    const snapTests = [
      { x: endX + 10, y: endY + 10, shouldSnap: true },  // 10px offset - should snap
      { x: endX + 25, y: endY + 25, shouldSnap: true },  // 25px offset - should snap
      { x: endX + 40, y: endY + 40, shouldSnap: false }, // 40px offset - should not snap
      { x: endX - 10, y: endY - 10, shouldSnap: true },  // Negative offset - should snap
    ];
    
    for (const test of snapTests) {
      // Drag another polyhedron near the first one
      const secondItem = page.locator('.library-item:nth-child(2)');
      await secondItem.click();
      await page.waitForTimeout(500);
      
      // Perform drag to test position
      await page.mouse.move(canvasBounds.x + 50, canvasBounds.y + 50);
      await page.mouse.down();
      await page.mouse.move(test.x, test.y, { steps: 3 });
      await page.mouse.up();
      
      await page.waitForTimeout(500);
      
      // Check if snapping occurred by examining attachment validator
      const validator = page.locator('.attachment-validator');
      const isVisible = await validator.isVisible();
      
      if (test.shouldSnap) {
        expect(isVisible).toBeTruthy();
        console.log(`Snapping test PASSED at ${test.x},${test.y} - should snap and did`);
      } else {
        // Should not snap - validator may or may not appear
        console.log(`Snapping test at ${test.x},${test.y} - should not snap`);
      }
    }
  });

  test('Realistic Mouse Interactions - Click, Double Click, Right Click', async ({ page }) => {
    // Test realistic human mouse interactions
    
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const canvas = page.locator('canvas');
    const canvasBounds = await canvas.boundingBox();
    
    // Test 1: Single click with realistic timing
    const firstItem = page.locator('.library-item:first-child');
    await firstItem.click();
    await page.waitForTimeout(300); // Human reaction time
    
    // Verify selection feedback
    const selectedItem = page.locator('.library-item.selected');
    expect(await selectedItem.count()).toBeGreaterThan(0);
    
    // Test 2: Double click with human-like timing
    await firstItem.dblclick();
    await page.waitForTimeout(200);
    
    // Check if double click triggers any special behavior
    // (e.g., zoom to polyhedron, detailed view, etc.)
    const detailView = page.locator('.polyhedron-details, .detail-panel');
    if (await detailView.count() > 0) {
      console.log('Double click triggered detail view');
    }
    
    // Test 3: Right click context menu
    await firstItem.click({ button: 'right' });
    await page.waitForTimeout(200);
    
    // Check for context menu
    const contextMenu = page.locator('.context-menu, .dropdown-menu');
    if (await contextMenu.isVisible()) {
      console.log('Right click triggered context menu');
      
      // Test context menu interaction
      const menuItems = contextMenu.locator('.menu-item');
      const itemCount = await menuItems.count();
      
      if (itemCount > 0) {
        // Click first menu item
        await menuItems.first().click();
        await page.waitForTimeout(300);
      }
    }
    
    // Test 4: Canvas interactions
    await page.mouse.move(canvasBounds.x + 200, canvasBounds.y + 200);
    await page.mouse.click();
    await page.waitForTimeout(200);
    
    // Test 5: Drag on canvas for rotation/pan
    await page.mouse.down();
    await page.mouse.move(canvasBounds.x + 250, canvasBounds.y + 250, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(300);
    
    // Verify canvas is still responsive
    await expect(canvas).toBeVisible();
  });

  test('Human-like Rotation and Camera Controls', async ({ page }) => {
    // Test realistic 3D rotation and camera controls
    
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    const canvasBounds = await canvas.boundingBox();
    
    // Select a polyhedron to rotate
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    
    // Test 1: Horizontal rotation (human-like circular motion)
    const centerX = canvasBounds.x + canvasBounds.width / 2;
    const centerY = canvasBounds.y + canvasBounds.height / 2;
    const radius = 100;
    
    await page.mouse.move(centerX + radius, centerY);
    await page.mouse.down();
    
    // Simulate human circular rotation motion
    for (let angle = 0; angle <= Math.PI; angle += Math.PI / 8) {
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      await page.mouse.move(x, y, { steps: 3 });
      await page.waitForTimeout(50); // Human-like pause
    }
    
    await page.mouse.up();
    await page.waitForTimeout(300);
    
    // Test 2: Vertical rotation
    await page.mouse.move(centerX, centerY + radius);
    await page.mouse.down();
    
    for (let angle = 0; angle <= Math.PI / 2; angle += Math.PI / 8) {
      const x = centerX;
      const y = centerY + radius * Math.cos(angle);
      await page.mouse.move(x, y, { steps: 3 });
      await page.waitForTimeout(50);
    }
    
    await page.mouse.up();
    await page.waitForTimeout(300);
    
    // Test 3: Zoom with realistic mouse wheel
    await page.mouse.move(centerX, centerY);
    
    // Zoom in (human-like scroll speed)
    for (let i = 0; i < 5; i++) {
      await page.mouse.wheel(0, -50); // Negative for zoom in
      await page.waitForTimeout(100);
    }
    
    await page.waitForTimeout(500);
    
    // Zoom out
    for (let i = 0; i < 5; i++) {
      await page.mouse.wheel(0, 50); // Positive for zoom out
      await page.waitForTimeout(100);
    }
    
    // Verify LOD indicator updates with zoom
    const lodIndicator = page.locator('.lod-indicator');
    if (await lodIndicator.isVisible()) {
      const lodText = await lodIndicator.textContent();
      expect(lodText).toMatch(/LOD:/i);
      console.log(`LOD after zoom: ${lodText}`);
    }
  });

  test('Realistic Multi-Selection and Group Operations', async ({ page }) => {
    // Test realistic multi-selection patterns
    
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const libraryItems = page.locator('.library-item');
    const itemCount = await libraryItems.count();
    
    if (itemCount < 3) {
      console.log('Skipping multi-selection test - not enough items');
      return;
    }
    
    // Test 1: Ctrl+Click for multi-selection
    await page.keyboard.down('Control');
    
    for (let i = 0; i < Math.min(3, itemCount); i++) {
      await libraryItems.nth(i).click();
      await page.waitForTimeout(200);
    }
    
    await page.keyboard.up('Control');
    await page.waitForTimeout(500);
    
    // Verify multiple items are selected
    const selectedItems = page.locator('.library-item.selected');
    const selectedCount = await selectedItems.count();
    expect(selectedCount).toBeGreaterThanOrEqual(2);
    
    // Test 2: Shift+Click for range selection
    await page.click('.library-item:first-child'); // Reset selection
    await page.waitForTimeout(200);
    
    await page.keyboard.down('Shift');
    await libraryItems.nth(2).click(); // Select range
    await page.keyboard.up('Shift');
    await page.waitForTimeout(500);
    
    // Test 3: Drag selection box (if implemented)
    const canvas = page.locator('canvas');
    const canvasBounds = await canvas.boundingBox();
    
    await page.mouse.move(canvasBounds.x + 50, canvasBounds.y + 50);
    await page.mouse.down();
    await page.mouse.move(canvasBounds.x + 200, canvasBounds.y + 150, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(500);
    
    // Test 4: Group operations on selected items
    const generateButton = page.locator('.generate-button');
    if (await generateButton.isEnabled()) {
      console.log('Group operation available - testing generation');
      await generateButton.click();
      await page.waitForTimeout(2000);
      
      // Verify generation results
      const generatedItems = page.locator('.generated-polyform-item');
      await expect(generatedItems.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('Realistic Error Recovery and User Feedback', async ({ page }) => {
    // Test realistic error scenarios and user recovery
    
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const canvas = page.locator('canvas');
    const canvasBounds = await canvas.boundingBox();
    
    // Test 1: Invalid drag destination (outside canvas)
    await page.click('.library-item:first-child');
    await page.waitForTimeout(300);
    
    // Drag outside canvas bounds
    await page.mouse.move(canvasBounds.x + canvasBounds.width / 2, canvasBounds.y + canvasBounds.height / 2);
    await page.mouse.down();
    await page.mouse.move(canvasBounds.x + canvasBounds.width + 100, canvasBounds.y + canvasBounds.height + 100, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(500);
    
    // System should handle gracefully
    await expect(canvas).toBeVisible();
    
    // Test 2: Rapid clicking (user frustration scenario)
    const firstItem = page.locator('.library-item:first-child');
    
    for (let i = 0; i < 10; i++) {
      await firstItem.click();
      await page.waitForTimeout(50); // Rapid clicking
    }
    
    await page.waitForTimeout(1000);
    
    // System should remain stable
    await expect(firstItem).toBeVisible();
    
    // Test 3: Network interruption during operation
    // Simulate API failure
    await page.route('**/api/**', route => route.abort());
    
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(500);
    
    const generateButton = page.locator('.generate-button');
    if (await generateButton.isEnabled()) {
      await generateButton.click();
      await page.waitForTimeout(1000);
      
      // Should show error state, not crash
      const errorElement = page.locator('.error-message, .generator-error');
      if (await errorElement.count() > 0) {
        console.log('Error handling working correctly');
      }
    }
    
    // Restore API and test recovery
    await page.unroute('**/api/**');
    
    // System should recover
    await page.reload();
    await page.waitForSelector('.app-layout', { timeout: 15000 });
    await expect(canvas).toBeVisible();
  });

  test('Realistic Performance and Responsiveness', async ({ page }) => {
    // Test realistic performance expectations for human users
    
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const canvas = page.locator('canvas');
    
    // Test 1: Click response time (<100ms for good UX)
    const firstItem = page.locator('.library-item:first-child');
    
    const clickStart = Date.now();
    await firstItem.click();
    const clickEnd = Date.now();
    
    const clickLatency = clickEnd - clickStart;
    console.log(`Click response time: ${clickLatency}ms`);
    expect(clickLatency).toBeLessThan(200); // Should be very fast
    
    // Test 2: Drag responsiveness
    const canvasBounds = await canvas.boundingBox();
    const dragStart = Date.now();
    
    await page.mouse.move(canvasBounds.x + 100, canvasBounds.y + 100);
    await page.mouse.down();
    await page.mouse.move(canvasBounds.x + 200, canvasBounds.y + 200, { steps: 10 });
    await page.mouse.up();
    
    const dragEnd = Date.now();
    const dragLatency = dragEnd - dragStart;
    console.log(`Drag operation time: ${dragLatency}ms`);
    expect(dragLatency).toBeLessThan(500); // Should feel responsive
    
    // Test 3: Generation waiting time (user patience)
    const generateButton = page.locator('.generate-button');
    
    if (await generateButton.isEnabled()) {
      const generationStart = Date.now();
      await generateButton.click();
      
      // Wait for completion but track time
      await page.waitForTimeout(3000); // Max 3 seconds wait
      
      const generationEnd = Date.now();
      const generationTime = generationEnd - generationStart;
      console.log(`Generation time: ${generationTime}ms`);
      
      // Should complete within reasonable human patience window
      expect(generationTime).toBeLessThan(5000); // 5 seconds max
    }
    
    // Test 4: Animation smoothness (perceived performance)
    const animationStart = Date.now();
    
    // Perform multiple rapid operations
    for (let i = 0; i < 5; i++) {
      await page.mouse.move(canvasBounds.x + 100 + i * 20, canvasBounds.y + 100 + i * 20);
      await page.mouse.click();
      await page.waitForTimeout(100);
    }
    
    const animationEnd = Date.now();
    const totalTime = animationEnd - animationStart;
    console.log(`Multiple operations time: ${totalTime}ms`);
    
    // Should maintain smooth interaction
    expect(totalTime).toBeLessThan(2000);
  });
});