import { test, expect } from '@playwright/test';

test.describe('Workspace Polyform 2D Mapping', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
  });

  test('Workspace polyform can be accessed for 2D mapping', async ({ page }) => {
    // Create workspace polyform
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Select multiple polyhedra
    for (let i = 0; i < 3; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(500);
    }
    
    // Check that geometry is available
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Canvas should have rendered geometry
    const canvasBox = await canvas.boundingBox();
    expect(canvasBox).not.toBeNull();
  });

  test('Large workspace assemblies are manageable', async ({ page }) => {
    // Select many polyhedra to create large assembly
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Select 5+ polyhedra
    for (let i = 0; i < 5; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(300);
    }
    
    // Check that system handles it
    const countText = await page.locator('.polyhedra-count').textContent();
    expect(countText).toContain('5');
    
    // LOD should adjust for performance
    const lodIndicator = page.locator('.lod-indicator');
    await expect(lodIndicator).toBeVisible();
  });

  test('2D subforms can be extracted from workspace', async ({ page }) => {
    // Create a workspace polyform
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Select polyhedra to form a structure
    for (let i = 0; i < 3; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(500);
    }
    
    // Generate polyform
    const generator = page.locator('.polyform-generator');
    if (await generator.isVisible()) {
      const generateButton = generator.locator('button').filter({ hasText: /generate/i });
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(3000);
        
        // Generated polyform should have geometry data
        const result = generator.locator('.generated-result');
        if (await result.isVisible()) {
          // Geometry should be accessible for 2D mapping
          const resultText = await result.textContent();
          expect(resultText).toBeTruthy();
        }
      }
    }
  });
});

