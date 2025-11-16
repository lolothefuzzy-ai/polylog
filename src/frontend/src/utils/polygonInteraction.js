/**
 * Polygon interaction system for drag, drop, and 3D manipulation
 */

import * as BABYLON from '@babylonjs/core';
import { EdgeSnapper } from './edgeSnapping.js';
import { SnapVisualFeedback } from './snapVisualFeedback.js';
import { getFoldAngleFromBackend } from './geometryUtils.js';
import { getWorkspaceEntryPoint } from './workspaceEntryPoint.js';

export class PolygonInteractionManager {
  constructor(scene, camera, onAttachment, workspaceManager = null) {
    this.scene = scene;
    this.camera = camera;
    this.onAttachment = onAttachment;
    this.workspaceManager = workspaceManager; // Optional workspace manager for chain movement
    this.meshes = new Map(); // polygonId -> mesh
    this.dragging = null;
    this.snapGuide = null;
    this.openEdges = new Map(); // polygonId -> Set<edgeIndex>
    this.visualFeedback = new SnapVisualFeedback(scene);
    this.rotationEnabled = true;
    this.pointerObserver = null;
    this.isDragging = false; // Global drag state
    this.dragStartPosition = null; // Track start position for delta calculation
    
    // Set up global pointer observer once
    this.setupGlobalPointerObserver();
  }
  
  /**
   * Set up global pointer observer (called once)
   */
  setupGlobalPointerObserver() {
    if (this.pointerObserver) return; // Already set up
    
    this.pointerObserver = this.scene.onPointerObservable.add((pointerInfo) => {
      if (pointerInfo.type === BABYLON.PointerEventTypes.POINTERMOVE && this.isDragging && this.dragging) {
        // Create picking ray from mouse position
        const pickInfo = this.scene.pick(
          pointerInfo.event.offsetX,
          pointerInfo.event.offsetY,
          (mesh) => mesh === this.dragging.mesh || mesh.name === 'ground'
        );
        
        if (pickInfo && pickInfo.pickedPoint) {
          // Calculate delta from start position
          if (!this.dragStartPosition) {
            this.dragStartPosition = this.dragging.mesh.position.clone();
          }
          const newPosition = pickInfo.pickedPoint.add(this.dragging.offset);
          const delta = newPosition.subtract(this.dragging.mesh.position);
          
          // Use workspace entry point for chain movement (preferred)
          const workspace = getWorkspaceEntryPoint();
          if (workspace.isInitialized() && this.dragging.polygonId) {
            workspace.movePolygon(this.dragging.polygonId, delta);
          } else if (this.workspaceManager && this.dragging.polygonId) {
            // Fallback: direct workspace manager
            this.workspaceManager.movePolygon(this.dragging.polygonId, delta);
          } else {
            // Fallback: direct mesh movement
            this.dragging.mesh.position = newPosition;
          }
          
          // Check for snap candidates
          const otherMeshes = Array.from(this.meshes.values()).filter(m => m !== this.dragging.mesh);
          const candidates = EdgeSnapper.findSnapCandidates(this.dragging.mesh, otherMeshes);
          
          if (candidates.length > 0) {
            this.snapGuide = candidates[0];
            // Show visual feedback
            this.visualFeedback.highlightSnapZones(otherMeshes, candidates);
          } else {
            this.snapGuide = null;
            this.visualFeedback.clearGuides();
          }

          // Enable free rotation with Shift key
          if (this.rotationEnabled && pointerInfo.event.shiftKey) {
            const deltaX = pointerInfo.event.movementX || 0;
            const deltaY = pointerInfo.event.movementY || 0;
            const rotationX = deltaY * 0.01;
            const rotationY = deltaX * 0.01;
            
            // Apply rotation
            this.dragging.mesh.rotation.x += rotationX;
            this.dragging.mesh.rotation.y += rotationY;
            
            this.visualFeedback.showRotationFeedback(this.dragging.mesh, rotationY);
          }
        }
      }
      
      if (pointerInfo.type === BABYLON.PointerEventTypes.POINTERUP && this.isDragging) {
        console.log(`[Interaction] Stopped dragging ${this.dragging?.polygonId}`);
        this.isDragging = false;
        this.dragStartPosition = null; // Reset drag start
        
        // Restore normal emissive color
        if (this.dragging && this.dragging.mesh.material) {
          this.dragging.mesh.material.emissiveColor = new BABYLON.Color3(0.1, 0.1, 0.2);
        }
        
        if (this.snapGuide && this.dragging) {
          // Apply snap/attachment
          console.log(`[Interaction] Applying attachment for ${this.dragging.polygonId}`);
          // Get fold angle from backend
          const sidesA = this.snapGuide.targetMesh.metadata?.sides || 4;
          const sidesB = this.dragging.mesh.metadata?.sides || 4;
          const foldAngle = await getFoldAngleFromBackend(sidesA, sidesB) || 0;
          await this.applyAttachment(
            this.snapGuide.targetMesh,
            this.dragging.mesh,
            this.snapGuide,
            foldAngle
          );
        }
        this.dragging = null;
        this.snapGuide = null;
        this.visualFeedback.clearGuides();
      }
    });
  }

  /**
   * Add polygon to workspace
   */
  addPolygon(polygonId, mesh, metadata) {
    mesh.metadata = metadata;
    this.meshes.set(polygonId, mesh);
    
    // Initialize open edges (all edges start open)
    const vertexCount = mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind).length / 3;
    this.openEdges.set(polygonId, new Set(Array.from({ length: vertexCount }, (_, i) => i)));
    
    // Enable picking
    mesh.enablePointerMoveEvents = true;
    mesh.actionManager = new BABYLON.ActionManager(this.scene);
    
    // Set up drag handlers
    this.setupDragHandlers(mesh, polygonId);
    
    // If this is the second polygon, attempt auto-attachment
    if (this.meshes.size === 2) {
      this.attemptAutoAttachment();
    }
  }

  /**
   * Attempt automatic attachment when second polygon is added
   */
  async attemptAutoAttachment() {
    const polygonIds = Array.from(this.meshes.keys());
    if (polygonIds.length < 2) return;

    const polyAId = polygonIds[0];
    const polyBId = polygonIds[1];
    const meshA = this.meshes.get(polyAId);
    const meshB = this.meshes.get(polyBId);

    // Find best attachment option
    const candidates = EdgeSnapper.findSnapCandidates(meshB, [meshA]);
    if (candidates.length === 0) return;

    const bestCandidate = candidates[0];
    
    // Get attachment sequence from API
    try {
      const symbolA = meshA.metadata?.symbol || 'A';
      const symbolB = meshB.metadata?.symbol || 'B';
      
      const response = await fetch('http://localhost:8000/api/attachment/sequence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          polygonA: symbolA,
          polygonB: symbolB,
          scaler: 1.0
        })
      });
      
      const data = await response.json();
      if (data.success && data.stability >= 0.7) {
        // Apply attachment with fold angle from sequence
        const foldAngle = (data.fold_angle || 0) * (Math.PI / 180); // Convert to radians
        this.applyAttachment(meshA, meshB, bestCandidate, foldAngle);
      }
    } catch (error) {
      console.error('Auto-attachment failed:', error);
    }
  }

  /**
   * Apply attachment between two meshes
   */
  async applyAttachment(meshA, meshB, candidate, foldAngle) {
    // Calculate snap transform
    const movingEdge = {
      start: meshB.position,
      end: meshB.position.clone().add(BABYLON.Vector3.Right()),
      midpoint: meshB.position
    };
    
    const transform = EdgeSnapper.calculateSnapTransform(
      movingEdge,
      candidate.targetEdge,
      foldAngle
    );
    
    // Apply transform
    meshB.position.addInPlace(transform.position);
    meshB.rotationQuaternion = transform.rotation;
    
    // Get polygon IDs from mesh metadata or fallback to lookup
    const polyAId = meshA.metadata?.polygonId || Array.from(this.meshes.entries()).find(([_, m]) => m === meshA)?.[0];
    const polyBId = meshB.metadata?.polygonId || Array.from(this.meshes.entries()).find(([_, m]) => m === meshB)?.[0];
    
    // Get edge indices from candidate
    const edgeAIndex = candidate.targetEdge?.index || 0;
    const edgeBIndex = 0; // Moving polygon's first edge (simplified)
    
    if (polyAId && polyBId) {
      // Remove attached edges from open edges
      const openA = this.openEdges.get(polyAId);
      const openB = this.openEdges.get(polyBId);
      if (openA) openA.delete(edgeAIndex);
      if (openB) openB.delete(edgeBIndex);
    }
    
    // Notify callback with proper IDs
    if (this.onAttachment) {
      this.onAttachment({
        polygonA: polyAId,
        polygonB: polyBId,
        edgeA: edgeAIndex,
        edgeB: edgeBIndex,
        foldAngle: foldAngle,
        transform: transform
      });
    }
  }

  /**
   * Set up drag handlers for a mesh
   */
  setupDragHandlers(mesh, polygonId) {
    // Ensure mesh is pickable
    mesh.isPickable = true;
    
    // Create action manager if it doesn't exist
    if (!mesh.actionManager) {
      mesh.actionManager = new BABYLON.ActionManager(this.scene);
    }

    // On click/pick down - start dragging
    mesh.actionManager.registerAction(
      new BABYLON.ExecuteCodeAction(BABYLON.ActionManager.OnPickDownTrigger, (evt) => {
        console.log(`[Interaction] Started dragging ${polygonId}`);
        this.isDragging = true;
        this.dragStartPosition = mesh.position.clone();
        const dragStart = evt.pickedPoint.clone();
        const dragOffset = mesh.position.subtract(dragStart);
        this.dragging = { mesh, polygonId, start: dragStart, offset: dragOffset };
        
        // Highlight mesh being dragged
        if (mesh.material) {
          mesh.material.emissiveColor = new BABYLON.Color3(0.3, 0.3, 0.5);
        }
      })
    );
  }
}

