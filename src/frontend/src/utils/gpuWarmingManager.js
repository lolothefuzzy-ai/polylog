/**
 * GPU Warming Manager
 * Async CPU pipeline for pre-warming GPU buffers with precomputed Tier 0 symbols
 * Implements double async warming with pass-back and pruning strategies
 */

import { tier0Encoder } from './tier0Encoder.js';

/**
 * Async CPU Pipeline
 * Runs ahead of GPU, streams attachment data asynchronously
 * GPU never waits on CPU
 */
export class AsyncCPUPipeline {
  constructor() {
    this.gpuBuffer = new Map(); // unicode_symbol -> attachment_data
    this.warmingQueue = [];
    this.isWarming = false;
    this.stats = {
      cacheHits: 0,
      cacheMisses: 0,
      warmedSymbols: 0,
      predictions: 0
    };
    
    // Precomputed Tier 0 cache (loaded from API)
    this.tier0Cache = new Map();
    this.tier0Loaded = false;
  }

  /**
   * Load precomputed Tier 0 symbols from API
   */
  async loadPrecomputedTier0() {
    if (this.tier0Loaded) return;
    
    try {
      const response = await fetch('/api/storage/symbols?tier=0&limit=1000');
      if (!response.ok) {
        console.warn('[GPU Warming] Failed to load Tier 0 symbols:', response.status);
        return;
      }
      
      const data = await response.json();
      const symbols = data.items || data || [];
      
      symbols.forEach(symbol => {
        if (symbol.symbol) {
          this.tier0Cache.set(symbol.symbol, symbol);
        }
      });
      
      this.tier0Loaded = true;
      console.log(`[GPU Warming] Loaded ${this.tier0Cache.size} precomputed Tier 0 symbols`);
    } catch (error) {
      console.warn('[GPU Warming] Error loading Tier 0 symbols:', error);
    }
  }

  /**
   * Warm attachments for current assembly
   * Predicts which polyforms user likely to add next
   * Pre-computes their attachment patterns
   */
  async warmAttachmentsFor(currentAssembly) {
    // Ensure Tier 0 cache is loaded
    await this.loadPrecomputedTier0();
    
    if (this.isWarming) return; // Already warming
    this.isWarming = true;
    
    try {
      // Step 1: Analyze current assembly
      const usedSymbols = this.extractUsedSymbols(currentAssembly);
      const openEdges = this.extractOpenEdges(currentAssembly);
      
      // Step 2: Predict next candidates (heuristic)
      const candidates = this.predictNextCandidates(usedSymbols, openEdges);
      this.stats.predictions += candidates.length;
      
      // Step 3: For each candidate, pre-compute attachments
      for (const candidateSymbol of candidates) {
        // Check if precomputed Tier 0 symbol exists
        const precomputed = this.tier0Cache.get(candidateSymbol);
        
        if (precomputed) {
          // Use precomputed attachment data
          const attachmentData = await this.extractAttachmentData(precomputed, openEdges);
          this.gpuBuffer.set(candidateSymbol, attachmentData);
          this.stats.warmedSymbols++;
        } else {
          // Compute attachment on-demand (fallback)
          const attachmentData = await this.computeAttachment(candidateSymbol, openEdges);
          if (attachmentData) {
            this.gpuBuffer.set(candidateSymbol, attachmentData);
            this.stats.warmedSymbols++;
          }
        }
      }
    } finally {
      this.isWarming = false;
    }
  }

  /**
   * GPU polls (doesn't wait): get pre-computed attachment or null
   */
  gpuPollAttachment(unicodeSymbol) {
    if (this.gpuBuffer.has(unicodeSymbol)) {
      this.stats.cacheHits++;
      return this.gpuBuffer.get(unicodeSymbol); // O(1) hit
    } else {
      this.stats.cacheMisses++;
      return null; // GPU renders placeholder, attachment data will arrive later
    }
  }

  /**
   * Extract used symbols from current assembly
   */
  extractUsedSymbols(assembly) {
    const symbols = [];
    
    if (assembly.polygons) {
      assembly.polygons.forEach(polygon => {
        if (polygon.symbol) {
          symbols.push(polygon.symbol);
        }
      });
    }
    
    return symbols;
  }

  /**
   * Extract open edges from current assembly
   */
  extractOpenEdges(assembly) {
    const openEdges = [];
    
    if (assembly.polygons) {
      assembly.polygons.forEach(polygon => {
        if (polygon.openEdges) {
          polygon.openEdges.forEach(edgeIndex => {
            openEdges.push({
              polygonId: polygon.id,
              edgeIndex,
              sides: polygon.sides
            });
          });
        }
      });
    }
    
    return openEdges;
  }

  /**
   * Predict next candidates (heuristic)
   * - Recent history (what user just placed)
   * - Tier 0 primitives (always likely)
   * - High-frequency chains (2-3 polygon chains)
   */
  predictNextCandidates(usedSymbols, openEdges) {
    const candidates = new Set();
    
    // Always include Tier 0 primitives (A-R, single polygons)
    const primitives = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R'];
    primitives.forEach(p => candidates.add(p));
    
    // Include most recently placed
    if (usedSymbols.length > 0) {
      candidates.add(usedSymbols[usedSymbols.length - 1]);
    }
    
    // Predict 2-polygon chains based on open edges
    if (openEdges.length > 0) {
      const edgeCounts = new Set(openEdges.map(e => e.sides));
      edgeCounts.forEach(sides => {
        // Generate likely 2-polygon chains (A + sides)
        primitives.forEach(base => {
          const chainSymbol = `${base}${sides}`;
          if (this.tier0Cache.has(chainSymbol)) {
            candidates.add(chainSymbol);
          }
        });
      });
    }
    
    // Limit to top 20 candidates
    return Array.from(candidates).slice(0, 20);
  }

  /**
   * Extract attachment data from precomputed Tier 0 symbol
   */
  async extractAttachmentData(precomputed, openEdges) {
    return {
      symbol: precomputed.symbol,
      polygons: precomputed.polygons || [],
      chainLength: precomputed.chain_length || 1,
      edgeSignature: precomputed.edge_signature || '',
      series: precomputed.series || [],
      attachmentHint: precomputed.attachment_hint || 'none',
      compatibleEdges: await this.findCompatibleEdges(precomputed, openEdges),
      foldAngles: await this.computeFoldAngles(precomputed.polygons || [])
    };
  }

  /**
   * Find compatible edges for attachment
   */
  async findCompatibleEdges(precomputed, openEdges) {
    const compatible = [];
    
    if (!precomputed.polygons || precomputed.polygons.length === 0) {
      return compatible;
    }
    
    const lastPolygonSides = precomputed.polygons[precomputed.polygons.length - 1];
    
    for (const openEdge of openEdges) {
      if (openEdge.sides === lastPolygonSides) {
        const foldAngle = await this.computeFoldAngle(lastPolygonSides, openEdge.sides);
        compatible.push({
          polygonId: openEdge.polygonId,
          edgeIndex: openEdge.edgeIndex,
          foldAngle
        });
      }
    }
    
    return compatible;
  }

  /**
   * Compute fold angles for polygon chain
   */
  async computeFoldAngles(polygons) {
    const foldAngles = [];
    
    for (let i = 0; i < polygons.length - 1; i++) {
      const sidesA = polygons[i];
      const sidesB = polygons[i + 1];
      const foldAngle = await this.computeFoldAngle(sidesA, sidesB);
      foldAngles.push(foldAngle);
    }
    
    return foldAngles;
  }

  /**
   * Compute fold angle between two polygons
   * Uses backend API for accuracy
   */
  async computeFoldAngle(sidesA, sidesB) {
    try {
      const response = await fetch(`/api/geometry/fold-angle/${sidesA}/${sidesB}`);
      if (response.ok) {
        const data = await response.json();
        return data.fold_angle;
      }
    } catch (error) {
      console.warn(`[GPU Warming] Error fetching fold angle: ${error.message}`);
    }
    
    // Fallback to local calculation
    const angleA = ((sidesA - 2) * Math.PI) / sidesA;
    const angleB = ((sidesB - 2) * Math.PI) / sidesB;
    return Math.PI - (angleA + angleB) / 2;
  }

  /**
   * Compute attachment on-demand (fallback)
   */
  async computeAttachment(symbol, openEdges) {
    // Try to decode symbol to get polygon chain
    try {
      const decoded = tier0Encoder.decodeSymbol(symbol);
      if (decoded && decoded.polygons) {
      return {
        symbol,
        polygons: decoded.polygons,
        chainLength: decoded.polygons.length,
        compatibleEdges: await this.findCompatibleEdges(decoded, openEdges),
        foldAngles: await this.computeFoldAngles(decoded.polygons)
      };
      }
    } catch (error) {
      console.warn('[GPU Warming] Failed to compute attachment for', symbol, error);
    }
    
    return null;
  }

  /**
   * Warm chain when instantiated into workspace
   */
  async warmChain(chainSymbol, chainPolygons) {
    await this.loadPrecomputedTier0();
    
    // Check if precomputed symbol exists
    const precomputed = this.tier0Cache.get(chainSymbol);
    
    if (precomputed) {
      const attachmentData = await this.extractAttachmentData(precomputed, []);
      this.gpuBuffer.set(chainSymbol, attachmentData);
      return attachmentData;
    }
    
    // Generate attachment data from chain polygons
    const attachmentData = {
      symbol: chainSymbol,
      polygons: chainPolygons.map(p => p.sides),
      chainLength: chainPolygons.length,
      foldAngles: await this.computeFoldAngles(chainPolygons.map(p => p.sides))
    };
    
    this.gpuBuffer.set(chainSymbol, attachmentData);
    return attachmentData;
  }

  /**
   * Get statistics
   */
  getStats() {
    return {
      ...this.stats,
      cacheSize: this.gpuBuffer.size,
      tier0CacheSize: this.tier0Cache.size,
      hitRate: this.stats.cacheHits / (this.stats.cacheHits + this.stats.cacheMisses) || 0
    };
  }

  /**
   * Clear cache (for testing/debugging)
   */
  clearCache() {
    this.gpuBuffer.clear();
    this.stats.cacheHits = 0;
    this.stats.cacheMisses = 0;
    this.stats.warmedSymbols = 0;
  }
}

// Singleton instance
let gpuWarmingInstance = null;

export function getGPUWarmingManager() {
  if (!gpuWarmingInstance) {
    gpuWarmingInstance = new AsyncCPUPipeline();
  }
  return gpuWarmingInstance;
}

