/**
 * Workspace Manager
 * Manages polygon workspace state, chains, and movement
 * Based on unit edges and internal angles architecture
 * Integrates with GPU warming for precomputed Tier 0 symbols
 */

import * as BABYLON from '@babylonjs/core';
import { getGPUWarmingManager } from './gpuWarmingManager.js';
import { tier0Encoder } from './tier0Encoder.js';
import { 
  calculateCircumradius, 
  calculateInternalAngle,
  getFoldAngleFromBackend
} from './geometryUtils.js';
import { decodeTier0Symbol, detectAtomicChain } from '../services/tier0Service.js';

export class WorkspacePolygon {
  constructor(id, symbol, sides, mesh, metadata = {}) {
    this.id = id;
    this.symbol = symbol;
    this.sides = sides;
    this.mesh = mesh;
    this.metadata = metadata;
    
    // Unit edge properties (use geometryUtils for consistency)
    this.unitEdgeLength = 1.0;
    this.circumradius = calculateCircumradius(this.sides);
    this.internalAngle = calculateInternalAngle(this.sides);
    
    // Workspace state
    this.position = mesh.position.clone();
    this.rotation = mesh.rotation.clone();
    this.openEdges = new Set(Array.from({ length: this.sides }, (_, i) => i));
    this.attachedTo = new Map(); // edgeIndex -> AttachmentInfo
    this.chainId = null; // Part of chain/subform
    
    // Initialize edges
    this.edges = this.calculateEdges();
  }
  
  calculateEdges() {
    const edges = [];
    const positions = this.mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
    
    if (!positions || positions.length < 9) {
      // Fallback: generate edges from circumradius
      for (let i = 0; i < this.sides; i++) {
        const angle1 = (i * 2 * Math.PI) / this.sides;
        const angle2 = ((i + 1) * 2 * Math.PI) / this.sides;
        
        const start = new BABYLON.Vector3(
          this.circumradius * Math.cos(angle1),
          0,
          this.circumradius * Math.sin(angle1)
        );
        const end = new BABYLON.Vector3(
          this.circumradius * Math.cos(angle2),
          0,
          this.circumradius * Math.sin(angle2)
        );
        
        edges.push({
          index: i,
          start: start.add(this.position),
          end: end.add(this.position),
          midpoint: BABYLON.Vector3.Center(start, end).add(this.position),
          length: this.unitEdgeLength,
          internalAngle: this.internalAngle,
          isOpen: true
        });
      }
    } else {
      // Use actual mesh vertices
      const vertexCount = positions.length / 3;
      for (let i = 0; i < vertexCount; i++) {
        const v1 = new BABYLON.Vector3(
          positions[i * 3],
          positions[i * 3 + 1],
          positions[i * 3 + 2]
        );
        const v2 = new BABYLON.Vector3(
          positions[((i + 1) % vertexCount) * 3],
          positions[((i + 1) % vertexCount) * 3 + 1],
          positions[((i + 1) % vertexCount) * 3 + 2]
        );
        
        edges.push({
          index: i,
          start: v1,
          end: v2,
          midpoint: BABYLON.Vector3.Center(v1, v2),
          length: BABYLON.Vector3.Distance(v1, v2),
          internalAngle: this.internalAngle,
          isOpen: true
        });
      }
    }
    
    return edges;
  }
  
  attachToEdge(edgeIndex, targetPolygon, targetEdgeIndex, foldAngle) {
    this.attachedTo.set(edgeIndex, {
      targetId: targetPolygon.id,
      targetEdgeIndex,
      foldAngle,
      timestamp: Date.now()
    });
    this.openEdges.delete(edgeIndex);
    
    // Update edge state
    if (this.edges[edgeIndex]) {
      this.edges[edgeIndex].isOpen = false;
    }
  }
  
  move(delta) {
    this.position.addInPlace(delta);
    this.mesh.position.addInPlace(delta);
    
    // Update edge positions
    this.edges.forEach(edge => {
      edge.start.addInPlace(delta);
      edge.end.addInPlace(delta);
      edge.midpoint.addInPlace(delta);
    });
  }
  
  setChainId(chainId) {
    this.chainId = chainId;
  }
}

export class Chain {
  constructor(id) {
    this.id = id;
    this.polygonIds = [];
    this.rootPolygonId = null;
  }
  
  addPolygon(polygonId) {
    if (!this.polygonIds.includes(polygonId)) {
      this.polygonIds.push(polygonId);
      if (!this.rootPolygonId) {
        this.rootPolygonId = polygonId;
      }
    }
  }
  
  move(delta, workspace) {
    // Move all polygons in chain together
    this.polygonIds.forEach(polyId => {
      const polygon = workspace.getPolygon(polyId);
      if (polygon) {
        polygon.move(delta);
      }
    });
  }
}

export class WorkspaceManager {
  constructor(scene) {
    this.scene = scene;
    this.polygons = new Map(); // id -> WorkspacePolygon
    this.chains = new Map(); // chainId -> Chain
    this.nextPolygonId = 0;
    this.nextChainId = 0;
    
    // GPU warming integration
    this.gpuWarming = getGPUWarmingManager();
    this.pendingWarming = new Set(); // Symbols being warmed
  }
  
  async addPolygon(symbol, sides, mesh, metadata = {}) {
    const id = `poly_${symbol}_${this.nextPolygonId++}`;
    const polygon = new WorkspacePolygon(id, symbol, sides, mesh, metadata);
    this.polygons.set(id, polygon);
    
    // Check if should form chain with existing polygons
    this.updateChains();
    
    // Warm GPU buffers for likely next chains (async, non-blocking)
    this.warmNextChains();
    
    return polygon;
  }
  
  getPolygon(id) {
    return this.polygons.get(id);
  }
  
  async attachPolygons(polygonAId, edgeAIndex, polygonBId, edgeBIndex, foldAngle = null) {
    const polyA = this.polygons.get(polygonAId);
    const polyB = this.polygons.get(polygonBId);
    
    if (!polyA || !polyB) return false;
    
    // Get fold angle from backend if not provided
    if (foldAngle === null) {
      foldAngle = await getFoldAngleFromBackend(polyA.sides, polyB.sides) || 0;
    }
    
    // Create bidirectional attachment
    polyA.attachToEdge(edgeAIndex, polyB, edgeBIndex, foldAngle);
    polyB.attachToEdge(edgeBIndex, polyA, edgeAIndex, -foldAngle);
    
    // Update chains
    this.updateChains();
    
    // Generate Tier 0 symbol for chain (pass-back to CPU)
    const chain = this.getChainForPolygon(polygonAId);
    if (chain && chain.polygonIds.length > 1) {
      await this.generateTier0Symbol(chain);
    }
    
    // Warm GPU buffers for next likely chains
    this.warmNextChains();
    
    return true;
  }
  
  detectChain(polygonId) {
    // BFS to find all connected polygons
    const visited = new Set();
    const chain = [];
    const queue = [polygonId];
    
    while (queue.length > 0) {
      const current = queue.shift();
      if (visited.has(current)) continue;
      
      visited.add(current);
      chain.push(current);
      
      const polygon = this.polygons.get(current);
      if (!polygon) continue;
      
      // Find all attached neighbors
      for (const [edgeIdx, attachment] of polygon.attachedTo) {
        if (!visited.has(attachment.targetId)) {
          queue.push(attachment.targetId);
        }
      }
    }
    
    return chain;
  }
  
  updateChains() {
    // Clear existing chain assignments
    this.polygons.forEach(poly => poly.setChainId(null));
    
    // Detect all chains
    const visited = new Set();
    const chains = [];
    
    this.polygons.forEach((polygon, id) => {
      if (visited.has(id)) return;
      
      const chainIds = this.detectChain(id);
      if (chainIds.length > 1) {
        // Multiple polygons form a chain
        const chainId = `chain_${this.nextChainId++}`;
        const chain = new Chain(chainId);
        
        chainIds.forEach(pid => {
          chain.addPolygon(pid);
          this.polygons.get(pid).setChainId(chainId);
          visited.add(pid);
        });
        
        chains.push(chain);
        this.chains.set(chainId, chain);
        
        // Generate Tier 0 symbol for new chain (async, non-blocking)
        this.generateTier0Symbol(chain).then(symbol => {
          if (symbol && this.onChainTier0Generated) {
            // Notify visualization system
            this.onChainTier0Generated(chain, symbol);
          }
        }).catch(err => {
          console.warn('[WorkspaceManager] Tier 0 generation error:', err);
        });
      } else {
        // Single polygon (no chain)
        visited.add(id);
      }
    });
    
    // Remove chains that no longer exist
    const activeChainIds = new Set(chains.map(c => c.id));
    for (const [chainId, chain] of this.chains) {
      if (!activeChainIds.has(chainId)) {
        this.chains.delete(chainId);
      }
    }
  }
  
  /**
   * Set callback for when Tier 0 symbol is generated for a chain
   * Used for visualization integration
   */
  setOnChainTier0Generated(callback) {
    this.onChainTier0Generated = callback;
  }
  
  getChainForPolygon(polygonId) {
    const polygon = this.polygons.get(polygonId);
    if (!polygon || !polygon.chainId) return null;
    return this.chains.get(polygon.chainId);
  }
  
  movePolygon(polygonId, delta) {
    const polygon = this.polygons.get(polygonId);
    if (!polygon) return false;
    
    // If polygon is part of chain, move entire chain
    const chain = this.getChainForPolygon(polygonId);
    if (chain) {
      chain.move(delta, this);
    } else {
      // Move single polygon
      polygon.move(delta);
    }
    
    return true;
  }
  
  getAllOpenEdges() {
    const openEdges = [];
    this.polygons.forEach(polygon => {
      polygon.openEdges.forEach(edgeIndex => {
        openEdges.push({
          polygonId: polygon.id,
          edgeIndex,
          edge: polygon.edges[edgeIndex]
        });
      });
    });
    return openEdges;
  }

  getPolygonCount() {
    return this.polygons.size;
  }

  getChainCount() {
    return this.chains.size;
  }

  /**
   * Warm GPU buffers for likely next chains (async, non-blocking)
   */
  async warmNextChains() {
    // Don't block on warming
    this.gpuWarming.warmAttachmentsFor({
      polygons: Array.from(this.polygons.values()),
      chains: Array.from(this.chains.values())
    }).catch(err => {
      console.warn('[WorkspaceManager] GPU warming error:', err);
    });
  }

  /**
   * Generate Tier 0 symbol for chain (pass-back from GPU to CPU)
   * Integrated with backend Tier 0 API for verification
   */
  async generateTier0Symbol(chain) {
    try {
      // Get polygon sequence from chain
      const polygonSequence = chain.polygonIds.map(id => {
        const polygon = this.polygons.get(id);
        return polygon ? polygon.sides : null;
      }).filter(sides => sides !== null);
      
      if (polygonSequence.length < 2) {
        return null; // Single polygon, no chain symbol needed
      }
      
      // Encode as Tier 0 symbol (frontend encoding)
      const chainSymbol = tier0Encoder.encodeChain(polygonSequence);
      
      // Verify with backend (optional, async)
      decodeTier0Symbol(chainSymbol).then(decoded => {
        if (decoded && decoded.polygons) {
          // Verify polygon sequence matches
          const matches = decoded.polygons.length === polygonSequence.length &&
            decoded.polygons.every((p, i) => p === polygonSequence[i]);
          
          if (!matches) {
            console.warn('[WorkspaceManager] Tier 0 symbol mismatch:', {
              frontend: polygonSequence,
              backend: decoded.polygons
            });
          }
        }
      }).catch(err => {
        console.warn('[WorkspaceManager] Backend verification error:', err);
      });
      
      // Detect atomic chain pattern (async, non-blocking)
      detectAtomicChain(chainSymbol).then(atomicChain => {
        if (atomicChain) {
          chain.atomicChainType = atomicChain.chain_type;
          chain.scaffoldApplications = atomicChain.scaffold_applications;
          console.log(`[WorkspaceManager] Detected atomic chain: ${atomicChain.chain_type} for ${chainSymbol}`);
        }
      }).catch(err => {
        console.warn('[WorkspaceManager] Atomic chain detection error:', err);
      });
      
      // Warm GPU buffer for this chain symbol
      const attachmentData = await this.gpuWarming.warmChain(chainSymbol, 
        chain.polygonIds.map(id => this.polygons.get(id)).filter(p => p !== null)
      );
      
      // Store Tier 0 symbol in chain metadata
      chain.tier0Symbol = chainSymbol;
      chain.attachmentData = attachmentData;
      
      // Pass-back: Send to backend for indexing (async, non-blocking)
      this.sendTier0SymbolToBackend(chainSymbol, polygonSequence).catch(err => {
        console.warn('[WorkspaceManager] Backend pass-back error:', err);
      });
      
      return chainSymbol;
    } catch (error) {
      console.warn('[WorkspaceManager] Tier 0 symbol generation error:', error);
      return null;
    }
  }

  /**
   * Send Tier 0 symbol to backend for indexing (pass-back)
   */
  async sendTier0SymbolToBackend(symbol, polygonSequence) {
    try {
      const response = await fetch('/api/storage/polyform', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          symbol,
          composition: polygonSequence,
          tier: 0,
          source: 'user_created'
        })
      });
      
      if (!response.ok) {
        console.warn('[WorkspaceManager] Backend registration failed:', response.status);
      }
    } catch (error) {
      console.warn('[WorkspaceManager] Backend registration error:', error);
    }
  }

  /**
   * Get GPU warming statistics
   */
  getGPUWarmingStats() {
    return this.gpuWarming.getStats();
  }
}

