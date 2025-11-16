/**
 * Polygon Symbol Mapping for Polylog6 Unicode Compression
 * 
 * Maps polygon side counts to Unicode symbols following Polylog6 architecture
 */

export interface PolygonSymbol {
  sides: number;
  symbol: string;
  name: string;
  unicodeBase: string;
}

/**
 * Level 0: Primitive polygon symbols (A-R for 3-20 sides)
 */
export const POLYGON_SYMBOLS: Record<number, PolygonSymbol> = {
  3: { sides: 3, symbol: 'A', name: 'Triangle', unicodeBase: 'A' },
  4: { sides: 4, symbol: 'B', name: 'Square', unicodeBase: 'B' },
  5: { sides: 5, symbol: 'C', name: 'Pentagon', unicodeBase: 'C' },
  6: { sides: 6, symbol: 'D', name: 'Hexagon', unicodeBase: 'D' },
  7: { sides: 7, symbol: 'E', name: 'Heptagon', unicodeBase: 'E' },
  8: { sides: 8, symbol: 'F', name: 'Octagon', unicodeBase: 'F' },
  9: { sides: 9, symbol: 'G', name: 'Nonagon', unicodeBase: 'G' },
  10: { sides: 10, symbol: 'H', name: 'Decagon', unicodeBase: 'H' },
  11: { sides: 11, symbol: 'I', name: 'Hendecagon', unicodeBase: 'I' },
  12: { sides: 12, symbol: 'J', name: 'Dodecagon', unicodeBase: 'J' },
  13: { sides: 13, symbol: 'K', name: 'Tridecagon', unicodeBase: 'K' },
  14: { sides: 14, symbol: 'L', name: 'Tetradecagon', unicodeBase: 'L' },
  15: { sides: 15, symbol: 'M', name: 'Pentadecagon', unicodeBase: 'M' },
  16: { sides: 16, symbol: 'N', name: 'Hexadecagon', unicodeBase: 'N' },
  17: { sides: 17, symbol: 'O', name: 'Heptadecagon', unicodeBase: 'O' },
  18: { sides: 18, symbol: 'P', name: 'Octadecagon', unicodeBase: 'P' },
  19: { sides: 19, symbol: 'Q', name: 'Enneadecagon', unicodeBase: 'Q' },
  20: { sides: 20, symbol: 'R', name: 'Icosagon', unicodeBase: 'R' },
};

/**
 * Level 1: Pair compression symbols (Greek letters)
 */
export const PAIR_SYMBOLS: Record<string, string> = {
  'AA': 'α', // U+03B1
  'AB': 'β', // U+03B2
  'BB': 'γ', // U+03B3
  'AC': 'δ', // U+03B4
  'BC': 'ε', // U+03B5
  'CC': 'ζ', // U+03B6
  'AD': 'η', // U+03B7
  'BD': 'θ', // U+03B8
  'CD': 'ι', // U+03B9
  'DD': 'κ', // U+03BA
};

/**
 * Get symbol for polygon by side count
 */
export function getPolygonSymbol(sides: number): string {
  const symbol = POLYGON_SYMBOLS[sides];
  return symbol ? symbol.symbol : '?';
}

/**
 * Get polygon name by side count
 */
export function getPolygonName(sides: number): string {
  const symbol = POLYGON_SYMBOLS[sides];
  return symbol ? symbol.name : `${sides}-gon`;
}

/**
 * Get side count from symbol
 */
export function getSidesFromSymbol(symbol: string): number | null {
  for (const [sides, data] of Object.entries(POLYGON_SYMBOLS)) {
    if (data.symbol === symbol) {
      return parseInt(sides);
    }
  }
  return null;
}

/**
 * Generate composition string from polygon list
 * Example: [3, 3, 4] → "AAB"
 */
export function generateComposition(polygonSides: number[]): string {
  return polygonSides.map(sides => getPolygonSymbol(sides)).join('');
}

/**
 * Compress composition using pair symbols if possible
 * Example: "AAAA" → "αα" or "AA"
 */
export function compressComposition(composition: string): string {
  let compressed = composition;
  
  // Try to replace pairs with Greek letters
  for (const [pair, symbol] of Object.entries(PAIR_SYMBOLS)) {
    const regex = new RegExp(pair, 'g');
    compressed = compressed.replace(regex, symbol);
  }
  
  return compressed;
}

/**
 * Calculate O value (number of unique polygon types)
 */
export function calculateOValue(polygonSides: number[]): number {
  const uniqueSides = new Set(polygonSides);
  return uniqueSides.size;
}

/**
 * Calculate I value (complexity metric)
 * Simplified version based on attachment pattern
 */
export function calculateIValue(polygonSides: number[], attachmentCount: number): number {
  // I value increases with number of attachments and polygon diversity
  const oValue = calculateOValue(polygonSides);
  const avgSides = polygonSides.reduce((sum, s) => sum + s, 0) / polygonSides.length;
  
  // Simple formula: I = attachments / (avgSides * O)
  return Math.ceil(attachmentCount / (avgSides * Math.max(oValue, 1)));
}

/**
 * Generate edge signature
 * Example: polygons [11, 20] → "11-20"
 */
export function generateEdgeSignature(polygon1Sides: number, polygon2Sides: number): string {
  return `${polygon1Sides}-${polygon2Sides}`;
}

/**
 * Determine tier based on polygon count and closure
 */
export function determineTier(polygonCount: number, isClosed: boolean): number {
  if (polygonCount <= 2) return 0; // Tier 0: Primitives and pairs
  if (isClosed && polygonCount <= 20) return 1; // Tier 1: Polyhedra
  return 2; // Tier 2+: Complex assemblies
}

/**
 * Generate polyform symbol for export
 * Format: <base><position1><position2>...
 * Example: "A111" for triangle at position 1 with pentagon at position 1
 */
export function generatePolyformSymbol(
  baseSymbol: string,
  positions: number[]
): string {
  return baseSymbol + positions.join('');
}

/**
 * Detect symmetry group (simplified)
 * Returns: C_n (cyclic), D_n (dihedral), T (tetrahedral), O (octahedral), I (icosahedral)
 */
export function detectSymmetryGroup(polygonSides: number[], isClosed: boolean): string | null {
  if (!isClosed) return null;
  
  // Simple heuristics
  if (polygonSides.length === 4 && polygonSides.every(s => s === 3)) {
    return 'T'; // Tetrahedral (4 triangles)
  }
  
  if (polygonSides.length === 6 && polygonSides.every(s => s === 4)) {
    return 'O'; // Octahedral (6 squares = cube)
  }
  
  if (polygonSides.length === 8 && polygonSides.every(s => s === 3)) {
    return 'O'; // Octahedral (8 triangles)
  }
  
  // Check for cyclic symmetry
  const uniqueSides = new Set(polygonSides);
  if (uniqueSides.size === 1) {
    return `C_${polygonSides.length}`;
  }
  
  return null;
}

/**
 * Generate full Polylog6 export data
 */
export interface Polylog6Export {
  symbol: string;
  polygons: number[];
  positions: number[];
  series: string[];
  chain_length: number;
  edge_signature: string;
  tier: number;
  range_name: string;
  range_code: string;
  base_series: string;
  attachment_hint: string;
  unicode_codepoint: string | null;
  symmetry_group: string | null;
  frequency_rank: number;
  generated_at: string;
  composition: string;
  o_value: number;
  i_value: number;
}

export function generatePolylog6Export(
  polygonSides: number[],
  attachmentCount: number,
  isClosed: boolean
): Polylog6Export {
  const composition = generateComposition(polygonSides);
  const oValue = calculateOValue(polygonSides);
  const iValue = calculateIValue(polygonSides, attachmentCount);
  const tier = determineTier(polygonSides.length, isClosed);
  const symmetryGroup = detectSymmetryGroup(polygonSides, isClosed);
  
  // Generate series (unique symbols)
  const series = Array.from(new Set(polygonSides.map(s => getPolygonSymbol(s))));
  
  // Generate positions (1-indexed)
  const positions = polygonSides.map((_, i) => i + 1);
  
  // Generate symbol
  const baseSymbol = getPolygonSymbol(polygonSides[0]);
  const symbol = generatePolyformSymbol(baseSymbol, positions);
  
  // Generate edge signature (simplified - first two polygons)
  const edgeSignature = polygonSides.length >= 2
    ? generateEdgeSignature(polygonSides[0], polygonSides[1])
    : `${polygonSides[0]}`;
  
  // Determine range
  let rangeName = '';
  let rangeCode = '';
  if (polygonSides.length === 1) {
    rangeName = 'Single Polygon';
    rangeCode = '0-9';
  } else if (polygonSides.length === 2) {
    rangeName = `Two-Polygon ${series.join('')}`;
    rangeCode = tier === 0 ? '10-99' : '100-199';
  } else {
    rangeName = `Multi-Polygon ${series.join('')}`;
    rangeCode = '200+';
  }
  
  return {
    symbol,
    polygons: polygonSides,
    positions,
    series,
    chain_length: polygonSides.length,
    edge_signature: edgeSignature,
    tier,
    range_name: rangeName,
    range_code: rangeCode,
    base_series: baseSymbol,
    attachment_hint: `base_${series[series.length - 1]}_connection`,
    unicode_codepoint: null, // TODO: Assign from Unicode block
    symmetry_group: symmetryGroup,
    frequency_rank: 0.5, // TODO: Calculate from usage statistics
    generated_at: new Date().toISOString(),
    composition,
    o_value: oValue,
    i_value: iValue,
  };
}
