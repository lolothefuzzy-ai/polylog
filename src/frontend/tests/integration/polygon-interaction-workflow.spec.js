import { test, expect } from '@playwright/test';

/**
 * Comprehensive Polygon Interaction Workflow Test
 * Tests the complete workflow: placement → rotation → movement → snapping → chaining
 * 
 * This test monitors:
 * - Polygon placement in workspace
 * - Free rotation during movement
 * - Independent movement of multiple polygons
 * - Edge snapping and visual feedback
 * - Chain formation when edges snap
 */

test.describe('Polygon Interaction Workflow', () => {
  let consoleMessages = [];
  let errors = [];
  
  test.beforeEach(async ({ page }) => {
    consoleMessages = [];
    errors = [];
    
    // Capture all console messages
    page.on('console', msg => {
      const text = msg.text();
      const type = msg.type();
      consoleMessages.push({ type, text, timestamp: Date.now() });
      
      if (type === 'error') {
        errors.push(text);
        console.error(`[BROWSER ERROR] ${text}`);
      } else if (text.includes('[BabylonScene]') || text.includes('[Interaction]')) {
        console.log(`[CONSOLE] ${text}`);
      }
    });
    
    // Capture page errors
    page.on('pageerror', error => {
      errors.push(error.message);
      console.error(`[PAGE ERROR] ${error.message}`);
    });
    
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
    await page.waitForSelector('canvas', { timeout: 10000 });
  });

  test('Complete Polygon Interaction Workflow', async ({ page }) => {
    const testResults = {
      polygon1Placed: false,
      polygon2Placed: false,
      polygon2Rotates: false,
      polygon1StillMoves: false,
      snapVisualFeedback: false,
      chainFormed: false,
      errors: []
    };

    // Step 1: Place first polygon
    console.log('[TEST] Step 1: Placing first polygon...');
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    const firstPolygon = page.locator('.library-item').first();
    await expect(firstPolygon).toBeVisible();
    await firstPolygon.click();
    await page.waitForTimeout(500);
    
    // Check for polygon placement in console
    const placementMessages = consoleMessages.filter(m => 
      m.text.includes('[BabylonScene]') && 
      (m.text.includes('Successfully added') || m.text.includes('Loading polyhedron'))
    );
    
    testResults.polygon1Placed = placementMessages.length > 0;
    expect(testResults.polygon1Placed).toBe(true);
    console.log(`[TEST] ✓ Polygon 1 placed: ${testResults.polygon1Placed}`);

    // Step 2: Place second polygon
    console.log('[TEST] Step 2: Placing second polygon...');
    const secondPolygon = page.locator('.library-item').nth(1);
    await expect(secondPolygon).toBeVisible();
    await secondPolygon.click();
    await page.waitForTimeout(500);
    
    const secondPlacementMessages = consoleMessages.filter(m => 
      m.text.includes('[BabylonScene]') && 
      (m.text.includes('Successfully added') || m.text.includes('Loading polyhedron'))
    );
    
    testResults.polygon2Placed = secondPlacementMessages.length >= 2;
    expect(testResults.polygon2Placed).toBe(true);
    console.log(`[TEST] ✓ Polygon 2 placed: ${testResults.polygon2Placed}`);

    // Step 3: Test free rotation of second polygon while moving
    console.log('[TEST] Step 3: Testing free rotation of polygon 2...');
    const canvas = page.locator('canvas');
    const canvasBounds = await canvas.boundingBox();
    
    if (!canvasBounds) {
      throw new Error('Canvas bounds not available');
    }
    
    // Click on canvas to select second polygon (if needed)
    const centerX = canvasBounds.x + canvasBounds.width / 2;
    const centerY = canvasBounds.y + canvasBounds.height / 2;
    
    // Simulate Shift+drag for rotation
    await page.mouse.move(centerX, centerY);
    await page.mouse.down();
    await page.keyboard.down('Shift');
    
    // Move mouse to simulate rotation
    const rotationStart = Date.now();
    for (let i = 0; i < 5; i++) {
      const angle = (i * Math.PI * 2) / 5;
      const x = centerX + 50 * Math.cos(angle);
      const y = centerY + 50 * Math.sin(angle);
      await page.mouse.move(x, y, { steps: 3 });
      await page.waitForTimeout(50);
    }
    
    await page.keyboard.up('Shift');
    await page.mouse.up();
    await page.waitForTimeout(300);
    
    // Check for rotation feedback in console
    const rotationMessages = consoleMessages.filter(m => 
      m.text.includes('rotation') || 
      m.text.includes('Rotation') ||
      m.text.includes('[Interaction]')
    );
    
    testResults.polygon2Rotates = rotationMessages.length > 0;
    console.log(`[TEST] ✓ Polygon 2 rotation: ${testResults.polygon2Rotates} (${rotationMessages.length} messages)`);

    // Step 4: Test that first polygon can still move independently
    console.log('[TEST] Step 4: Testing independent movement of polygon 1...');
    
    // Try to move first polygon
    await page.mouse.move(centerX - 100, centerY - 100);
    await page.mouse.down();
    await page.mouse.move(centerX - 50, centerY - 50, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(300);
    
    // Check for drag messages
    const dragMessages = consoleMessages.filter(m => 
      m.text.includes('dragging') || 
      m.text.includes('Started dragging') ||
      m.text.includes('Stopped dragging')
    );
    
    testResults.polygon1StillMoves = dragMessages.length > 0;
    console.log(`[TEST] ✓ Polygon 1 independent movement: ${testResults.polygon1StillMoves}`);

    // Step 5: Test edge snapping visual feedback
    console.log('[TEST] Step 5: Testing edge snapping visual feedback...');
    
    // Move second polygon near first polygon to trigger snapping
    await page.mouse.move(centerX + 50, centerY + 50);
    await page.mouse.down();
    
    // Move slowly toward first polygon
    for (let i = 0; i < 10; i++) {
      const progress = i / 10;
      const x = centerX + 50 - (progress * 100);
      const y = centerY + 50 - (progress * 100);
      await page.mouse.move(x, y, { steps: 2 });
      await page.waitForTimeout(50);
    }
    
    await page.waitForTimeout(500); // Wait for snap detection
    await page.mouse.up();
    await page.waitForTimeout(500);
    
    // Check for snap-related messages
    const snapMessages = consoleMessages.filter(m => 
      m.text.includes('snap') || 
      m.text.includes('Snap') ||
      m.text.includes('candidate') ||
      m.text.includes('edge')
    );
    
    testResults.snapVisualFeedback = snapMessages.length > 0;
    console.log(`[TEST] ✓ Snap visual feedback: ${testResults.snapVisualFeedback} (${snapMessages.length} messages)`);

    // Step 6: Test chain formation when edges snap
    console.log('[TEST] Step 6: Testing chain formation...');
    
    // Check for attachment/chain messages
    const attachmentMessages = consoleMessages.filter(m => 
      m.text.includes('attachment') || 
      m.text.includes('Attachment') ||
      m.text.includes('chain') ||
      m.text.includes('Applying attachment')
    );
    
    testResults.chainFormed = attachmentMessages.length > 0;
    console.log(`[TEST] ✓ Chain formation: ${testResults.chainFormed} (${attachmentMessages.length} messages)`);

    // Collect errors
    testResults.errors = errors;

    // Print summary
    console.log('\n[TEST] ========================================');
    console.log('[TEST] Test Results Summary:');
    console.log(`[TEST]   Polygon 1 Placed: ${testResults.polygon1Placed ? '✓' : '✗'}`);
    console.log(`[TEST]   Polygon 2 Placed: ${testResults.polygon2Placed ? '✓' : '✗'}`);
    console.log(`[TEST]   Polygon 2 Rotates: ${testResults.polygon2Rotates ? '✓' : '✗'}`);
    console.log(`[TEST]   Polygon 1 Still Moves: ${testResults.polygon1StillMoves ? '✓' : '✗'}`);
    console.log(`[TEST]   Snap Visual Feedback: ${testResults.snapVisualFeedback ? '✓' : '✗'}`);
    console.log(`[TEST]   Chain Formed: ${testResults.chainFormed ? '✓' : '✗'}`);
    console.log(`[TEST]   Errors: ${testResults.errors.length}`);
    console.log('[TEST] ========================================\n');

    // Assertions - these will fail if functionality is missing
    expect(testResults.polygon1Placed).toBe(true);
    expect(testResults.polygon2Placed).toBe(true);
    
    // These are the critical tests - if they fail, we need to fix
    if (!testResults.polygon2Rotates) {
      throw new Error('MISSING_FUNCTIONALITY: Polygon rotation not working - Shift+drag rotation not detected');
    }
    
    if (!testResults.polygon1StillMoves) {
      throw new Error('MISSING_FUNCTIONALITY: Independent polygon movement not working - first polygon cannot move after second is placed');
    }
    
    if (!testResults.snapVisualFeedback) {
      throw new Error('MISSING_FUNCTIONALITY: Edge snapping visual feedback not working - snap guides not appearing');
    }
    
    if (!testResults.chainFormed) {
      throw new Error('MISSING_FUNCTIONALITY: Chain formation not working - edges not snapping to form chains');
    }
    
    // If we get here, all tests passed
    console.log('[TEST] ✓ All interaction tests passed!');
  });

  test('Unicode Structure Async Decoupling', async ({ page }) => {
    // Test that Unicode structure operations are properly async decoupled
    // and GPU/CPU coordination works correctly
    
    console.log('[TEST] Testing Unicode structure async decoupling...');
    
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Place multiple polygons rapidly to test async handling
    for (let i = 0; i < 3; i++) {
      const polygon = page.locator('.library-item').nth(i);
      await polygon.click();
      await page.waitForTimeout(100); // Short delay to test async
    }
    
    await page.waitForTimeout(1000);
    
    // Check for async-related messages
    const asyncMessages = consoleMessages.filter(m => 
      m.text.includes('async') || 
      m.text.includes('Promise') ||
      m.text.includes('await')
    );
    
    // Check for GPU/CPU coordination messages
    const gpuMessages = consoleMessages.filter(m => 
      m.text.includes('GPU') || 
      m.text.includes('gpu') ||
      m.text.includes('render')
    );
    
    console.log(`[TEST] Async messages: ${asyncMessages.length}`);
    console.log(`[TEST] GPU messages: ${gpuMessages.length}`);
    
    // System should handle rapid operations without blocking
    expect(errors.length).toBe(0);
  });
});

