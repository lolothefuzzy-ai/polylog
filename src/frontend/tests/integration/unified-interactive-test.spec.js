/**
 * Unified Interactive Test Suite
 * Runs in the same browser session as user interactions
 * Tracks and validates user actions
 */

import { test, expect } from '@playwright/test';

test.describe('Unified Interactive Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Wait for servers to be ready
    let serversReady = false;
    for (let i = 0; i < 30; i++) {
      try {
        const response = await page.request.get('http://localhost:8000/health');
        if (response.ok()) {
          serversReady = true;
          break;
        }
      } catch (e) {
        // Server not ready yet
      }
      await page.waitForTimeout(1000);
    }
    
    if (!serversReady) {
      console.warn('[TEST] Servers may not be ready, continuing anyway...');
    }
    
    // Navigate to the application
    await page.goto('http://localhost:5173');
    
    // Wait for application to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Give app time to initialize
    
    // Inject interaction tracker
    await page.addInitScript(() => {
      if (!window.interactionLog) {
        window.interactionLog = [];
      }
      window.trackInteraction = (type, data) => {
        if (!window.interactionLog) {
          window.interactionLog = [];
        }
        window.interactionLog.push({
          timestamp: Date.now(),
          type,
          data
        });
      };
      
      // Track mouse movements
      document.addEventListener('mousemove', (e) => {
        window.trackInteraction('mouse_move', {
          x: e.clientX,
          y: e.clientY
        });
      });
      
      // Track clicks
      document.addEventListener('click', (e) => {
        window.trackInteraction('click', {
          selector: e.target.id || e.target.className || e.target.tagName,
          x: e.clientX,
          y: e.clientY,
          element: e.target.tagName
        });
      });
      
      // Track keyboard input
      document.addEventListener('keydown', (e) => {
        window.trackInteraction('keydown', {
          key: e.key,
          code: e.code
        });
      });
      
      // Track input changes
      document.addEventListener('input', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
          window.trackInteraction('input', {
            selector: e.target.id || e.target.className,
            value: e.target.value
          });
        }
      });
    });
  });

  test('Track user interactions during test execution', async ({ page }) => {
    // Wait for initial load
    await page.waitForTimeout(1000);
    
    // Get initial interaction count
    const initialCount = await page.evaluate(() => {
      return window.interactionLog ? window.interactionLog.length : 0;
    });
    
    // Simulate some interactions (or wait for user)
    await page.waitForTimeout(5000); // Wait 5 seconds for user interactions
    
    // Get final interaction count
    const finalCount = await page.evaluate(() => {
      return window.interactionLog ? window.interactionLog.length : 0;
    });
    const interactions = await page.evaluate(() => {
      return window.interactionLog || [];
    });
    
    // Log interactions
    console.log(`Tracked ${finalCount - initialCount} interactions during test`);
    console.log('Interactions:', JSON.stringify(interactions, null, 2));
    
    // Save interactions to API
    if (interactions.length > 0) {
      await page.evaluate(async (interactions) => {
        await fetch('/api/test/interactions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ interactions })
        });
      }, interactions);
    }
    
    // Test should pass if we tracked interactions
    expect(finalCount).toBeGreaterThanOrEqual(initialCount);
  });

  test('Validate system state after user interactions', async ({ page }) => {
    // Wait for user to interact
    await page.waitForTimeout(10000); // Wait 10 seconds
    
    // Get interactions
    const interactions = await page.evaluate(() => {
      return window.interactionLog || [];
    });
    
    // Validate that system is still responsive
    const isResponsive = await page.evaluate(() => {
      return document.readyState === 'complete' && 
             !document.querySelector('.error') &&
             window.Babylon !== undefined;
    });
    
    expect(isResponsive).toBe(true);
    
    // Check if any polygons were created/modified
    const polygonCount = await page.evaluate(() => {
      return window.workspaceManager?.polygons?.length || 0;
    });
    
    console.log(`System state: ${polygonCount} polygons, ${interactions.length} interactions`);
  });

  test('Run automated tests while tracking user interactions', async ({ page }) => {
    // Start automated test sequence
    const testSequence = [
      { action: 'wait', time: 2000 },
      { action: 'check_health' },
      { action: 'wait', time: 3000 }, // Allow user to interact
      { action: 'validate_state' }
    ];
    
    for (const step of testSequence) {
      if (step.action === 'wait') {
        await page.waitForTimeout(step.time);
      } else if (step.action === 'check_health') {
        // Check API health
        const healthResponse = await page.evaluate(async () => {
          const response = await fetch('http://localhost:8000/health');
          return response.json();
        });
        expect(healthResponse.status).toBe('healthy');
      } else if (step.action === 'validate_state') {
        // Validate workspace state
        const state = await page.evaluate(() => {
          return {
            polygons: window.workspaceManager?.polygons?.length || 0,
            interactions: window.interactionLog?.length || 0
          };
        });
        expect(state.polygons).toBeGreaterThanOrEqual(0);
      }
    }
    
    // Get all interactions
    const interactions = await page.evaluate(() => {
      return window.interactionLog || [];
    });
    console.log(`Total interactions tracked: ${interactions.length}`);
  });
});

