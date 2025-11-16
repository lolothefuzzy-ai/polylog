/**
 * Tier 0 Service
 * Unified service for Tier 0 operations (encoding, decoding, atomic chains, scaffolds)
 * Connects frontend to backend Tier 0 API
 */

/**
 * Decode Tier 0 symbol from backend
 * @param {string} symbol - Tier 0 symbol (e.g., "A11", "B11")
 * @returns {Promise<Object>} Decoded symbol data
 */
export async function decodeTier0Symbol(symbol) {
  try {
    const response = await fetch(`/api/tier0/decode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol })
    });
    
    if (!response.ok) {
      throw new Error(`Decode failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn(`[Tier0Service] Decode error for ${symbol}:`, error);
    // Fallback to frontend decoder
    return decodeTier0SymbolLocal(symbol);
  }
}

/**
 * Decode Tier 0 symbol locally (fallback)
 * @param {string} symbol - Tier 0 symbol
 * @returns {Object|null} Decoded data
 */
function decodeTier0SymbolLocal(symbol) {
  // Use tier0Encoder for local decoding
  const { tier0Encoder } = require('../utils/tier0Encoder.js');
  const decoded = tier0Encoder.decodeSymbol(symbol);
  
  if (!decoded) return null;
  
  return {
    symbol: decoded.symbol,
    polygons: decoded.polygons,
    chain_length: decoded.chainLength,
    edge_signature: decoded.polygons.join('-')
  };
}

/**
 * Detect atomic chain in Tier 0 symbol
 * @param {string} symbol - Tier 0 symbol
 * @returns {Promise<Object>} Atomic chain data
 */
export async function detectAtomicChain(symbol) {
  try {
    const response = await fetch(`/api/tier0/atomic-chains/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol })
    });
    
    if (!response.ok) {
      throw new Error(`Detection failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn(`[Tier0Service] Atomic chain detection error for ${symbol}:`, error);
    return null;
  }
}

/**
 * Get atomic chain library
 * @returns {Promise<Object>} Library data
 */
export async function getAtomicChainLibrary() {
  try {
    const response = await fetch(`/api/tier0/atomic-chains/library`);
    
    if (!response.ok) {
      throw new Error(`Library fetch failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn('[Tier0Service] Library fetch error:', error);
    return { square_chains: [], triangle_clusters: [], mixed_chains: [] };
  }
}

// Export for use in components
export { getAtomicChainLibrary };

/**
 * Create scaffold from atomic chains
 * @param {Array<string>} atomicChains - Array of Tier 0 symbols
 * @param {string} targetPolyformType - Target polyform type
 * @returns {Promise<Object>} Scaffold data
 */
export async function createScaffold(atomicChains, targetPolyformType) {
  try {
    const response = await fetch(`/api/tier0/scaffolds/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        atomic_chains: atomicChains,
        target_polyform_type: targetPolyformType
      })
    });
    
    if (!response.ok) {
      throw new Error(`Scaffold creation failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn('[Tier0Service] Scaffold creation error:', error);
    return null;
  }
}

/**
 * Get scaffold for Johnson solid
 * @param {string} solidName - Johnson solid name
 * @returns {Promise<Object>} Scaffold data
 */
export async function getJohnsonSolidScaffold(solidName) {
  try {
    const response = await fetch(`/api/tier0/scaffolds/johnson-solid/${solidName}`);
    
    if (!response.ok) {
      throw new Error(`Scaffold fetch failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn(`[Tier0Service] Scaffold fetch error for ${solidName}:`, error);
    return null;
  }
}

