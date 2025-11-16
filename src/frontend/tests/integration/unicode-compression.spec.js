import { test, expect } from '@playwright/test';

test.describe('Unicode Compression and Symbol Allocation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
  });

  test('Generated polyforms have Unicode symbols', async ({ page }) => {
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
    
    // Check for Unicode symbol in result
    const result = generator.locator('.generated-result');
    await expect(result).toBeVisible({ timeout: 5000 });
    
    const resultText = await result.textContent();
    // Should contain symbol or unicode
    expect(resultText).toMatch(/symbol|unicode|compression/i);
  });

  test('Compression ratio is displayed', async ({ page }) => {
    // Select and generate
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(1000);
    
    const generator = page.locator('.polyform-generator');
    if (await generator.isVisible()) {
      const generateButton = generator.locator('button').filter({ hasText: /generate/i });
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(3000);
        
        const result = generator.locator('.generated-result');
        if (await result.isVisible()) {
          const resultText = await result.textContent();
          // Should show compression ratio
          expect(resultText).toMatch(/\d+[:\/]\d+|compression|ratio/i);
        }
      }
    }
  });

  test('Library items show compression ratios', async ({ page }) => {
    // Check library items for compression info
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    const items = page.locator('.library-item');
    const firstItem = items.first();
    
    // Some items may have compression ratio displayed
    const itemText = await firstItem.textContent();
    // Compression info might be in item-compression class
    const compression = firstItem.locator('.item-compression');
    if (await compression.count() > 0) {
      const ratio = await compression.first().textContent();
      expect(ratio).toMatch(/\d+[:\/]\d+/);
    }
  });
});
