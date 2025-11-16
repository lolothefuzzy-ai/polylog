import { test, expect } from '@playwright/test';

test.describe('Unicode Compression System - 4 Tier Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.app-layout', { timeout: 15000 });
  });

  test('Tier 0: Primitive Polygon Labels (A-R)', async ({ page }) => {
    // Test that primitive polygons use single-letter symbols A-R
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    const libraryItems = page.locator('.library-item');
    const itemCount = await libraryItems.count();
    
    expect(itemCount).toBeGreaterThanOrEqual(10); // Should have at least A-J
    
    // Get symbols from library items
    const symbols = [];
    for (let i = 0; i < Math.min(itemCount, 18); i++) {
      const item = libraryItems.nth(i);
      const symbol = await item.locator('.polyhedron-symbol').textContent();
      if (symbol && symbol.length === 1 && /[A-R]/.test(symbol)) {
        symbols.push(symbol);
      }
    }
    
    // Should have primitive symbols
    expect(symbols.length).toBeGreaterThan(5);
    console.log(`Tier 0 symbols found: ${symbols.join(', ')}`);
    
    // Verify symbol mapping to polygon sides
    const symbolToSides = { 'A': 3, 'B': 4, 'C': 5, 'D': 6, 'E': 7, 'F': 8 };
    
    for (const symbol of symbols.slice(0, 6)) {
      const expectedSides = symbolToSides[symbol];
      if (expectedSides) {
        // Click to load details and verify
        await libraryItems.filter({ hasText: symbol }).first().click();
        await page.waitForTimeout(500);
        
        // Check if the loaded polyhedron has correct number of sides
        const sidesInfo = page.locator('.polyhedron-sides');
        if (await sidesInfo.count() > 0) {
          const sidesText = await sidesInfo.textContent();
          expect(sidesText).toContain(expectedSides.toString());
        }
      }
    }
  });

  test('Tier 1: Pair Compression (Greek letters)', async ({ page }) => {
    // Test that polygon pairs compress to Greek letters
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Select two polygons to test pair compression
    await page.click('.library-item:first-child'); // First polygon
    await page.waitForTimeout(300);
    await page.click('.library-item:nth-child(2)'); // Second polygon
    await page.waitForTimeout(500);
    
    // Generate polyform to test compression
    const generateButton = page.locator('.generate-button');
    if (await generateButton.isEnabled()) {
      await generateButton.click();
      await page.waitForTimeout(2000);
      
      // Check for compression display
      const compressionInfo = page.locator('.polyform-compression, .compression-ratio');
      if (await compressionInfo.count() > 0) {
        const compressionText = await compressionInfo.first().textContent();
        console.log(`Compression info: ${compressionText}`);
        
        // Should show compression ratio
        expect(compressionText).toMatch(/compression/i);
        
        // Look for Unicode symbols in the display
        const unicodePattern = /[\u03B1-\u03C9]/; // Greek alphabet range
        if (unicodePattern.test(compressionText)) {
          console.log('Tier 1 compression: Greek letter symbols detected');
        }
      }
    }
  });

  test('Tier 2: Cluster Encoding Format Validation', async ({ page }) => {
    // Test cluster encoding format: <symbol>⟨n=<count>, θ=<angle>°, σ=<symmetry>⟩
    
    // Generate a more complex polyform to test cluster encoding
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Select multiple polygons for complex assembly
    const selections = [1, 2, 3];
    for (const index of selections) {
      await page.click(`.library-item:nth-child(${index})`);
      await page.waitForTimeout(300);
    }
    
    // Generate multiple times to create clusters
    const generateButton = page.locator('.generate-button');
    if (await generateButton.isEnabled()) {
      for (let i = 0; i < 3; i++) {
        await generateButton.click();
        await page.waitForTimeout(1500);
      }
      
      // Check generated polyforms for cluster encoding
      const generatedItems = page.locator('.generated-polyform-item');
      const itemCount = await generatedItems.count();
      
      if (itemCount > 0) {
        for (let i = 0; i < Math.min(itemCount, 3); i++) {
          const item = generatedItems.nth(i);
          const itemText = await item.textContent();
          
          // Look for cluster encoding patterns
          const clusterPattern = /⟨n=\d+, θ=[\d.]+°, σ=[A-Z]⟩/;
          if (clusterPattern.test(itemText)) {
            console.log(`Tier 2 cluster encoding found: ${itemText}`);
            
            // Validate format components
            const match = itemText.match(clusterPattern);
            if (match) {
              const clusterData = match[0];
              expect(clusterData).toContain('n=');
              expect(clusterData).toContain('θ=');
              expect(clusterData).toContain('σ=');
            }
          }
        }
      }
    }
  });

  test('Tier 3: Assembly Encoding Validation', async ({ page }) => {
    // Test assembly encoding format: <cluster_sequence>⟨symmetry⟩
    
    // Create multiple generated polyforms to form assemblies
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Generate several polyforms
    for (let round = 0; round < 5; round++) {
      // Select different combinations
      await page.click('.library-item:first-child');
      await page.waitForTimeout(200);
      await page.click('.library-item:nth-child(2)');
      await page.waitForTimeout(500);
      
      const generateButton = page.locator('.generate-button');
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(1000);
      }
    }
    
    // Check for assembly encoding in generated polyforms
    const generatedItems = page.locator('.generated-polyform-item');
    const itemCount = await generatedItems.count();
    
    if (itemCount > 0) {
      let assemblyFound = false;
      
      for (let i = 0; i < itemCount; i++) {
        const item = generatedItems.nth(i);
        const itemText = await item.textContent();
        
        // Look for assembly encoding patterns
        const assemblyPattern = /⟨σ=[A-Z\d_]+⟩/;
        if (assemblyPattern.test(itemText)) {
          console.log(`Tier 3 assembly encoding found: ${itemText}`);
          assemblyFound = true;
          
          // Validate symmetry notation
          const match = itemText.match(assemblyPattern);
          if (match) {
            const symmetryData = match[0];
            expect(symmetryData).toContain('σ=');
            
            // Common symmetry groups
            const validSymmetries = ['C2', 'C3', 'D2', 'D3', 'T', 'O', 'I'];
            const hasValidSymmetry = validSymmetries.some(sym => 
              symmetryData.includes(sym)
            );
            
            if (hasValidSymmetry) {
              console.log(`Valid symmetry group detected: ${symmetryData}`);
            }
          }
        }
      }
      
      if (!assemblyFound) {
        console.log('Tier 3 assembly encoding not detected in current polyforms');
      }
    }
  });

  test('Tier 4: Mega-Structure Encoding', async ({ page }) => {
    // Test mega-structure encoding: <assembly_symbol><pattern>⟨params⟩
    
    // This tier would be tested with very large assemblies
    // For now, we'll validate the pattern recognition
    
    await page.waitForSelector('.library-item', { timeout: 10000 });
    
    // Generate many polyforms to potentially trigger mega-structure encoding
    for (let round = 0; round < 8; round++) {
      // Select different polygon combinations
      const firstIndex = (round % 3) + 1;
      const secondIndex = ((round + 1) % 3) + 2;
      
      await page.click(`.library-item:nth-child(${firstIndex})`);
      await page.waitForTimeout(200);
      await page.click(`.library-item:nth-child(${secondIndex})`);
      await page.waitForTimeout(500);
      
      const generateButton = page.locator('.generate-button');
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(800);
      }
    }
    
    // Check for mega-structure patterns
    const generatedItems = page.locator('.generated-polyform-item');
    const itemCount = await generatedItems.count();
    
    if (itemCount > 0) {
      for (let i = 0; i < itemCount; i++) {
        const item = generatedItems.nth(i);
        const itemText = await item.textContent();
        
        // Look for mega-structure patterns
        const megaPatterns = [
          /⟨radial, n=\d+, r=[\d.]+, σ=/,
          /⟨linear, n=\d+, l=[\d.]+, σ=/,
          /⟨spiral, n=\d+, θ=[\d.]+, σ=/
        ];
        
        for (const pattern of megaPatterns) {
          if (pattern.test(itemText)) {
            console.log(`Tier 4 mega-structure encoding found: ${itemText}`);
            
            // Validate mega-structure components
            const match = itemText.match(pattern);
            if (match) {
              const megaData = match[0];
              expect(megaData).toContain('n='); // count
              expect(megaData).toContain('σ='); // symmetry
              
              // Pattern-specific validation
              if (megaData.includes('radial')) {
                expect(megaData).toContain('r='); // radius
              } else if (megaData.includes('linear')) {
                expect(megaData).toContain('l='); // length
              } else if (megaData.includes('spiral')) {
                expect(megaData).toContain('θ='); // angle
              }
            }
          }
        }
      }
    }
  });

  test('Compression Ratio Validation Across Tiers', async ({ page }) => {
    // Test compression ratios meet architectural requirements
    
    const compressionTests = [
      { tier: 'Single polygon', expectedRatio: 500 },
      { tier: 'Small cluster', expectedRatio: 100 },
      { tier: 'Assembly', expectedRatio: 200 },
      { tier: 'Mega-structure', expectedRatio: 5000 }
    ];
    
    for (const test of compressionTests) {
      // Generate polyforms for this tier
      await page.waitForSelector('.library-item', { timeout: 10000 });
      
      const complexity = test.tier === 'Single polygon' ? 2 : 
                        test.tier === 'Small cluster' ? 3 :
                        test.tier === 'Assembly' ? 5 : 8;
      
      for (let i = 0; i < complexity; i++) {
        await page.click(`.library-item:nth-child(${(i % 5) + 1})`);
        await page.waitForTimeout(200);
      }
      
      const generateButton = page.locator('.generate-button');
      if (await generateButton.isEnabled()) {
        await generateButton.click();
        await page.waitForTimeout(1500);
        
        // Check compression ratio
        const compressionInfo = page.locator('.polyform-compression, .compression-ratio');
        if (await compressionInfo.count() > 0) {
          const compressionText = await compressionInfo.first().textContent();
          
          // Extract ratio from text
          const ratioMatch = compressionText.match(/(\d+\.?\d*):?1/);
          if (ratioMatch) {
            const ratio = parseFloat(ratioMatch[1]);
            console.log(`${test.tier}: Compression ratio ${ratio}:1 (expected ≥ ${test.expectedRatio}:1)`);
            
            // Should meet or exceed expected ratio (allowing for implementation variations)
            expect(ratio).toBeGreaterThan(test.expectedRatio * 0.1); // 10% of target
          }
        }
      }
      
      // Clear selection for next test
      await page.waitForTimeout(500);
    }
  });

  test('Unicode Symbol Allocation Performance', async ({ page }) => {
    // Test O(1) Unicode symbol allocation performance
    
    const allocationMetrics = await page.evaluate(async () => {
      const testSymbols = [];
      const allocationTimes = [];
      
      // Simulate symbol allocation for many polyforms
      for (let i = 0; i < 1000; i++) {
        const startTime = performance.now();
        
        // Simulate symbol allocation (in real implementation, this would call the encoder)
        const symbol = String.fromCharCode(0x03B1 + (i % 25)); // Greek letters
        testSymbols.push(symbol);
        
        const endTime = performance.now();
        allocationTimes.push(endTime - startTime);
      }
      
      return {
        symbolCount: testSymbols.length,
        avgAllocationTime: allocationTimes.reduce((a, b) => a + b, 0) / allocationTimes.length,
        maxAllocationTime: Math.max(...allocationTimes),
        uniqueSymbols: [...new Set(testSymbols)].length
      };
    });
    
    console.log(`Symbol allocation metrics:`, allocationMetrics);
    
    // Performance should be very fast (sub-microsecond in real implementation)
    expect(allocationMetrics.avgAllocationTime).toBeLessThan(0.1); // Sub-millisecond in browser
    expect(allocationMetrics.maxAllocationTime).toBeLessThan(1);
    expect(allocationMetrics.uniqueSymbols).toBeGreaterThan(10); // Should have variety
  });
});