import { test, expect } from '@playwright/test';

test.describe('Tier Structure and Unicode Mapping', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
  });

  test('Tier 0 primitives are accessible', async ({ page }) => {
    // Check that we can access primitive polygons (Tier 0)
    const library = page.locator('.polyhedra-library');
    await expect(library).toBeVisible();
    
    // Library should load polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const items = page.locator('.library-item');
    const count = await items.count();
    expect(count).toBeGreaterThan(0);
    
    // Check that items have symbols (Unicode mapping)
    const firstItem = items.first();
    const symbol = firstItem.locator('.item-symbol');
    await expect(symbol).toBeVisible();
    const symbolText = await symbol.textContent();
    expect(symbolText).toBeTruthy();
    expect(symbolText.length).toBeGreaterThan(0);
  });

  test('Tier 1 polyhedra load correctly', async ({ page }) => {
    // Select a polyhedron from library
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(1000);
    
    // Check that it appears in workspace
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Check polyhedron count
    const countText = await page.locator('.polyhedra-count').textContent();
    expect(countText).toContain('1');
  });

  test('Unicode symbol allocation works for generated polyforms', async ({ page }) => {
    // Select two polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(1000);
    
    // Generate polyform
    const generator = page.locator('.polyform-generator');
    await expect(generator).toBeVisible();
    
    const generateButton = generator.locator('button').filter({ hasText: /generate/i });
    await generateButton.click();
    await page.waitForTimeout(3000);
    
    // Check for generated result with Unicode symbol
    const result = generator.locator('.generated-result');
    await expect(result).toBeVisible({ timeout: 5000 });
    
    // Check that Unicode symbol is displayed
    const symbolText = await result.textContent();
    expect(symbolText).toMatch(/symbol|unicode/i);
  });

  test('Node chain structure is preserved in composition', async ({ page }) => {
    // Select multiple polyhedra to create a chain
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Select 3 polyhedra
    for (let i = 0; i < 3; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(500);
    }
    
    // Check that composition reflects the chain
    const countText = await page.locator('.polyhedra-count').textContent();
    expect(countText).toContain('3');
    
    // Generate polyform to see composition
    const generator = page.locator('.polyform-generator');
    if (await generator.isVisible()) {
      const generateButton = generator.locator('button').filter({ hasText: /generate/i });
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(3000);
        
        // Check composition string
        const result = generator.locator('.generated-result');
        if (await result.isVisible()) {
          const composition = await result.textContent();
          expect(composition).toBeTruthy();
        }
      }
    }
  });

  test('Scalar variants maintain tier structure', async ({ page }) => {
    // Filter to scalar variants
    const filter = page.locator('.library-filter');
    await filter.selectOption('scalar_variant');
    await page.waitForTimeout(1000);
    
    // Check that scalar variants are shown
    const items = page.locator('.library-item');
    const count = await items.count();
    expect(count).toBeGreaterThan(0);
    
    // Select a scalar variant
    await items.first().click();
    await page.waitForTimeout(500);
    
    // Check that it loads correctly
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });
});

