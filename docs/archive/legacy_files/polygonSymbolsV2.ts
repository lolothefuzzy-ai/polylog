/**
 * Convert Unicode subscript back to number
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

/**
 * Get polygon sides from series and subscript
 * @param series 'A', 'B', 'C', or 'D'
 * @param subscript 1-9
 */
export function getPolygonSides(series: 'A' | 'B' | 'C' | 'D', subscript: number): number {
  if (subscript < 1 || subscript > 9) {
    throw new Error('Subscript must be between 1 and 9 for single polygons');
  }
  
  const seriesData = ALL_SERIES[series];
  return seriesData[subscript - 1];  // Arrays are 0-indexed
}

/**
 * Get series and subscript from polygon sides
 * Returns all matches (some polygons appear in multiple series)
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
 * Generate Unicode symbol for single polygon
 * @param series 'A', 'B', 'C', or 'D'
 * @param subscript 1-9
 * @returns e.g., "A₁", "B₅", "C₉"
 */
export function generateSingleSymbol(series: 'A' | 'B' | 'C' | 'D', subscript: number): string {
  return `${series}${toSubscript(subscript)}`;
}

/**
 * Generate Unicode symbol for two-element pattern
 * @param series1 First series
 * @param series2 Second series
 * @param subscript 10-99 (determines position in secondary series)
 * @returns e.g., "AB₁₀", "CD₅₅"
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
 * Generate Unicode symbol for three-element pattern
 * @param series1 First series
 * @param series2 Second series
 * @param series3 Third series
 * @param subscript 100-999
 * @returns e.g., "ABC₁₀₀", "DAB₅₅₅"
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