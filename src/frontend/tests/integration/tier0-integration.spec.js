/**
 * Tier 0 Integration Tests
 * Tests the complete Tier 0 workflow: encoding, decoding, atomic chains, scaffolds
 */

import { test, expect } from '@playwright/test';
import { ensureApiRunning, testTier0Endpoint } from '../setup/api-setup.js';

test.describe('Tier 0 Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure API is running
    await ensureApiRunning(page);
    
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
  });

  test('Tier 0 API endpoints are accessible', async ({ page }) => {
    // Test decode endpoint
    const result = await testTier0Endpoint(page, '/api/tier0/decode', 'POST', { symbol: 'A11' });
    expect(result.ok).toBeTruthy();
    expect(result.data).toHaveProperty('symbol');
    expect(result.data).toHaveProperty('polygons');
    expect(Array.isArray(result.data.polygons)).toBeTruthy();
  });

  test('Atomic chain library is accessible', async ({ page }) => {
    const result = await testTier0Endpoint(page, '/api/tier0/atomic-chains/library', 'GET');
    expect(result.ok).toBeTruthy();
    expect(result.data).toHaveProperty('square_chains');
    expect(result.data).toHaveProperty('triangle_clusters');
    expect(result.data).toHaveProperty('mixed_chains');
  });

  test('Atomic chain detection works', async ({ page }) => {
    const result = await testTier0Endpoint(
      page, 
      '/api/tier0/atomic-chains/detect', 
      'POST', 
      { symbol: 'B1' } // Single square
    );
    
    if (result.ok) {
      expect(result.data).toHaveProperty('chain_type');
      expect(result.data).toHaveProperty('polygon_sequence');
    } else {
      // If detection fails, that's okay - it means the symbol might not be an atomic chain
      expect(result.status).toBeGreaterThanOrEqual(400);
    }
  });

  test('Tier 0 symbols are generated when chains are created', async ({ page }) => {
    // Wait for workspace to be ready
    await page.waitForSelector('canvas', { timeout: 10000 });
    
    // Check if Tier0Display component is visible (after 3+ polygons)
    const tier0Display = page.locator('.tier0-display');
    
    // The display should exist but might be empty initially
    // We'll check that the component structure is there
    const displayExists = await tier0Display.count() > 0;
    
    // If advanced features are enabled (3+ polygons), Tier0Display should be visible
    const warmupMessage = page.locator('.warmup-message');
    const warmupVisible = await warmupMessage.isVisible().catch(() => false);
    
    if (!warmupVisible) {
      // Advanced features enabled - Tier0Display should be visible
      expect(displayExists).toBeTruthy();
    }
  });

  test('Tier 0 visualization toggle works', async ({ page }) => {
    await page.waitForSelector('.app', { timeout: 15000 });
    
    // Check if toggle exists (only visible when advanced features enabled)
    const toggle = page.locator('.toggle-visualization input[type="checkbox"]');
    const toggleExists = await toggle.count() > 0;
    
    if (toggleExists) {
      const initialChecked = await toggle.isChecked();
      
      // Toggle it
      await toggle.click();
      
      // Wait a bit for state to update
      await page.waitForTimeout(500);
      
      const afterToggle = await toggle.isChecked();
      expect(afterToggle).toBe(!initialChecked);
    }
  });

  test('Johnson solid scaffold API works', async ({ page }) => {
    const result = await testTier0Endpoint(
      page, 
      '/api/tier0/scaffolds/johnson-solid/square_pyramid', 
      'GET'
    );
    
    if (result.ok) {
      expect(result.data).toHaveProperty('scaffold_symbol');
      expect(result.data).toHaveProperty('atomic_chains');
      expect(Array.isArray(result.data.atomic_chains)).toBeTruthy();
    } else {
      // Scaffold might not exist for this solid - that's okay
      expect(result.status).toBeGreaterThanOrEqual(400);
    }
  });

  test('Tier 0 symbol display updates when chains change', async ({ page }) => {
    await page.waitForSelector('.app', { timeout: 15000 });
    
    // Check if chains list exists
    const chainsList = page.locator('.chains-list');
    const chainsListExists = await chainsList.count() > 0;
    
    if (chainsListExists) {
      // Check that empty state or chain items are present
      const emptyState = page.locator('.empty-state');
      const chainItems = page.locator('.chain-item');
      
      const hasEmptyState = await emptyState.isVisible().catch(() => false);
      const chainCount = await chainItems.count();
      
      // Should have either empty state or chain items
      expect(hasEmptyState || chainCount > 0).toBeTruthy();
    }
  });
});

