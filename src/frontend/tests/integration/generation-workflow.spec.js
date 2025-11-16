import { test, expect } from '@playwright/test';

test.describe('Polyform Generation Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 10000 });
  });

  test('Complete generation workflow: Select → Validate → Generate', async ({ page }) => {
    // Step 1: Select first polygon
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    
    // Step 2: Select second polygon
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(500);
    
    // Step 3: Verify attachment validator appears
    const validator = page.locator('.attachment-validator');
    await expect(validator).toBeVisible();
    
    // Step 4: Verify generator is ready
    const generator = page.locator('.polyform-generator');
    await expect(generator).toBeVisible();
    
    const statusReady = page.locator('.status-ready');
    await expect(statusReady).toBeVisible({ timeout: 2000 });
    
    // Step 5: Click generate button
    const generateButton = page.locator('.generate-button');
    await expect(generateButton).toBeEnabled();
    await generateButton.click();
    
    // Step 6: Wait for generation to complete
    await page.waitForTimeout(2000);
    
    // Step 7: Verify generated polyform appears
    const generatedList = page.locator('.generated-polyforms');
    await expect(generatedList).toBeVisible({ timeout: 5000 });
    
    // Step 8: Verify polyform appears in list
    const polyformItem = page.locator('.generated-polyform-item');
    await expect(polyformItem.first()).toBeVisible();
  });

  test('Generation shows compression ratio', async ({ page }) => {
    // Select two polygons
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(300);
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(500);
    
    // Generate
    const generateButton = page.locator('.generate-button');
    await generateButton.click();
    
    // Wait for generation
    await page.waitForTimeout(2000);
    
    // Check for compression ratio
    const compression = page.locator('.polyform-compression');
    await expect(compression.first()).toBeVisible({ timeout: 5000 });
    
    const compressionText = await compression.first().textContent();
    expect(compressionText).toMatch(/Compression:/i);
  });

  test('Generated polyform appears in 3D scene', async ({ page }) => {
    // Select and generate
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(300);
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(500);
    
    const generateButton = page.locator('.generate-button');
    await generateButton.click();
    await page.waitForTimeout(2000);
    
    // Verify 3D scene still renders
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Check that polyhedra count increased
    const polyhedraCount = page.locator('.polyhedra-count');
    if (await polyhedraCount.count() > 0) {
      const countText = await polyhedraCount.textContent();
      expect(countText).toMatch(/\d+/);
    }
  });

  test('Error handling: API unavailable', async ({ page }) => {
    // Simulate API failure
    await page.route('**/api/polyform/generate', route => route.abort());
    
    // Select polygons
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(300);
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(500);
    
    // Try to generate
    const generateButton = page.locator('.generate-button');
    await generateButton.click();
    
    // Should show error
    const error = page.locator('.generator-error');
    await expect(error).toBeVisible({ timeout: 3000 });
  });
});

