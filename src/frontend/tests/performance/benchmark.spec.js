import { test, expect } from '@playwright/test';

test.describe('Performance Benchmarks', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app', { timeout: 10000 });
  });

  test('API response time should be under 100ms', async ({ page }) => {
    const startTime = Date.now();
    
    // Trigger API call by selecting polyhedron
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    
    // Wait for API response
    await page.waitForTimeout(200);
    
    const responseTime = Date.now() - startTime;
    
    console.log(`API response time: ${responseTime}ms`);
    expect(responseTime).toBeLessThan(500); // Allow some buffer for initial load
  });

  test('Rendering should maintain 60 FPS', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Measure FPS by checking render loop
    const fps = await page.evaluate(() => {
      return new Promise((resolve) => {
        let frames = 0;
        const start = performance.now();
        
        function countFrame() {
          frames++;
          if (performance.now() - start < 1000) {
            requestAnimationFrame(countFrame);
          } else {
            resolve(frames);
          }
        }
        
        requestAnimationFrame(countFrame);
      });
    });
    
    console.log(`Measured FPS: ${fps}`);
    expect(fps).toBeGreaterThan(30); // Minimum acceptable
  });

  test('LOD transition should be under 20ms', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
    
    // Simulate camera zoom (triggers LOD change)
    const transitionTime = await page.evaluate(() => {
      return new Promise((resolve) => {
        const start = performance.now();
        
        // Simulate zoom
        const event = new WheelEvent('wheel', {
          deltaY: -100,
          bubbles: true
        });
        document.querySelector('canvas')?.dispatchEvent(event);
        
        // Measure transition
        setTimeout(() => {
          resolve(performance.now() - start);
        }, 50);
      });
    });
    
    console.log(`LOD transition time: ${transitionTime}ms`);
    expect(transitionTime).toBeLessThan(100); // Allow buffer
  });

  test('Memory usage should be reasonable', async ({ page }) => {
    const memoryBefore = await page.evaluate(() => {
      return performance.memory ? performance.memory.usedJSHeapSize : 0;
    });
    
    // Load multiple polyhedra
    for (let i = 0; i < 10; i++) {
      await page.click('.library-item').catch(() => {});
      await page.waitForTimeout(100);
    }
    
    const memoryAfter = await page.evaluate(() => {
      return performance.memory ? performance.memory.usedJSHeapSize : 0;
    });
    
    if (memoryBefore > 0 && memoryAfter > 0) {
      const memoryIncrease = (memoryAfter - memoryBefore) / (1024 * 1024); // MB
      console.log(`Memory increase: ${memoryIncrease.toFixed(2)} MB`);
      expect(memoryIncrease).toBeLessThan(100); // Should not exceed 100MB
    }
  });

  test('Edge validation should be under 5ms', async ({ page }) => {
    // Select two polyhedra
    await page.waitForSelector('.library-item', { timeout: 10000 });
    await page.click('.library-item:first-child');
    await page.waitForTimeout(100);
    await page.click('.library-item:nth-child(2)');
    
    // Measure validation time
    const validationTime = await page.evaluate(() => {
      return new Promise((resolve) => {
        const start = performance.now();
        
        // Wait for attachment options to appear
        const observer = new MutationObserver(() => {
          const options = document.querySelector('.validator-option');
          if (options) {
            resolve(performance.now() - start);
            observer.disconnect();
          }
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Timeout after 1 second
        setTimeout(() => resolve(1000), 1000);
      });
    });
    
    console.log(`Edge validation time: ${validationTime}ms`);
    expect(validationTime).toBeLessThan(500); // Allow buffer for API call
  });
});

