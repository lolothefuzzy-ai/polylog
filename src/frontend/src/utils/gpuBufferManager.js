/**
 * GPU Buffer Manager
 * Manages GPU buffers for precomputed chain data
 * Integrates with Babylon.js for efficient rendering
 */

import * as BABYLON from '@babylonjs/core';

/**
 * GPU Buffer Manager
 * Handles GPU-side caching and buffer management for chains
 */
export class GPUBufferManager {
  constructor(engine) {
    this.engine = engine;
    this.scene = null;
    
    // GPU buffers for chain data
    this.chainBuffers = new Map(); // chainSymbol -> GPU buffer
    this.meshCache = new Map(); // chainSymbol -> Babylon mesh
    
    // Instanced rendering pools
    this.instancePools = new Map(); // polygonSides -> InstancedMesh pool
    
    // Statistics
    this.stats = {
      buffersCreated: 0,
      buffersReused: 0,
      meshesCreated: 0,
      meshesReused: 0
    };
  }

  /**
   * Set scene reference
   */
  setScene(scene) {
    this.scene = scene;
  }

  /**
   * Get or create GPU buffer for chain symbol
   * Non-blocking: returns cached buffer or null
   */
  getChainBuffer(chainSymbol, attachmentData) {
    // Check cache first
    if (this.chainBuffers.has(chainSymbol)) {
      this.stats.buffersReused++;
      return this.chainBuffers.get(chainSymbol);
    }
    
    // Create new buffer if attachment data provided
    if (attachmentData) {
      const buffer = this.createChainBuffer(chainSymbol, attachmentData);
      this.chainBuffers.set(chainSymbol, buffer);
      this.stats.buffersCreated++;
      return buffer;
    }
    
    // Cache miss - return null (GPU will render placeholder)
    return null;
  }

  /**
   * Create GPU buffer for chain
   */
  createChainBuffer(chainSymbol, attachmentData) {
    const { polygons, foldAngles } = attachmentData;
    
    // Create vertex buffer for chain geometry
    const vertices = this.generateChainVertices(polygons, foldAngles);
    
    // Create Babylon.js buffer
    const vertexBuffer = new BABYLON.VertexBuffer(
      this.engine,
      vertices,
      BABYLON.VertexBuffer.PositionKind,
      false,
      false,
      3, // 3 components (x, y, z)
      3 * 4 // stride: 3 floats * 4 bytes
    );
    
    return {
      symbol: chainSymbol,
      vertexBuffer,
      polygonCount: polygons.length,
      vertexCount: vertices.length / 3,
      foldAngles
    };
  }

  /**
   * Generate vertices for chain geometry
   */
  generateChainVertices(polygons, foldAngles) {
    const vertices = [];
    let currentTransform = BABYLON.Matrix.Identity();
    
    polygons.forEach((sides, index) => {
      const polygonVertices = this.generatePolygonVertices(sides);
      
      // Transform vertices by current transform
      polygonVertices.forEach(vertex => {
        const transformed = BABYLON.Vector3.TransformCoordinates(vertex, currentTransform);
        vertices.push(transformed.x, transformed.y, transformed.z);
      });
      
      // Apply fold angle for next polygon (if exists)
      if (index < foldAngles.length) {
        const foldAngle = foldAngles[index];
        const rotation = BABYLON.Matrix.RotationY(foldAngle);
        currentTransform = currentTransform.multiply(rotation);
        
        // Translate to next attachment point
        const unitEdgeLength = 1.0;
        const translation = BABYLON.Matrix.Translation(unitEdgeLength, 0, 0);
        currentTransform = currentTransform.multiply(translation);
      }
    });
    
    return new Float32Array(vertices);
  }

  /**
   * Generate vertices for single polygon
   */
  generatePolygonVertices(sides) {
    const vertices = [];
    const unitEdgeLength = 1.0;
    const circumradius = unitEdgeLength / (2 * Math.sin(Math.PI / sides));
    
    for (let i = 0; i < sides; i++) {
      const angle = (i * 2 * Math.PI) / sides;
      const x = circumradius * Math.cos(angle);
      const z = circumradius * Math.sin(angle);
      vertices.push(new BABYLON.Vector3(x, 0, z));
    }
    
    return vertices;
  }

  /**
   * Get or create mesh for chain
   */
  getChainMesh(chainSymbol, attachmentData) {
    // Check cache
    if (this.meshCache.has(chainSymbol)) {
      this.stats.meshesReused++;
      return this.meshCache.get(chainSymbol);
    }
    
    if (!this.scene) {
      console.warn('[GPU Buffer Manager] Scene not set');
      return null;
    }
    
    // Get or create buffer
    let buffer = this.getChainBuffer(chainSymbol, attachmentData);
    if (!buffer) {
      return null; // Buffer not ready yet
    }
    
    // Create mesh from buffer
    const mesh = new BABYLON.Mesh(chainSymbol, this.scene);
    
    // Set vertex buffer
    mesh.setVerticesData(BABYLON.VertexBuffer.PositionKind, buffer.vertexBuffer.getData());
    
    // Create indices for polygon faces
    const indices = this.generateChainIndices(buffer.polygonCount, buffer.vertexCount);
    mesh.setIndices(indices);
    
    // Create material
    const material = new BABYLON.StandardMaterial(`${chainSymbol}_mat`, this.scene);
    material.diffuseColor = new BABYLON.Color3(0.5, 0.7, 0.9);
    material.specularColor = new BABYLON.Color3(0.2, 0.2, 0.2);
    mesh.material = material;
    
    this.meshCache.set(chainSymbol, mesh);
    this.stats.meshesCreated++;
    
    return mesh;
  }

  /**
   * Generate indices for chain faces
   */
  generateChainIndices(polygonCount, totalVertices) {
    const indices = [];
    let vertexOffset = 0;
    
    for (let p = 0; p < polygonCount; p++) {
      // Assume each polygon has same vertex count (simplified)
      const verticesPerPolygon = Math.floor(totalVertices / polygonCount);
      
      // Create fan triangulation for polygon
      for (let i = 1; i < verticesPerPolygon - 1; i++) {
        indices.push(vertexOffset);
        indices.push(vertexOffset + i);
        indices.push(vertexOffset + i + 1);
      }
      
      vertexOffset += verticesPerPolygon;
    }
    
    return indices;
  }

  /**
   * Get instanced mesh pool for polygon type
   */
  getInstancePool(polygonSides) {
    if (this.instancePools.has(polygonSides)) {
      return this.instancePools.get(polygonSides);
    }
    
    if (!this.scene) {
      return null;
    }
    
    // Create base mesh for polygon
    const baseMesh = this.createPolygonMesh(polygonSides);
    
    // Create instanced mesh pool
    const instancePool = {
      baseMesh,
      instances: [],
      maxInstances: 1000
    };
    
    this.instancePools.set(polygonSides, instancePool);
    return instancePool;
  }

  /**
   * Create base mesh for polygon
   */
  createPolygonMesh(sides) {
    const vertices = this.generatePolygonVertices(sides);
    const mesh = new BABYLON.Mesh(`polygon_${sides}`, this.scene);
    
    const positions = [];
    vertices.forEach(v => {
      positions.push(v.x, v.y, v.z);
    });
    
    mesh.setVerticesData(BABYLON.VertexBuffer.PositionKind, positions);
    
    // Create indices for fan triangulation
    const indices = [];
    for (let i = 1; i < sides - 1; i++) {
      indices.push(0, i, i + 1);
    }
    mesh.setIndices(indices);
    
    return mesh;
  }

  /**
   * Update chain buffer with new attachment data (pass-back from GPU)
   */
  updateChainBuffer(chainSymbol, attachmentData) {
    // Remove old buffer
    if (this.chainBuffers.has(chainSymbol)) {
      const oldBuffer = this.chainBuffers.get(chainSymbol);
      oldBuffer.vertexBuffer.dispose();
      this.chainBuffers.delete(chainSymbol);
    }
    
    // Create new buffer
    const buffer = this.createChainBuffer(chainSymbol, attachmentData);
    this.chainBuffers.set(chainSymbol, buffer);
    
    // Update mesh if exists
    if (this.meshCache.has(chainSymbol)) {
      const mesh = this.meshCache.get(chainSymbol);
      mesh.setVerticesData(BABYLON.VertexBuffer.PositionKind, buffer.vertexBuffer.getData());
    }
  }

  /**
   * Dispose resources
   */
  dispose() {
    // Dispose all buffers
    this.chainBuffers.forEach(buffer => {
      buffer.vertexBuffer.dispose();
    });
    this.chainBuffers.clear();
    
    // Dispose all meshes
    this.meshCache.forEach(mesh => {
      mesh.dispose();
    });
    this.meshCache.clear();
    
    // Dispose instance pools
    this.instancePools.forEach(pool => {
      pool.baseMesh.dispose();
      pool.instances.forEach(instance => instance.dispose());
    });
    this.instancePools.clear();
  }

  /**
   * Get statistics
   */
  getStats() {
    return {
      ...this.stats,
      bufferCount: this.chainBuffers.size,
      meshCount: this.meshCache.size,
      poolCount: this.instancePools.size
    };
  }
}

// Singleton instance
let gpuBufferInstance = null;

export function getGPUBufferManager(engine) {
  if (!gpuBufferInstance && engine) {
    gpuBufferInstance = new GPUBufferManager(engine);
  }
  return gpuBufferInstance;
}

