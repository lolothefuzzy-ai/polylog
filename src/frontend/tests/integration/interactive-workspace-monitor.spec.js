/**
 * Interactive Workspace Monitor Test
 * Monitors user interactions in the browser workspace and analyzes behavior
 * This test runs continuously and monitors:
 * - Polygon placement
 * - Polygon movement
 * - Polygon rotation
 * - Edge snapping
 * - Chain formation
 * - Tier 0 symbol generation
 * - API calls
 * - Console errors
 */

import { test, expect } from '@playwright/test';
import { ensureApiRunning, testTier0Endpoint } from '../setup/api-setup.js';

test.describe('Interactive Workspace Monitor', () => {
  let interactionLog = [];
  let apiCalls = [];
  let consoleErrors = [];
  let tier0SymbolsGenerated = [];
  
  test.beforeEach(async ({ page }) => {
    // Reset logs
    interactionLog = [];
    apiCalls = [];
    consoleErrors = [];
    tier0SymbolsGenerated = [];
    
    // Ensure API is running
    await ensureApiRunning(page);
    
    // Capture console messages
    page.on('console', msg => {
      const text = msg.text();
      const type = msg.type();
      
      if (type === 'error') {
        consoleErrors.push({ text, timestamp: Date.now() });
        console.error(`[BROWSER ERROR] ${text}`);
      }
      
      // Log Tier 0 symbol generation
      if (text.includes('[WorkspaceManager]') && text.includes('Tier 0 symbol')) {
        const match = text.match(/symbol[:\s]+([A-Z]\d+)/);
        if (match) {
          tier0SymbolsGenerated.push({ symbol: match[1], timestamp: Date.now() });
        }
      }
      
      // Log important workspace events
      if (text.includes('[Interaction]') || text.includes('[BabylonScene]') || text.includes('[WorkspaceManager]')) {
        interactionLog.push({ type, text, timestamp: Date.now() });
      }
    });
    
    // Capture API calls
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/')) {
        apiCalls.push({
          method: request.method(),
          url,
          timestamp: Date.now()
        });
      }
    });
    
    // Capture page errors
    page.on('pageerror', error => {
      consoleErrors.push({ text: error.message, timestamp: Date.now() });
      console.error(`[PAGE ERROR] ${error.message}`);
    });
    
    // Navigate to app
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 15000 });
    await page.waitForSelector('canvas', { timeout: 10000 });
    
    console.log('[TEST] Workspace ready for interaction');
  });

  test('Monitor Interactive Workspace Session', async ({ page }) => {
    const testDuration = 300000; // 5 minutes of monitoring
    const startTime = Date.now();
    const checkInterval = 5000; // Check every 5 seconds
    
    console.log('[TEST] Starting interactive workspace monitoring...');
    console.log('[TEST] Monitor will run for 5 minutes');
    console.log('[TEST] Interact with the workspace - place polygons, move them, create chains');
    
    // Monitor workspace state
    const workspaceState = {
      polygonsPlaced: 0,
      polygonsMoved: 0,
      attachmentsCreated: 0,
      chainsFormed: 0,
      tier0SymbolsGenerated: 0,
      errors: 0
    };
    
    // Periodic state check
    const checkState = async () => {
      const elapsed = Date.now() - startTime;
      
      // Count polygons in scene
      const polygonCount = await page.evaluate(() => {
        // Check for polygon count indicator or count meshes
        const countElement = document.querySelector('.polyhedra-count, .polygon-count');
        if (countElement) {
          const text = countElement.textContent;
          const match = text.match(/(\d+)/);
          return match ? parseInt(match[1]) : 0;
        }
        return 0;
      });
      
      workspaceState.polygonsPlaced = polygonCount;
      
      // Count chains
      const chainCount = await page.evaluate(() => {
        const chainElements = document.querySelectorAll('.chain-item, .tier0-chain');
        return chainElements.length;
      });
      
      workspaceState.chainsFormed = chainCount;
      workspaceState.tier0SymbolsGenerated = tier0SymbolsGenerated.length;
      workspaceState.errors = consoleErrors.length;
      
      // Log current state
      console.log(`[MONITOR] State at ${Math.floor(elapsed / 1000)}s:`);
      console.log(`  - Polygons placed: ${workspaceState.polygonsPlaced}`);
      console.log(`  - Chains formed: ${workspaceState.chainsFormed}`);
      console.log(`  - Tier 0 symbols generated: ${workspaceState.tier0SymbolsGenerated}`);
      console.log(`  - API calls: ${apiCalls.length}`);
      console.log(`  - Errors: ${workspaceState.errors}`);
      
      // Check for issues
      if (workspaceState.errors > 0) {
        console.warn(`[MONITOR] ⚠️  ${workspaceState.errors} error(s) detected`);
        consoleErrors.forEach((err, idx) => {
          console.warn(`  Error ${idx + 1}: ${err.text}`);
        });
      }
      
      // Check for Tier 0 symbol generation
      if (workspaceState.polygonsPlaced >= 2 && workspaceState.tier0SymbolsGenerated === 0) {
        console.warn('[MONITOR] ⚠️  Multiple polygons placed but no Tier 0 symbols generated');
      }
      
      // Check API responsiveness
      if (apiCalls.length > 0) {
        const recentApiCalls = apiCalls.filter(call => Date.now() - call.timestamp < 10000);
        console.log(`[MONITOR] Recent API calls (last 10s): ${recentApiCalls.length}`);
      }
    };
    
    // Run periodic checks
    const monitoringInterval = setInterval(async () => {
      if (Date.now() - startTime >= testDuration) {
        clearInterval(monitoringInterval);
        return;
      }
      await checkState();
    }, checkInterval);
    
    // Wait for test duration
    await page.waitForTimeout(testDuration);
    clearInterval(monitoringInterval);
    
    // Final state check
    await checkState();
    
    // Analyze results
    console.log('\n[TEST] === Monitoring Session Complete ===');
    console.log(`[TEST] Duration: ${Math.floor(testDuration / 1000)}s`);
    console.log(`[TEST] Final State:`);
    console.log(`  - Polygons placed: ${workspaceState.polygonsPlaced}`);
    console.log(`  - Chains formed: ${workspaceState.chainsFormed}`);
    console.log(`  - Tier 0 symbols generated: ${workspaceState.tier0SymbolsGenerated}`);
    console.log(`  - Total API calls: ${apiCalls.length}`);
    console.log(`  - Total errors: ${workspaceState.errors}`);
    
    // Test assertions
    expect(workspaceState.errors).toBe(0);
    
    // If polygons were placed, verify Tier 0 generation
    if (workspaceState.polygonsPlaced >= 2) {
      expect(workspaceState.tier0SymbolsGenerated).toBeGreaterThan(0);
    }
    
    // Verify API calls were made
    if (workspaceState.polygonsPlaced > 0) {
      expect(apiCalls.length).toBeGreaterThan(0);
    }
    
    // Log interaction summary
    console.log('\n[TEST] === Interaction Summary ===');
    console.log(`[TEST] Interaction events logged: ${interactionLog.length}`);
    console.log(`[TEST] API calls logged: ${apiCalls.length}`);
    console.log(`[TEST] Tier 0 symbols: ${tier0SymbolsGenerated.map(s => s.symbol).join(', ')}`);
  });

  test('Analyze Workspace Interactions', async ({ page }) => {
    // This test analyzes the workspace state after interactions
    console.log('[TEST] Analyzing workspace interactions...');
    
    // Wait a bit for any initial interactions
    await page.waitForTimeout(2000);
    
    // Check workspace state
    const workspaceAnalysis = await page.evaluate(() => {
      const analysis = {
        polygonsInScene: 0,
        chainsDetected: 0,
        tier0DisplayVisible: false,
        visualizationEnabled: false,
        errors: []
      };
      
      // Count polygons
      const countElement = document.querySelector('.polyhedra-count, .polygon-count');
      if (countElement) {
        const text = countElement.textContent;
        const match = text.match(/(\d+)/);
        analysis.polygonsInScene = match ? parseInt(match[1]) : 0;
      }
      
      // Check Tier 0 display
      const tier0Display = document.querySelector('.tier0-display');
      analysis.tier0DisplayVisible = tier0Display !== null && tier0Display.offsetParent !== null;
      
      // Check visualization toggle
      const toggle = document.querySelector('.toggle-visualization input[type="checkbox"]');
      analysis.visualizationEnabled = toggle ? toggle.checked : false;
      
      // Check for chains
      const chainItems = document.querySelectorAll('.chain-item, .tier0-chain');
      analysis.chainsDetected = chainItems.length;
      
      return analysis;
    });
    
    console.log('[TEST] Workspace Analysis:');
    console.log(`  - Polygons in scene: ${workspaceAnalysis.polygonsInScene}`);
    console.log(`  - Chains detected: ${workspaceAnalysis.chainsDetected}`);
    console.log(`  - Tier 0 display visible: ${workspaceAnalysis.tier0DisplayVisible}`);
    console.log(`  - Visualization enabled: ${workspaceAnalysis.visualizationEnabled}`);
    
    // Verify workspace is functional
    expect(workspaceAnalysis.errors.length).toBe(0);
    
    // If polygons exist, Tier 0 display should be visible (after 3+ polygons)
    if (workspaceAnalysis.polygonsInScene >= 3) {
      expect(workspaceAnalysis.tier0DisplayVisible).toBeTruthy();
    }
  });
});

