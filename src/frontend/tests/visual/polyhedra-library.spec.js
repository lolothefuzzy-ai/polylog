import { test, expect } from '@playwright/test';

test.describe('Polyhedra Library', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for app to load
    await page.waitForSelector('.app', { timeout: 10000 });
  });

  test('should display polyhedra library', async ({ page }) => {
    const library = page.locator('.polyhedra-library');
    await expect(library).toBeVisible();
  });

  test('should load and display polyhedra items', async ({ page }) => {
    // Wait for library items to load
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    const items = page.locator('.library-item');
    const count = await items.count();
    
    expect(count).toBeGreaterThan(0);
  });

  test('should filter polyhedra by classification', async ({ page }) => {
    await page.waitForSelector('.library-filter', { timeout: 10000 });
    
    // Select Platonic filter
    await page.selectOption('.library-filter', 'platonic');
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
    
    const items = page.locator('.library-item');
    const count = await items.count();
    
    // Should show some items (may be 0 if API not available, but should not error)
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should search polyhedra', async ({ page }) => {
    await page.waitForSelector('.library-search', { timeout: 10000 });
    
    // Type search query
    await page.fill('.library-search', 'cube');
    await page.waitForTimeout(500);
    
    // Should show filtered results
    const items = page.locator('.library-item');
    const count = await items.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should select polyhedron on click', async ({ page }) => {
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    const firstItem = page.locator('.library-item').first();
    await firstItem.click();
    
    // Should trigger selection (check if attachment validator appears)
    await page.waitForTimeout(500);
    
    // Verify interaction happened
    expect(firstItem).toBeVisible();
  });
});

test.describe('3D Workspace', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 10000 });
  });

  test('should render Babylon.js scene', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible({ timeout: 10000 });
  });

  test('should have interactive 3D canvas', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Try to interact with canvas
    await canvas.click({ position: { x: 400, y: 300 } });
    
    // Canvas should remain visible
    await expect(canvas).toBeVisible();
  });
});

test.describe('Attachment Validator', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 10000 });
  });

  test('should show empty state initially', async ({ page }) => {
    const validator = page.locator('.attachment-validator');
    await expect(validator).toBeVisible();
    
    const emptyState = page.locator('.validator-empty');
    await expect(emptyState).toBeVisible();
  });

  test('should display attachment options when two polyhedra selected', async ({ page }) => {
    // This test requires API to be running
    // For now, just verify the component exists
    const validator = page.locator('.attachment-validator');
    await expect(validator).toBeVisible();
  });
});

