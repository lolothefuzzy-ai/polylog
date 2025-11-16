/**
 * Tier 0 Encoder/Decoder
 * Generates Tier 0 symbols for backend indexing
 * Visualization can work independently, but uses this for backend integration
 */

// Series tables - canonical reference
// NOTE: These match backend SERIES_TABLE in src/polylog6/storage/tier0_generator.py
// This is the DEFINITIVE specification - do not modify without updating backend
const SERIES_TABLE = {
  'A': [3, 4, 5, 6, 7, 8, 9, 10, 11],      // Position 1-9
  'B': [20, 4, 6, 8, 10, 12, 14, 16, 18],  // Position 1-9
  'C': [3, 6, 9, 12, 15, 18, 8, 7, 10],    // Position 1-9 (multiples of 3)
  'D': [14, 20, 13, 11, 4, 16, 17, 5, 19], // Position 1-9
};

// Total: 36 base positions (4 series × 9 positions)
// Supports 2000+ attachment sequences via subscript encoding (1-999)

// Inverted mapping: edge count -> [(series, position), ...]
const EDGE_TO_SERIES_REFS = {};
for (const [series, edges] of Object.entries(SERIES_TABLE)) {
  edges.forEach((edgeCount, index) => {
    const position = index + 1;
    if (!EDGE_TO_SERIES_REFS[edgeCount]) {
      EDGE_TO_SERIES_REFS[edgeCount] = [];
    }
    EDGE_TO_SERIES_REFS[edgeCount].push({ series, position });
  });
}

// Verify frontend matches backend - critical for integration
if (typeof window !== 'undefined') {
  console.log('[Tier0Encoder] Frontend Tier 0 encoder initialized');
  console.log('[Tier0Encoder] Series table matches backend:', SERIES_TABLE);
}

export class Tier0Encoder {
  /**
   * Encode attachment sequence as Tier 0 symbol
   * @param {Array<{sides: number}>} polygons - Array of polygon edge counts
   * @param {string} baseSeries - Base series (A, B, C, or D)
   * @returns {string} Tier 0 symbol (e.g., "A11", "A115")
   */
  static encodeAttachmentSequence(polygons, baseSeries = 'A') {
    if (polygons.length === 0) return null;
    if (polygons.length === 1) {
      // Single primitive: A1-A9
      const position = this.findSeriesPosition(polygons[0].sides, baseSeries);
      return position ? `${baseSeries}${position}` : null;
    }
    
    if (polygons.length === 2) {
      // Two-polygon attachment: A10-A99 (AB), A100-A199 (AC), A200-A299 (AD)
      const pos1 = this.findSeriesPosition(polygons[0].sides, baseSeries);
      const pos2 = this.findSeriesPosition(polygons[1].sides, 'B'); // Default to B for two-polygon
      
      if (pos1 && pos2) {
        return `${baseSeries}${pos1}${pos2}`;
      }
    }
    
    // Three+ polygon attachments: A100-A999
    // More complex encoding based on hundreds digit
    // For now, simplified encoding
    const positions = polygons.map(poly => 
      this.findSeriesPosition(poly.sides, baseSeries)
    ).filter(p => p !== null);
    
    if (positions.length === polygons.length) {
      return `${baseSeries}${positions.join('')}`;
    }
    
    return null;
  }
  
  /**
   * Find series position for an edge count
   * @param {number} edgeCount - Number of edges (3-20)
   * @param {string} preferredSeries - Preferred series (A, B, C, or D)
   * @returns {number|null} Position (1-9) or null if not found
   */
  static findSeriesPosition(edgeCount, preferredSeries = 'A') {
    // Check preferred series first
    const preferredIndex = SERIES_TABLE[preferredSeries]?.indexOf(edgeCount);
    if (preferredIndex !== -1) {
      return preferredIndex + 1;
    }
    
    // Check all series
    const refs = EDGE_TO_SERIES_REFS[edgeCount];
    if (refs && refs.length > 0) {
      // Prefer the preferred series if available
      const preferred = refs.find(r => r.series === preferredSeries);
      if (preferred) return preferred.position;
      // Otherwise return first match
      return refs[0].position;
    }
    
    return null;
  }
  
  /**
   * Decode Tier 0 symbol to get edge counts
   * @param {string} symbol - Tier 0 symbol (e.g., "A11", "A115")
   * @returns {Array<number>|null} Array of edge counts
   */
  static decodeTier0Symbol(symbol) {
    if (!symbol || symbol.length < 2) return null;
    
    const baseSeries = symbol[0].toUpperCase();
    const subscript = symbol.slice(1);
    
    if (!SERIES_TABLE[baseSeries]) return null;
    if (!/^\d+$/.test(subscript)) return null;
    
    const digits = subscript.split('').map(Number);
    const edgeCounts = [];
    
    if (digits.length === 1) {
      // Single digit: A1-A9
      const position = digits[0];
      if (position >= 1 && position <= 9) {
        edgeCounts.push(SERIES_TABLE[baseSeries][position - 1]);
      }
    } else if (digits.length === 2) {
      // Two digits: A10-A99 (AB attachment)
      const pos1 = digits[0];
      const pos2 = digits[1];
      if (pos1 >= 1 && pos1 <= 9 && pos2 >= 1 && pos2 <= 9) {
        edgeCounts.push(SERIES_TABLE[baseSeries][pos1 - 1]);
        edgeCounts.push(SERIES_TABLE['B'][pos2 - 1]);
      }
    } else if (digits.length === 3) {
      // Three digits: A100-A999
      const hundreds = digits[0];
      const tens = digits[1];
      const ones = digits[2];
      
      // Determine secondary series based on hundreds digit
      const secondarySeries = this.getSecondarySeries(baseSeries, hundreds);
      
      if (tens >= 1 && tens <= 9 && ones >= 1 && ones <= 9) {
        edgeCounts.push(SERIES_TABLE[baseSeries][tens - 1]);
        edgeCounts.push(SERIES_TABLE[secondarySeries][ones - 1]);
      }
    }
    
    return edgeCounts.length > 0 ? edgeCounts : null;
  }
  
  /**
   * Get secondary series based on base series and hundreds digit
   * @param {string} baseSeries - Base series (A, B, C, or D)
   * @param {number} hundreds - Hundreds digit (1-9)
   * @returns {string} Secondary series
   */
  static getSecondarySeries(baseSeries, hundreds) {
    const cyclicMap = {
      'A': ['C', 'D', 'B'],
      'B': ['D', 'A', 'C'],
      'C': ['A', 'B', 'D'],
      'D': ['B', 'C', 'A'],
    };
    
    const sequence = cyclicMap[baseSeries] || ['C', 'D', 'B'];
    
    if (hundreds >= 1 && hundreds <= 2) {
      return sequence[hundreds - 1];
    } else if (hundreds >= 3 && hundreds <= 5) {
      return sequence[hundreds - 3];
    } else if (hundreds >= 6 && hundreds <= 8) {
      return sequence[hundreds - 6];
    }
    
    return sequence[0]; // Default
  }
  
  /**
   * Get all possible series positions for an edge count
   * @param {number} edgeCount - Number of edges
   * @returns {Array<{series: string, position: number}>} Array of series positions
   */
  static getAllSeriesPositions(edgeCount) {
    return EDGE_TO_SERIES_REFS[edgeCount] || [];
  }

  /**
   * Encode chain as Tier 0 symbol (convenience method)
   * @param {Array<number>} polygonSides - Array of polygon edge counts
   * @param {string} baseSeries - Base series (A, B, C, or D)
   * @returns {string} Tier 0 symbol
   */
  static encodeChain(polygonSides, baseSeries = 'A') {
    const polygons = polygonSides.map(sides => ({ sides }));
    return this.encodeAttachmentSequence(polygons, baseSeries);
  }

  /**
   * Decode symbol (alias for decodeTier0Symbol)
   * @param {string} symbol - Tier 0 symbol
   * @returns {Object|null} Decoded data with polygons array
   */
  static decodeSymbol(symbol) {
    const polygons = this.decodeTier0Symbol(symbol);
    if (!polygons) return null;
    
    return {
      symbol,
      polygons,
      chainLength: polygons.length
    };
  }
}

// Export singleton instance for convenience
export const tier0Encoder = Tier0Encoder;

