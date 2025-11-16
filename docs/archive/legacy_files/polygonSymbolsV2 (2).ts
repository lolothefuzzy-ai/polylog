/**
 * Polylog6 Unicode Symbol System - OPTIMIZED for Attachment Stability
 * 
 * ABCD Series: Edge count mappings optimized to prioritize stable attachments
 * - Triangles, squares, pentagons placed early in series (positions 1-3)
 * - Higher-order polygons placed later (positions 4-9)
 * 
 * Version: 3.0 (Stability-Optimized)
 * Date: 2025-11-15
 */

// ============================================================================
// OPTIMIZED SERIES TABLES (DO NOT MODIFY WITHOUT VALIDATION)
// ============================================================================

/**
 * Series A: Odd-sided polygons (Triangle-first for stability)
 * Position 1-9 maps to edge counts
 */
const SERIES_A = [3, 5, 7, 9, 11, 13, 15, 17, 19];

/**
 * Series B: Even-sided polygons (Square-first, already optimal)
 * Position 1-9 maps to edge counts
 */
const SERIES_B = [4, 6, 8, 10, 12, 14, 16, 18, 20];

/**
 * Series C: Divisibility-optimized (multiples of 3, unchanged)
 * Position 1-9 maps to edge counts
 */
const SERIES_C = [3, 6, 9, 12, 15, 18, 7, 8, 10];

/**
 * Series D: Mixed distribution (Square-first, pentagon-second for stability)
 * Position 1-9 maps to edge counts
 */
const SERIES_D = [4, 5, 11, 13, 14, 16, 17, 19, 20];

/**
 * Combined series lookup table
 */
export const ALL_SERIES = {
  A: SERIES_A,
  B: SERIES_B,
  C: SERIES_C,
  D: SERIES_D,
} as const;

// ============================================================================
// UNICODE SUBSCRIPT UTILITIES
// ============================================================================

/**
 * Unicode subscript digits (₀-₉)
 */
const SUBSCRIPTS = '₀₁₂₃₄₅₆₇₈₉';

/**
 * Convert number to Unicode subscript string
 * @param num Number to convert (e.g., 42 → "₄₂")
 */
export function toSubscript(num: number): string {
  return num
    .toString()
    .split('')
    .map(digit => SUBSCRIPTS[parseInt(digit)])
    .join('');
}

/**
 * Convert Unicode subscript back to number
 * @param subscript Unicode subscript string (e.g., "₄₂" → 42)
 */
export function fromSubscript(subscript: string): number {
  let num = 0;
  for (const char of subscript) {
    const index = SUBSCRIPTS.indexOf(char);
    if (index === -1) {
      throw new Error(`Invalid subscript character: ${char}`);
    }
    num = num * 10 + index;
  }
  return num;
}

// ============================================================================
// CORE SERIES FUNCTIONS
// ============================================================================

/**
 * Get polygon edge count from series and subscript
 * @param series 'A', 'B', 'C', or 'D'
 * @param subscript 1-9 (position in series)
 * @returns Number of edges
 * @example getPolygonSides('A', 1) → 3 (triangle)
 * @example getPolygonSides('D', 1) → 4 (square)
 */
export function getPolygonSides(series: 'A' | 'B' | 'C' | 'D', subscript: number): number {
  if (subscript < 1 || subscript > 9) {
    throw new Error('Subscript must be between 1 and 9 for single polygons');
  }
  
  const seriesData = ALL_SERIES[series];
  return seriesData[subscript - 1];  // Arrays are 0-indexed
}

/**
 * Get all series/subscript combinations that produce a given edge count
 * @param sides Number of edges
 * @returns Array of {series, subscript} matches
 * @example getSeriesFromSides(3) → [{series: 'A', subscript: 1}, {series: 'C', subscript: 1}]
 */
export function getSeriesFromSides(sides: number): Array<{ series: 'A' | 'B' | 'C' | 'D', subscript: number }> {
  const matches: Array<{ series: 'A' | 'B' | 'C' | 'D', subscript: number }> = [];
  
  for (const [seriesName, seriesData] of Object.entries(ALL_SERIES)) {
    const index = seriesData.indexOf(sides);
    if (index !== -1) {
      matches.push({
        series: seriesName as 'A' | 'B' | 'C' | 'D',
        subscript: index + 1
      });
    }
  }
  
  return matches;
}

/**
 * Get the primary (most stable) series for a given edge count
 * Priority: A (odd) > D (mixed) > B (even) > C (divisibility)
 */
export function getPrimarySeries(sides: number): { series: 'A' | 'B' | 'C' | 'D', subscript: number } | null {
  const matches = getSeriesFromSides(sides);
  if (matches.length === 0) return null;
  
  // Prioritize by series stability
  const priority = ['A', 'D', 'B', 'C'];
  for (const preferredSeries of priority) {
    const match = matches.find(m => m.series === preferredSeries);
    if (match) return match;
  }
  
  return matches[0];
}

// ============================================================================
// SYMBOL GENERATION
// ============================================================================

/**
 * Generate Unicode symbol for single polygon
 * @param series 'A', 'B', 'C', or 'D'
 * @param subscript 1-9
 * @returns Unicode symbol (e.g., "A₁", "D₅")
 */
export function generateSingleSymbol(series: 'A' | 'B' | 'C' | 'D', subscript: number): string {
  if (subscript < 1 || subscript > 9) {
    throw new Error('Single symbol subscript must be 1-9');
  }
  return `${series}${toSubscript(subscript)}`;
}

/**
 * Generate Unicode symbol for two-polygon attachment
 * @param series1 First series
 * @param series2 Second series
 * @param subscript 10-99 (skips X0 patterns)
 * @returns Unicode symbol (e.g., "AB₁₁", "AD₂₃")
 */
export function generateTwoElementSymbol(
  series1: 'A' | 'B' | 'C' | 'D',
  series2: 'A' | 'B' | 'C' | 'D',
  subscript: number
): string {
  if (subscript < 10 || subscript > 99) {
    throw new Error('Two-element subscript must be between 10 and 99');
  }
  
  // Skip X0 patterns (10, 20, 30, etc.)
  if (subscript % 10 === 0) {
    throw new Error('X0 patterns are skipped (no 10, 20, 30, etc.)');
  }
  
  return `${series1}${series2}${toSubscript(subscript)}`;
}

/**
 * Generate Unicode symbol for three-polygon chain
 * @param series1 First series
 * @param series2 Second series
 * @param series3 Third series
 * @param subscript 100-999
 * @returns Unicode symbol (e.g., "ABC₁₀₀", "DAB₅₅₅")
 */
export function generateThreeElementSymbol(
  series1: 'A' | 'B' | 'C' | 'D',
  series2: 'A' | 'B' | 'C' | 'D',
  series3: 'A' | 'B' | 'C' | 'D',
  subscript: number
): string {
  if (subscript < 100 || subscript > 999) {
    throw new Error('Three-element subscript must be between 100 and 999');
  }
  
  // Skip X00, XX0 patterns
  if (subscript % 100 === 0 || subscript % 10 === 0) {
    throw new Error('X00 and XX0 patterns are skipped');
  }
  
  return `${series1}${series2}${series3}${toSubscript(subscript)}`;
}

// ============================================================================
// VALIDATION & UTILITIES
// ============================================================================

/**
 * Validate series tables on module load
 */
export function validateSeriesTables(): boolean {
  // Check all series have exactly 9 entries
  for (const [name, series] of Object.entries(ALL_SERIES)) {
    if (series.length !== 9) {
      console.error(`Series ${name} has ${series.length} entries, expected 9`);
      return false;
    }
  }
  
  // Check all edge counts are in valid range (3-20)
  const allEdgeCounts = Object.values(ALL_SERIES).flat();
  const invalidCounts = allEdgeCounts.filter(count => count < 3 || count > 20);
  if (invalidCounts.length > 0) {
    console.error(`Invalid edge counts found: ${invalidCounts}`);
    return false;
  }
  
  // Check for required triangles and squares
  const hasTriangle = getSeriesFromSides(3).length > 0;
  const hasSquare = getSeriesFromSides(4).length > 0;
  
  if (!hasTriangle || !hasSquare) {
    console.error('Series must include triangles (3) and squares (4)');
    return false;
  }
  
  console.log('✅ ABCD Series tables validated successfully');
  console.log(`   A₁ = ${getPolygonSides('A', 1)} sides (triangle)`);
  console.log(`   B₁ = ${getPolygonSides('B', 1)} sides (square)`);
  console.log(`   D₁ = ${getPolygonSides('D', 1)} sides (square)`);
  
  return true;
}

// Run validation on module load
validateSeriesTables();

// ============================================================================
// EXPORTS
// ============================================================================

export type Series = 'A' | 'B' | 'C' | 'D';
export type Subscript = number; // 1-999

export interface PolygonSymbol {
  series: Series;
  subscript: Subscript;
  edgeCount: number;
  symbol: string;
}
