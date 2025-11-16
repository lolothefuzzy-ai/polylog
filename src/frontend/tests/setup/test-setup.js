/**
 * Test Setup
 * Global test configuration and utilities
 */

import { test as base } from '@playwright/test';

// Check if servers are running
async function checkServers() {
  try {
    const apiResponse = await fetch('http://localhost:8000/health');
    const frontendResponse = await fetch('http://localhost:5173');
    
    return {
      api: apiResponse.ok,
      frontend: frontendResponse.ok
    };
  } catch (error) {
    return {
      api: false,
      frontend: false,
      error: error.message
    };
  }
}

// Wait for servers to be ready
export async function waitForServers(page, timeout = 30000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      const apiResponse = await page.request.get('http://localhost:8000/health');
      const frontendResponse = await page.request.get('http://localhost:5173');
      
      if (apiResponse.ok() && frontendResponse.ok()) {
        return true;
      }
    } catch (error) {
      // Servers not ready yet
    }
    
    await page.waitForTimeout(1000); // Wait 1 second before retry
  }
  
  throw new Error('Servers did not become ready within timeout');
}

// Enhanced test with server checks
export const test = base.extend({
  page: async ({ page }, use) => {
    // Wait for servers before running tests
    await waitForServers(page);
    
    // Navigate to app
    await page.goto('/');
    
    // Wait for app to load
    await page.waitForSelector('.app', { timeout: 15000 });
    
    await use(page);
  }
});

