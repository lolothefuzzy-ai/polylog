/**
 * Unified Workspace Entry Point
 * 
 * Single entry point for all workspace operations
 * Provides unified API for polygon management, chain operations, and workspace state
 * Optimizes development workflow by centralizing workspace access
 */

import { WorkspaceManager } from './workspaceManager.js';
import { getGPUWarmingManager } from './gpuWarmingManager.js';

/**
 * Workspace Entry Point Singleton
 * Provides unified access to workspace operations
 */
class WorkspaceEntryPoint {
  constructor() {
    this.workspaceManager = null;
    this.scene = null;
    this.initialized = false;
  }

  /**
   * Initialize workspace entry point
   * Must be called before any workspace operations
   * 
   * @param {BABYLON.Scene} scene - Babylon.js scene
   * @returns {WorkspaceManager} Initialized workspace manager
   */
  initialize(scene) {
    if (this.initialized && this.scene === scene) {
      return this.workspaceManager;
    }

    this.scene = scene;
    this.workspaceManager = new WorkspaceManager(scene);
    this.initialized = true;
    
    console.log('[WorkspaceEntryPoint] Initialized');
    return this.workspaceManager;
  }

  /**
   * Get workspace manager instance
   * Returns null if not initialized
   */
  getWorkspaceManager() {
    if (!this.initialized) {
      console.warn('[WorkspaceEntryPoint] Not initialized. Call initialize() first.');
      return null;
    }
    return this.workspaceManager;
  }

  /**
   * Add polygon to workspace
   * Unified entry point for polygon addition
   * 
   * @param {string} symbol - Polygon symbol
   * @param {number} sides - Number of sides
   * @param {BABYLON.Mesh} mesh - Babylon.js mesh
   * @param {Object} metadata - Additional metadata
   * @returns {Promise<WorkspacePolygon>} Added workspace polygon
   */
  async addPolygon(symbol, sides, mesh, metadata = {}) {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      throw new Error('Workspace not initialized');
    }
    return await manager.addPolygon(symbol, sides, mesh, metadata);
  }

  /**
   * Attach two polygons
   * Unified entry point for attachment operations
   * 
   * @param {string} polygonAId - First polygon ID
   * @param {number} edgeAIndex - Edge index on first polygon
   * @param {string} polygonBId - Second polygon ID
   * @param {number} edgeBIndex - Edge index on second polygon
   * @param {number} foldAngle - Fold angle (optional, fetched from backend if not provided)
   * @returns {Promise<boolean>} Success status
   */
  async attachPolygons(polygonAId, edgeAIndex, polygonBId, edgeBIndex, foldAngle = null) {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      throw new Error('Workspace not initialized');
    }
    return await manager.attachPolygons(polygonAId, edgeAIndex, polygonBId, edgeBIndex, foldAngle);
  }

  /**
   * Move polygon (with chain support)
   * Unified entry point for movement operations
   * 
   * @param {string} polygonId - Polygon ID
   * @param {BABYLON.Vector3} delta - Movement delta
   * @returns {boolean} Success status
   */
  movePolygon(polygonId, delta) {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return false;
    }
    return manager.movePolygon(polygonId, delta);
  }

  /**
   * Get polygon by ID
   * 
   * @param {string} polygonId - Polygon ID
   * @returns {WorkspacePolygon|null} Workspace polygon or null
   */
  getPolygon(polygonId) {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return null;
    }
    return manager.getPolygon(polygonId);
  }

  /**
   * Get chain for polygon
   * 
   * @param {string} polygonId - Polygon ID
   * @returns {Chain|null} Chain or null
   */
  getChainForPolygon(polygonId) {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return null;
    }
    return manager.getChainForPolygon(polygonId);
  }

  /**
   * Get all workspace polygons
   * 
   * @returns {Array<WorkspacePolygon>} Array of workspace polygons
   */
  getAllPolygons() {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return [];
    }
    return Array.from(manager.polygons.values());
  }

  /**
   * Get all chains
   * 
   * @returns {Array<Chain>} Array of chains
   */
  getAllChains() {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return [];
    }
    return Array.from(manager.chains.values());
  }

  /**
   * Get all open edges
   * 
   * @returns {Array} Array of open edge objects
   */
  getAllOpenEdges() {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return [];
    }
    return manager.getAllOpenEdges();
  }

  /**
   * Warm GPU buffers for likely next chains
   * Unified entry point for GPU warming
   */
  async warmNextChains() {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return;
    }
    await manager.warmNextChains();
  }

  /**
   * Generate Tier 0 symbol for chain
   * Unified entry point for Tier 0 symbol generation
   * 
   * @param {Chain} chain - Chain object
   * @returns {Promise<string|null>} Tier 0 symbol or null
   */
  async generateTier0Symbol(chain) {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return null;
    }
    return await manager.generateTier0Symbol(chain);
  }

  /**
   * Get workspace statistics
   * 
   * @returns {Object} Workspace statistics
   */
  getStats() {
    const manager = this.getWorkspaceManager();
    if (!manager) {
      return {
        polygonCount: 0,
        chainCount: 0,
        openEdgeCount: 0
      };
    }
    
    const allOpenEdges = manager.getAllOpenEdges();
    return {
      polygonCount: manager.polygons.size,
      chainCount: manager.chains.size,
      openEdgeCount: allOpenEdges.length,
      gpuWarmingStats: getGPUWarmingManager().getStats()
    };
  }

  /**
   * Reset workspace
   * Clears all polygons and chains
   */
  reset() {
    const manager = this.getWorkspaceManager();
    if (manager) {
      manager.polygons.clear();
      manager.chains.clear();
      manager.nextPolygonId = 0;
      manager.nextChainId = 0;
      console.log('[WorkspaceEntryPoint] Workspace reset');
    }
  }

  /**
   * Check if workspace is initialized
   * 
   * @returns {boolean} Initialization status
   */
  isInitialized() {
    return this.initialized && this.workspaceManager !== null;
  }
}

// Singleton instance
let workspaceEntryPointInstance = null;

/**
 * Get workspace entry point singleton
 * 
 * @returns {WorkspaceEntryPoint} Workspace entry point instance
 */
export function getWorkspaceEntryPoint() {
  if (!workspaceEntryPointInstance) {
    workspaceEntryPointInstance = new WorkspaceEntryPoint();
  }
  return workspaceEntryPointInstance;
}

/**
 * Initialize workspace entry point
 * Convenience function for initialization
 * 
 * @param {BABYLON.Scene} scene - Babylon.js scene
 * @returns {WorkspaceManager} Initialized workspace manager
 */
export function initializeWorkspace(scene) {
  return getWorkspaceEntryPoint().initialize(scene);
}

