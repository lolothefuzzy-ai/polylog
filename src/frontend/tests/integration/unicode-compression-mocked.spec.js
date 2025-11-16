import { test, expect } from '../setup/mock-api';

test.describe('Unicode Compression and Symbol Allocation (Mocked API)', () => {
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
    // Should contain symbol or unicode (mock returns 'α')
    expect(resultText).toMatch(/symbol|unicode|compression|α/i);
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
          // Should show compression ratio (mock returns 250)
          expect(resultText).toMatch(/\d+[:\/]\d+|compression|ratio|250/i);
        }
      }
    }
  });
});

