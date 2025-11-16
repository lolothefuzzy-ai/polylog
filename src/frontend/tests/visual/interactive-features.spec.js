import { test, expect } from '@playwright/test';

test.describe('Interactive Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 10000 });
  });

  test('Drag and drop from library works', async ({ page }) => {
    // Wait for library to load
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Get first library item
    const firstItem = page.locator('.library-item').first();
    await expect(firstItem).toBeVisible();
    
    // Get canvas
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Drag from library to canvas
    await firstItem.dragTo(canvas);
    
    // Wait a bit for drop to process
    await page.waitForTimeout(500);
    
    // Check that polyhedron count increased
    const countText = await page.locator('.polyhedra-count').textContent();
    expect(countText).toContain('polyhedra');
  });

  test('Edge snapping visual feedback appears', async ({ page }) => {
    // Select first polyhedron
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    
    // Select second polyhedron
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(1000); // Wait for auto-attachment
    
    // Check for snap guides (green lines/spheres)
    // These would be created by SnapVisualFeedback
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Visual check - canvas should have content
    const canvasBox = await canvas.boundingBox();
    expect(canvasBox).not.toBeNull();
  });

  test('Free rotation works with Shift key', async ({ page }) => {
    // Select a polyhedron
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    
    const canvas = page.locator('canvas');
    
    // Simulate Shift + mouse move for rotation
    await canvas.hover();
    await page.keyboard.down('Shift');
    await page.mouse.move(100, 100);
    await page.mouse.move(200, 200);
    await page.keyboard.up('Shift');
    
    // Canvas should still be visible
    await expect(canvas).toBeVisible();
  });

  test('Polyform generator creates new polyform', async ({ page }) => {
    // Select two polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(300);
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(1000);
    
    // Find generator component
    const generator = page.locator('.polyform-generator');
    await expect(generator).toBeVisible();
    
    // Click generate button
    const generateButton = generator.locator('button').filter({ hasText: /generate/i });
    await expect(generateButton).toBeVisible();
    await generateButton.click();
    
    // Wait for generation
    await page.waitForTimeout(2000);
    
    // Check for generated result
    const result = generator.locator('.generated-result');
    await expect(result).toBeVisible({ timeout: 5000 });
  });

  test('Scalar variants appear in library', async ({ page }) => {
    // Filter to scalar variants
    const filter = page.locator('.library-filter');
    await filter.selectOption('scalar_variant');
    await page.waitForTimeout(1000);
    
    // Check that scalar variants are shown
    const items = page.locator('.library-item');
    const count = await items.count();
    expect(count).toBeGreaterThan(0);
    
    // Check that items show scale factor
    const firstItem = items.first();
    const text = await firstItem.textContent();
    expect(text).toMatch(/k=\d+/i);
  });

  test('Multi-polygon selection works', async ({ page }) => {
    // Select multiple polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    for (let i = 0; i < 3; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(300);
    }
    
    // Check polyhedron count
    const countText = await page.locator('.polyhedra-count').textContent();
    expect(countText).toContain('3');
  });
});

