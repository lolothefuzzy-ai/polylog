import { test, expect } from '@playwright/test';

test.describe('Visual: Basic Rendering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 10000 });
  });

  test('App loads and renders correctly', async ({ page }) => {
    // Check main app container
    const app = page.locator('.app-layout');
    await expect(app).toBeVisible();
    
    // Check sidebar
    const sidebar = page.locator('.app-sidebar-left');
    await expect(sidebar).toBeVisible();
    
    // Check main canvas area
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Check right sidebar
    const rightSidebar = page.locator('.app-sidebar-right');
    await expect(rightSidebar).toBeVisible();
  });

  test('Polyhedra library renders', async ({ page }) => {
    const library = page.locator('.polyhedra-library');
    await expect(library).toBeVisible();
    
    // Library should have title
    const title = library.locator('h3');
    await expect(title).toContainText('Polyhedra Library');
  });

  test('3D canvas renders', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Canvas should have content (not blank)
    const canvasBox = await canvas.boundingBox();
    expect(canvasBox).not.toBeNull();
    expect(canvasBox.width).toBeGreaterThan(0);
    expect(canvasBox.height).toBeGreaterThan(0);
  });

  test('Attachment validator appears when two polyhedra selected', async ({ page }) => {
    // Select first polyhedron
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(500);
    
    // Select second polyhedron
    await page.click('.library-item:nth-child(2)');
    await page.waitForTimeout(500);
    
    // Attachment validator should appear
    const validator = page.locator('.attachment-validator');
    await expect(validator).toBeVisible({ timeout: 5000 });
  });

  test('LOD indicator displays', async ({ page }) => {
    const lodIndicator = page.locator('.lod-indicator');
    await expect(lodIndicator).toBeVisible();
    
    // Should show LOD level
    const text = await lodIndicator.textContent();
    expect(text).toMatch(/LOD:/i);
  });
});

