/**
 * Tier 0 Visualizer
 * Converts Tier 0 symbols to Babylon.js meshes for visualization
 * Unified visualization pipeline for Tier 0 symbols
 */

import * as BABYLON from '@babylonjs/core';
import { decodeTier0Symbol } from '../services/tier0Service.js';
import { generatePolygonVertices } from './geometryUtils.js';

/**
 * Visualize Tier 0 symbol as Babylon.js mesh
 * @param {string} symbol - Tier 0 symbol (e.g., "A11", "B11")
 * @param {BABYLON.Scene} scene - Babylon.js scene
 * @param {BABYLON.Vector3} position - Position for the chain
 * @returns {Promise<BABYLON.Mesh>} Babylon.js mesh representing the chain
 */
export async function visualizeTier0Symbol(symbol, scene, position = BABYLON.Vector3.Zero()) {
  try {
    // Decode Tier 0 symbol to get polygon sequence
    const decoded = await decodeTier0Symbol(symbol);
    
    if (!decoded || !decoded.polygons || decoded.polygons.length === 0) {
      console.warn(`[Tier0Visualizer] Could not decode symbol: ${symbol}`);
      return null;
    }
    
    const polygonSequence = decoded.polygons;
    
    // Create mesh for the chain
    const chainMesh = new BABYLON.Mesh(`tier0_${symbol}`, scene);
    
    // Generate geometry for each polygon in sequence
    const allVertices = [];
    const allIndices = [];
    let vertexOffset = 0;
    
    for (let i = 0; i < polygonSequence.length; i++) {
      const sides = polygonSequence[i];
      
      // Generate vertices for this polygon
      const polygonVertices = await generatePolygonVertices(
        sides,
        position.add(new BABYLON.Vector3(i * 2.5, 0, 0)), // Space polygons horizontally
        0, // No rotation initially
        true // Use backend geometry
      );
      
      // Add vertices to combined array
      polygonVertices.forEach(v => {
        allVertices.push(v.x, v.y, v.z);
      });
      
      // Generate indices (fan triangulation)
      const polygonVertexCount = polygonVertices.length;
      for (let j = 1; j < polygonVertexCount - 1; j++) {
        allIndices.push(
          vertexOffset,
          vertexOffset + j,
          vertexOffset + j + 1
        );
      }
      
      vertexOffset += polygonVertexCount;
    }
    
    // Create vertex data
    const vertexData = new BABYLON.VertexData();
    vertexData.positions = new Float32Array(allVertices);
    vertexData.indices = new Uint32Array(allIndices);
    
    // Calculate normals
    BABYLON.VertexData.ComputeNormals(
      vertexData.positions,
      vertexData.indices,
      new Float32Array(allVertices.length)
    );
    
    // Apply to mesh
    vertexData.applyToMesh(chainMesh);
    
    // Create material
    const material = new BABYLON.StandardMaterial(`tier0_${symbol}_mat`, scene);
    material.diffuseColor = new BABYLON.Color3(0.6, 0.7, 0.9);
    material.specularColor = new BABYLON.Color3(0.5, 0.5, 0.7);
    material.emissiveColor = new BABYLON.Color3(0.1, 0.1, 0.2);
    chainMesh.material = material;
    
    // Store metadata
    chainMesh.metadata = {
      tier0Symbol: symbol,
      polygonSequence: polygonSequence,
      chainLength: polygonSequence.length,
      edgeSignature: decoded.edge_signature || polygonSequence.join('-')
    };
    
    console.log(`[Tier0Visualizer] Visualized ${symbol}: ${polygonSequence.length} polygons`);
    
    return chainMesh;
  } catch (error) {
    console.error(`[Tier0Visualizer] Error visualizing ${symbol}:`, error);
    return null;
  }
}

/**
 * Visualize atomic chain
 * @param {Object} atomicChain - Atomic chain data from API
 * @param {BABYLON.Scene} scene - Babylon.js scene
 * @param {BABYLON.Vector3} position - Position for the chain
 * @returns {Promise<BABYLON.Mesh>} Babylon.js mesh
 */
export async function visualizeAtomicChain(atomicChain, scene, position = BABYLON.Vector3.Zero()) {
  if (!atomicChain || !atomicChain.symbol) {
    return null;
  }
  
  const mesh = await visualizeTier0Symbol(atomicChain.symbol, scene, position);
  
  if (mesh) {
    // Apply special styling based on chain type
    const material = mesh.material;
    if (atomicChain.chain_type === 'square_chain') {
      material.diffuseColor = new BABYLON.Color3(0.7, 0.8, 0.6); // Green tint
    } else if (atomicChain.chain_type === 'triangle_cluster') {
      material.diffuseColor = new BABYLON.Color3(0.8, 0.6, 0.7); // Pink tint
    } else if (atomicChain.chain_type === 'mixed_chain') {
      material.diffuseColor = new BABYLON.Color3(0.7, 0.7, 0.8); // Blue tint
    }
    
    mesh.metadata.atomicChainType = atomicChain.chain_type;
    mesh.metadata.scaffoldApplications = atomicChain.scaffold_applications;
  }
  
  return mesh;
}

/**
 * Visualize scaffold
 * @param {Object} scaffold - Scaffold data from API
 * @param {BABYLON.Scene} scene - Babylon.js scene
 * @param {BABYLON.Vector3} position - Position for the scaffold
 * @returns {Promise<Array<BABYLON.Mesh>>} Array of meshes
 */
export async function visualizeScaffold(scaffold, scene, position = BABYLON.Vector3.Zero()) {
  if (!scaffold || !scaffold.atomic_chains) {
    return [];
  }
  
  const meshes = [];
  
  for (let i = 0; i < scaffold.atomic_chains.length; i++) {
    const chainSymbol = scaffold.atomic_chains[i];
    const chainPosition = position.add(new BABYLON.Vector3(i * 3, 0, 0));
    
    const mesh = await visualizeTier0Symbol(chainSymbol, scene, chainPosition);
    if (mesh) {
      // Apply scaffold styling
      mesh.material.diffuseColor = new BABYLON.Color3(0.9, 0.7, 0.5); // Orange tint
      mesh.metadata.scaffoldSymbol = scaffold.scaffold_symbol;
      mesh.metadata.targetPolyformType = scaffold.target_polyform_type;
      
      meshes.push(mesh);
    }
  }
  
  return meshes;
}

