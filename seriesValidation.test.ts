/**
 * Test suite for ABCD Series Optimization
 * Validates that series tables are correctly optimized for stability
 */

import { describe, test, expect } from 'vitest';
import {
  ALL_SERIES,
  getPolygonSides,
  getSeriesFromSides,
  getPrimarySeries,
  generateSingleSymbol,
  generateTwoElementSymbol,
  toSubscript,
  fromSubscript,
} from '../src/core/polygonSymbolsV2';

describe('ABCD Series Tables', () => {
  test('Series A is triangle-first (optimized)', () => {
    expect(getPolygonSides('A', 1)).toBe(3); // Triangle
    expect(getPolygonSides('A', 2)).toBe(5); // Pentagon
    expect(getPolygonSides('A', 3)).toBe(7); // Heptagon
  });

  test('Series B is square-first (optimized)', () => {
    expect(getPolygonSides('B', 1)).toBe(4);  // Square
    expect(getPolygonSides('B', 2)).toBe(6);  // Hexagon
    expect(getPolygonSides('B', 3)).toBe(8);  // Octagon
  });

  test('Series D is square-first, pentagon-second (optimized)', () => {
    expect(getPolygonSides('D', 1)).toBe(4);  // Square
    expect(getPolygonSides('D', 2)).toBe(5);  // Pentagon
    expect(getPolygonSides('D', 3)).toBe(11); // 11-gon
  });

  test('All series have exactly 9 entries', () => {
    expect(ALL_SERIES.A.length).toBe(9);
    expect(ALL_SERIES.B.length).toBe(9);
    expect(ALL_SERIES.C.length).toBe(9);
    expect(ALL_SERIES.D.length).toBe(9);
  });

  test('All edge counts are in valid range (3-20)', () => {
    const allCounts = Object.values(ALL_SERIES).flat();
    allCounts.forEach(count => {
      expect(count).toBeGreaterThanOrEqual(3);
      expect(count).toBeLessThanOrEqual(20);
    });
  });
});

describe('Series Lookup Functions', () => {
  test('getSeriesFromSides finds all matches', () => {
    const triangleMatches = getSeriesFromSides(3);
    expect(triangleMatches.length).toBeGreaterThan(0);
    expect(triangleMatches.some(m => m.series === 'A' && m.subscript === 1)).toBe(true);
  });

  test('getSeriesFromSides returns multiple matches for duplicates', () => {
    const squareMatches = getSeriesFromSides(4);
    expect(squareMatches.length).toBe(2); // Should be in both B and D
    expect(squareMatches.some(m => m.series === 'B')).toBe(true);
    expect(squareMatches.some(m => m.series === 'D')).toBe(true);
  });

  test('getPrimarySeries prioritizes A-series', () => {
    const trianglePrimary = getPrimarySeries(3);
    expect(trianglePrimary?.series).toBe('A'); // A has priority
    expect(trianglePrimary?.subscript).toBe(1);
  });

  test('getPrimarySeries returns null for invalid edge count', () => {
    const invalid = getPrimarySeries(2); // No 2-sided polygon
    expect(invalid).toBeNull();
  });
});

describe('Symbol Generation', () => {
  test('generateSingleSymbol creates correct Unicode', () => {
    expect(generateSingleSymbol('A', 1)).toBe('A₁');
    expect(generateSingleSymbol('D', 5)).toBe('D₅');
    expect(generateSingleSymbol('B', 9)).toBe('B₉');
  });

  test('generateTwoElementSymbol creates correct Unicode', () => {
    expect(generateTwoElementSymbol('A', 'B', 11)).toBe('AB₁₁');
    expect(generateTwoElementSymbol('D', 'C', 45)).toBe('DC₄₅');
  });

  test('generateTwoElementSymbol rejects X0 patterns', () => {
    expect(() => generateTwoElementSymbol('A', 'B', 10)).toThrow();
    expect(() => generateTwoElementSymbol('A', 'B', 20)).toThrow();
    expect(() => generateTwoElementSymbol('A', 'B', 90)).toThrow();
  });

  test('generateTwoElementSymbol rejects out of range', () => {
    expect(() => generateTwoElementSymbol('A', 'B', 9)).toThrow();
    expect(() => generateTwoElementSymbol('A', 'B', 100)).toThrow();
  });
});

describe('Subscript Utilities', () => {
  test('toSubscript converts numbers correctly', () => {
    expect(toSubscript(0)).toBe('₀');
    expect(toSubscript(1)).toBe('₁');
    expect(toSubscript(42)).toBe('₄₂');
    expect(toSubscript(123)).toBe('₁₂₃');
  });

  test('fromSubscript converts back correctly', () => {
    expect(fromSubscript('₀')).toBe(0);
    expect(fromSubscript('₁')).toBe(1);
    expect(fromSubscript('₄₂')).toBe(42);
    expect(fromSubscript('₁₂₃')).toBe(123);
  });

  test('toSubscript and fromSubscript are inverse functions', () => {
    const testNumbers = [0, 1, 5, 42, 123, 999];
    testNumbers.forEach(num => {
      const subscript = toSubscript(num);
      const converted = fromSubscript(subscript);
      expect(converted).toBe(num);
    });
  });
});

describe('Attachment Stability Optimization', () => {
  test('Most stable polygons are in early positions', () => {
    // Triangles, squares, pentagons should be positions 1-3
    const earlyA = [
      getPolygonSides('A', 1),
      getPolygonSides('A', 2),
      getPolygonSides('A', 3)
    ];
    expect(earlyA).toContain(3);  // Triangle
    expect(earlyA).toContain(5);  // Pentagon
    expect(earlyA).toContain(7);  // Heptagon (odd stable)

    const earlyD = [
      getPolygonSides('D', 1),
      getPolygonSides('D', 2),
      getPolygonSides('D', 3)
    ];
    expect(earlyD).toContain(4);  // Square
    expect(earlyD).toContain(5);  // Pentagon
  });

  test('Triangle-square attachment is accessible as A₁-B₁', () => {
    const tri = getPolygonSides('A', 1);
    const square = getPolygonSides('B', 1);
    expect(tri).toBe(3);
    expect(square).toBe(4);
    // This represents the most stable attachment
  });

  test('Tetrahedron base (tri-tri) is accessible as A₁-A₁', () => {
    const tri = getPolygonSides('A', 1);
    expect(tri).toBe(3);
    // A₁ + A₁ attachment creates tetrahedron foundation
  });
});

describe('Integration with Existing Code', () => {
  test('Symbol format matches expected pattern', () => {
    const symbol = generateSingleSymbol('A', 1);
    expect(symbol).toMatch(/^[ABCD]₁$/);
  });

  test('Can generate all 36 base symbols', () => {
    const series: ('A' | 'B' | 'C' | 'D')[] = ['A', 'B', 'C', 'D'];
    const symbols = new Set<string>();
    
    series.forEach(s => {
      for (let sub = 1; sub <= 9; sub++) {
        const symbol = generateSingleSymbol(s, sub);
        symbols.add(symbol);
      }
    });
    
    expect(symbols.size).toBe(36); // 4 series × 9 positions
  });
});
