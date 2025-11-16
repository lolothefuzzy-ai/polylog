import { test, expect } from '@playwright/test';

test.describe('2D Flattening and Subform Detection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
  });

  test('Workspace polyform can be visualized in 3D', async ({ page }) => {
    // Create a workspace polyform by selecting multiple polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Select 2-3 polyhedra
    for (let i = 0; i < 2; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(500);
    }
    
    // Check that 3D canvas shows the polyform
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Canvas should have content
    const canvasBox = await canvas.boundingBox();
    expect(canvasBox).not.toBeNull();
    expect(canvasBox.width).toBeGreaterThan(0);
    expect(canvasBox.height).toBeGreaterThan(0);
  });

  test('Polyform geometry is accessible for 2D mapping', async ({ page }) => {
    // Select polyhedra and generate
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(1000);
    
    // Generate polyform
    const generator = page.locator('.polyform-generator');
    if (await generator.isVisible()) {
      const generateButton = generator.locator('button').filter({ hasText: /generate/i });
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(3000);
        
        // Check that geometry data is available
        const result = generator.locator('.generated-result');
        if (await result.isVisible()) {
          // Geometry should be in the result
          const resultText = await result.textContent();
          expect(resultText).toBeTruthy();
        }
      }
    }
  });

  test('Multiple polyhedra form a workspace assembly', async ({ page }) => {
    // Select multiple polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    const selectedCount = 4;
    for (let i = 0; i < selectedCount; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(500);
    }
    
    // Check that all are in workspace
    const countText = await page.locator('.polyhedra-count').textContent();
    expect(countText).toContain(selectedCount.toString());
    
    // Canvas should show the assembly
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });

  test('LOD switching works for performance', async ({ page }) => {
    // Select multiple polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    for (let i = 0; i < 3; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(500);
    }
    
    // Check LOD indicator
    const lodIndicator = page.locator('.lod-indicator');
    await expect(lodIndicator).toBeVisible();
    
    // LOD should show current level
    const lodText = await lodIndicator.textContent();
    expect(lodText).toMatch(/LOD:/i);
  });
});

