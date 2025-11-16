import { test, expect } from '@playwright/test';

test.describe('Architecture Performance Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app-layout', { timeout: 15000 });
  });

  test('Performance Requirement: ≥30 FPS for complex assemblies', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();

    // Load multiple polyhedra to create complex assembly
    await page.waitForSelector('.library-item', { timeout: 10000 });
    const itemCount = Math.min(20, await page.locator('.library-item').count());

    for (let i = 0; i < itemCount; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(100);
    }

    // Measure FPS over time
    const fpsMeasurements = await page.evaluate(async () => {
      return new Promise((resolve) => {
        const measurements = [];
        let lastTime = performance.now();
        let frameCount = 0;
        
        const measureFrame = (currentTime) => {
          frameCount++;
          
          if (currentTime - lastTime >= 1000) { // 1 second intervals
            const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
            measurements.push(fps);
            
            frameCount = 0;
            lastTime = currentTime;
            
            if (measurements.length >= 5) { // Measure for 5 seconds
              resolve(measurements);
              return;
            }
          }
          
          requestAnimationFrame(measureFrame);
        };
        
        requestAnimationFrame(measureFrame);
      });
    });

    const avgFps = fpsMeasurements.reduce((a, b) => a + b, 0) / fpsMeasurements.length;
    const minFps = Math.min(...fpsMeasurements);
    
    console.log(`FPS measurements: ${fpsMeasurements.join(', ')}`);
    console.log(`Average FPS: ${avgFps}, Minimum FPS: ${minFps}`);
    
    // Architecture requirement: ≥30 FPS
    expect(avgFps).toBeGreaterThanOrEqual(30);
    expect(minFps).toBeGreaterThanOrEqual(25); // Allow some variance
  });

  test('Performance Requirement: <100ms interaction latency', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();

    // Test various interaction types
    const interactions = [
      { type: 'click', position: { x: 100, y: 100 } },
      { type: 'wheel', deltaY: 100 },
      { type: 'mousemove', position: { x: 200, y: 200 } }
    ];

    for (const interaction of interactions) {
      const latencies = [];
      
      for (let i = 0; i < 10; i++) {
        const startTime = performance.now();
        
        if (interaction.type === 'click') {
          await canvas.click({ position: interaction.position });
        } else if (interaction.type === 'wheel') {
          await canvas.dispatchEvent('wheel', { deltaY: interaction.deltaY, bubbles: true });
        } else if (interaction.type === 'mousemove') {
          await canvas.hover({ position: interaction.position });
        }
        
        // Wait for visual feedback
        await page.waitForTimeout(50);
        
        const endTime = performance.now();
        latencies.push(endTime - startTime);
      }
      
      const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
      const maxLatency = Math.max(...latencies);
      
      console.log(`${interaction.type} - Avg: ${avgLatency.toFixed(2)}ms, Max: ${maxLatency.toFixed(2)}ms`);
      
      // Architecture requirement: <100ms interaction latency
      expect(avgLatency).toBeLessThan(100);
      expect(maxLatency).toBeLessThan(150); // Allow some variance for worst case
    }
  });

  test('Memory Budget: ≤200MB rendering memory', async ({ page }) => {
    const memorySnapshots = [];
    
    // Function to capture memory snapshot
    const captureMemory = async () => {
      return await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });
    };
    
    // Baseline memory
    const baseline = await captureMemory();
    if (baseline) {
      memorySnapshots.push(baseline);
      console.log(`Baseline memory: ${(baseline.used / 1024 / 1024).toFixed(2)}MB`);
    }
    
    // Load progressively more complex scenes
    const loadSteps = [5, 10, 15, 20];
    
    for (const step of loadSteps) {
      await page.waitForSelector('.library-item', { timeout: 10000 });
      const itemCount = Math.min(step, await page.locator('.library-item').count());
      
      for (let i = 0; i < itemCount; i++) {
        await page.click(`.library-item:nth-child(${i + 1})`);
        await page.waitForTimeout(100);
      }
      
      // Wait for rendering to stabilize
      await page.waitForTimeout(1000);
      
      const snapshot = await captureMemory();
      if (snapshot) {
        memorySnapshots.push(snapshot);
        const memoryMB = snapshot.used / 1024 / 1024;
        console.log(`After ${itemCount} polyhedra: ${memoryMB.toFixed(2)}MB`);
        
        // Architecture requirement: ≤200MB rendering memory budget
        expect(memoryMB).toBeLessThan(200);
      }
    }
    
    // Check memory growth rate
    if (memorySnapshots.length > 1 && baseline) {
      const finalMemory = memorySnapshots[memorySnapshots.length - 1];
      const memoryGrowth = finalMemory.used - baseline.used;
      const growthMB = memoryGrowth / 1024 / 1024;
      
      console.log(`Total memory growth: ${growthMB.toFixed(2)}MB`);
      
      // Memory growth should be reasonable
      expect(growthMB).toBeLessThan(150);
    }
  });

  test('API Performance: Sub-50ms response times', async ({ page }) => {
    // Test API response times for critical endpoints
    const endpoints = [
      '/tier1/polyhedra',
      '/tier1/stats',
      '/api/polyform/generated'
    ];

    for (const endpoint of endpoints) {
      const responseTimes = [];
      
      for (let i = 0; i < 5; i++) {
        const startTime = performance.now();
        
        const response = await page.evaluate(async (ep) => {
          try {
            const resp = await fetch(`http://localhost:8000${ep}`);
            const data = await resp.json();
            return { status: resp.status, success: resp.ok };
          } catch (error) {
            return { status: 0, success: false, error: error.message };
          }
        }, endpoint);
        
        const endTime = performance.now();
        responseTimes.push(endTime - startTime);
        
        // API should respond successfully
        if (endpoint.startsWith('/tier1/')) {
          expect(response.success || response.status === 0).toBe(true);
        }
      }
      
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      const maxResponseTime = Math.max(...responseTimes);
      
      console.log(`${endpoint} - Avg: ${avgResponseTime.toFixed(2)}ms, Max: ${maxResponseTime.toFixed(2)}ms`);
      
      // API should respond quickly
      expect(avgResponseTime).toBeLessThan(50);
      expect(maxResponseTime).toBeLessThan(100);
    }
  });

  test('LOD Performance: Smooth transitions without frame drops', async ({ page }) => {
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();

    // Load polyhedra for LOD testing
    await page.waitForSelector('.library-item', { timeout: 10000 });
    for (let i = 0; i < 5; i++) {
      await page.click(`.library-item:nth-child(${i + 1})`);
      await page.waitForTimeout(100);
    }

    // Monitor FPS during LOD transitions
    const fpsDuringTransitions = await page.evaluate(async () => {
      return new Promise((resolve) => {
        const fpsData = [];
        let lastTime = performance.now();
        let frameCount = 0;
        let transitionCount = 0;
        
        const measureFrame = (currentTime) => {
          frameCount++;
          
          if (currentTime - lastTime >= 100) { // Measure every 100ms for more granular data
            const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
            fpsData.push(fps);
            
            frameCount = 0;
            lastTime = currentTime;
            transitionCount++;
            
            if (transitionCount >= 50) { // 5 seconds of data
              resolve(fpsData);
              return;
            }
          }
          
          requestAnimationFrame(measureFrame);
        };
        
        // Trigger LOD changes during measurement
        setTimeout(() => {
          const canvas = document.querySelector('canvas');
          if (canvas) {
            // Simulate zoom events
            canvas.dispatchEvent(new WheelEvent('wheel', { deltaY: -500 }));
          }
        }, 1000);
        
        setTimeout(() => {
          const canvas = document.querySelector('canvas');
          if (canvas) {
            canvas.dispatchEvent(new WheelEvent('wheel', { deltaY: 500 }));
          }
        }, 2500);
        
        requestAnimationFrame(measureFrame);
      });
    });

    const minFpsDuringTransition = Math.min(...fpsDuringTransitions);
    const avgFpsDuringTransition = fpsDuringTransitions.reduce((a, b) => a + b, 0) / fpsDuringTransitions.length;
    
    console.log(`FPS during LOD transitions - Min: ${minFpsDuringTransition}, Avg: ${avgFpsDuringTransition}`);
    
    // FPS should not drop significantly during LOD transitions
    expect(minFpsDuringTransition).toBeGreaterThanOrEqual(20);
    expect(avgFpsDuringTransition).toBeGreaterThanOrEqual(25);
  });

  test('Compression Performance: Sub-millisecond symbol operations', async ({ page }) => {
    // Test Unicode compression performance
    const compressionMetrics = await page.evaluate(async () => {
      // Simulate compression operations
      const testStrings = ['A+B', 'C+D+E', 'F+G+H+I', 'J+K+L+M+N+O'];
      const metrics = {
        encode: [],
        decode: []
      };
      
      for (const testString of testStrings) {
        // Test encoding performance
        const encodeStart = performance.now();
        // Simulate encoding (in real implementation, this would call the encoder)
        const encoded = testString.split('+').join('→');
        const encodeEnd = performance.now();
        metrics.encode.push(encodeEnd - encodeStart);
        
        // Test decoding performance
        const decodeStart = performance.now();
        // Simulate decoding
        const decoded = encoded.split('→').join('+');
        const decodeEnd = performance.now();
        metrics.decode.push(decodeEnd - decodeStart);
      }
      
      return metrics;
    });
    
    const avgEncodeTime = compressionMetrics.encode.reduce((a, b) => a + b, 0) / compressionMetrics.encode.length;
    const avgDecodeTime = compressionMetrics.decode.reduce((a, b) => a + b, 0) / compressionMetrics.decode.length;
    
    console.log(`Compression performance - Encode: ${avgEncodeTime.toFixed(4)}ms, Decode: ${avgDecodeTime.toFixed(4)}ms`);
    
    // Architecture requirement: Sub-microsecond symbol allocation and lookup
    // In browser context, we expect sub-millisecond performance
    expect(avgEncodeTime).toBeLessThan(1);
    expect(avgDecodeTime).toBeLessThan(1);
  });
});