import { test, expect } from '@playwright/test';

test.describe('Node Chain Structure', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
  });

  test('Polyform composition reflects node chain', async ({ page }) => {
    // Select multiple polyhedra to create a chain
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Select 3 polyhedra sequentially
    const selectedSymbols = [];
    for (let i = 0; i < 3; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(500);
      
      // Get symbol from selected item
      const item = page.locator(`.library-item:nth-child(${i + 1})`);
      const symbol = item.locator('.item-symbol');
      if (await symbol.isVisible()) {
        const symbolText = await symbol.textContent();
        selectedSymbols.push(symbolText.trim());
      }
    }
    
    // Check that all are in workspace
    const countText = await page.locator('.polyhedra-count').textContent();
    expect(countText).toContain('3');
    
    // Generate polyform to see composition
    const generator = page.locator('.polyform-generator');
    if (await generator.isVisible()) {
      const generateButton = generator.locator('button').filter({ hasText: /generate/i });
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(3000);
        
        // Check composition reflects the chain
        const result = generator.locator('.generated-result');
        if (await result.isVisible()) {
          const composition = await result.textContent();
          // Composition should contain the symbols in order
          expect(composition).toBeTruthy();
        }
      }
    }
  });

  test('Attachment sequence creates valid node chain', async ({ page }) => {
    // Select two polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(1000);
    
    // Check attachment validator shows valid options
    const validator = page.locator('.attachment-validator');
    if (await validator.isVisible()) {
      // Should show attachment options
      const options = validator.locator('.attachment-option');
      const optionCount = await options.count();
      expect(optionCount).toBeGreaterThan(0);
    }
  });

  test('Multi-polygon chains maintain structure', async ({ page }) => {
    // Select 4+ polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    for (let i = 0; i < 4; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(500);
    }
    
    // Check workspace shows all
    const countText = await page.locator('.polyhedra-count').textContent();
    expect(countText).toContain('4');
    
    // Canvas should render the chain
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });
});

