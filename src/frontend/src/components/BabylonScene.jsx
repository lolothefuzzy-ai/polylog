import React, { useEffect, useRef, useState } from 'react';
import * as BABYLON from '@babylonjs/core';
import '@babylonjs/loaders';
import { PolyformMesh } from '../utils/PolyformMesh';
import { PolygonInteractionManager } from '../utils/polygonInteraction.js';
import { initializeWorkspace, getWorkspaceEntryPoint } from '../utils/workspaceEntryPoint.js';
import { storageService } from '../services/storageService';
import { visualizeTier0Symbol } from '../utils/tier0Visualizer.js';

export const BabylonScene = ({ selectedPolyhedra = [], selectedAttachment = null, generatedPolyform = null, onPolygonAttached }) => {
  const canvasRef = useRef(null);
  const sceneRef = useRef(null);
  const engineRef = useRef(null);
  const cameraRef = useRef(null);
  const meshesRef = useRef([]);
  const interactionManagerRef = useRef(null);
  const workspaceManagerRef = useRef(null);
  const [lodLevel, setLodLevel] = useState('full');
  const [workspacePolygons, setWorkspacePolygons] = useState([]);

  useEffect(() => {
    if (!canvasRef.current) return;

    // Initialize Babylon.js engine and scene
    const engine = new BABYLON.Engine(canvasRef.current, true, {
      preserveDrawingBuffer: true,
      stencil: true,
      antialias: true
    });
    engineRef.current = engine;

    const scene = new BABYLON.Scene(engine);
    sceneRef.current = scene;
    scene.clearColor = new BABYLON.Color4(0.02, 0.02, 0.05, 1);

    // Camera setup - positioned to see workspace clearly
    const camera = new BABYLON.ArcRotateCamera(
      'camera',
      -Math.PI / 2,
      Math.PI / 3,
      15, // Increased distance to see all polygons
      BABYLON.Vector3.Zero(),
      scene
    );
    camera.attachControl(canvasRef.current, true);
    camera.wheelPrecision = 50;
    camera.lowerRadiusLimit = 3; // Closer minimum
    camera.upperRadiusLimit = 50;
    camera.setTarget(BABYLON.Vector3.Zero()); // Look at origin
    cameraRef.current = camera;
    
    console.log('[BabylonScene] Camera initialized at radius 15');

    // Initialize workspace entry point (unified entry point)
    const workspaceManager = initializeWorkspace(scene);
    workspaceManagerRef.current = workspaceManager;
    
    // Set callback for Tier 0 symbol visualization
    // Visualization can be toggled via Tier0Display component
    const tier0VisualizationRef = { enabled: true }; // Use ref for mutable state
    
    workspaceManager.setOnChainTier0Generated(async (chain, symbol) => {
      console.log(`[BabylonScene] Tier 0 symbol generated: ${symbol} for chain ${chain.id}`);
      
      // Check if visualization is enabled
      if (!tier0VisualizationRef.enabled) {
        return;
      }
      
      // Visualize Tier 0 symbol (optional, can be toggled)
      // Position visualization offset from actual chain
      const visualizationPosition = new BABYLON.Vector3(
        chain.polygonIds.length * 3, // Offset horizontally
        2, // Above workspace
        0
      );
      
      try {
        const tier0Mesh = await visualizeTier0Symbol(symbol, scene, visualizationPosition);
        if (tier0Mesh) {
          // Store reference for cleanup
          if (!meshesRef.current.includes(tier0Mesh)) {
            meshesRef.current.push(tier0Mesh);
            console.log(`[BabylonScene] Visualized Tier 0 symbol: ${symbol}`);
          }
        }
      } catch (error) {
        console.warn(`[BabylonScene] Tier 0 visualization error:`, error);
      }
    });
    
    // Listen for visualization toggle events
    const handleVisualizationToggle = (event) => {
      tier0VisualizationRef.enabled = event.detail.enabled;
      console.log(`[BabylonScene] Tier 0 visualization ${tier0VisualizationRef.enabled ? 'enabled' : 'disabled'}`);
    };
    
    window.addEventListener('tier0-visualization-toggle', handleVisualizationToggle);
    
    // Initialize interaction manager (workspace manager passed for backward compatibility)
    // Interaction manager will use entry point directly for operations
    interactionManagerRef.current = new PolygonInteractionManager(
      scene,
      camera,
      async (attachment) => {
        // Use workspace entry point for attachment
        const workspace = getWorkspaceEntryPoint();
        if (workspace.isInitialized() && attachment.polygonA && attachment.polygonB) {
          await workspace.attachPolygons(
            attachment.polygonA,
            attachment.edgeA || 0,
            attachment.polygonB,
            attachment.edgeB || 0,
            attachment.foldAngle
          );
        }
        if (onPolygonAttached) {
          onPolygonAttached(attachment);
        }
      },
      workspaceManager // Pass for backward compatibility (entry point preferred)
    );

    // Lighting setup
    const light1 = new BABYLON.HemisphericLight(
      'light1',
      new BABYLON.Vector3(1, 1, 0),
      scene
    );
    light1.intensity = 0.7;

    const light2 = new BABYLON.DirectionalLight(
      'light2',
      new BABYLON.Vector3(-1, -2, -1),
      scene
    );
    light2.position = new BABYLON.Vector3(20, 40, 20);
    light2.intensity = 0.5;

    // Grid ground
    const ground = BABYLON.MeshBuilder.CreateGround(
      'ground',
      { width: 20, height: 20, subdivisions: 20 },
      scene
    );
    const groundMaterial = new BABYLON.StandardMaterial('groundMat', scene);
    groundMaterial.diffuseColor = new BABYLON.Color3(0.1, 0.1, 0.15);
    groundMaterial.specularColor = new BABYLON.Color3(0, 0, 0);
    ground.material = groundMaterial;
    ground.position.y = -0.5;

    // Grid lines
    const gridLines = BABYLON.MeshBuilder.CreateLines(
      'gridLines',
      {
        points: [
          new BABYLON.Vector3(-10, -0.49, 0),
          new BABYLON.Vector3(10, -0.49, 0),
          new BABYLON.Vector3(0, -0.49, -10),
          new BABYLON.Vector3(0, -0.49, 10)
        ]
      },
      scene
    );
    gridLines.color = new BABYLON.Color3(0.3, 0.3, 0.4);

    // LOD switching based on camera distance
    scene.registerBeforeRender(() => {
      if (cameraRef.current) {
        const distance = cameraRef.current.radius;
        let newLod = 'full';
        if (distance > 30) newLod = 'thumbnail';
        else if (distance > 20) newLod = 'low';
        else if (distance > 10) newLod = 'medium';
        else newLod = 'full';
        
        if (newLod !== lodLevel) {
          setLodLevel(newLod);
        }
      }
    });

    // Start render loop
    engine.runRenderLoop(() => {
      scene.render();
    });

    // Notify parent that scene is ready
    if (onSceneReady) {
      onSceneReady(scene);
    }

    // Handle resize
    const handleResize = () => {
      engine.resize();
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('tier0-visualization-toggle', handleVisualizationToggle);
      scene.dispose();
      engine.dispose();
    };
  }, []);

  // Load generated polyform when provided
  useEffect(() => {
    if (!generatedPolyform || !sceneRef.current) return;

    const loadGeneratedPolyform = async () => {
      try {
        // Clear existing meshes first
        meshesRef.current.forEach(mesh => mesh.dispose());
        meshesRef.current = [];

        // Create PolyformMesh for the generated polyform
        const polyformMesh = new PolyformMesh(generatedPolyform.unicode, sceneRef.current);
        await polyformMesh.initialize();
        
        // Position the generated polyform
        if (polyformMesh.mesh) {
          polyformMesh.mesh.position = new BABYLON.Vector3(0, 1, 0);
          
          // Apply special material for generated polyforms
          const material = new BABYLON.StandardMaterial('generatedMat', sceneRef.current);
          material.diffuseColor = new BABYLON.Color3(0.8, 0.4, 0.8); // Purple for generated
          material.specularColor = new BABYLON.Color3(0.6, 0.6, 0.8);
          material.emissiveColor = new BABYLON.Color3(0.1, 0.05, 0.1);
          polyformMesh.mesh.material = material;
          
          meshesRef.current.push(polyformMesh.mesh);
        }

        // Also load the original polyhedra for reference
        selectedPolyhedra.forEach((poly, index) => {
          loadPolyhedron(poly, index + 1); // Offset index to avoid collision
        });

      } catch (error) {
        console.error('Failed to load generated polyform:', error);
      }
    };

    loadGeneratedPolyform();
  }, [generatedPolyform, selectedPolyhedra]);

  // Only attempt auto-attachment after 3+ polygons (for closure)
  useEffect(() => {
    if (selectedPolyhedra.length >= 3 && interactionManagerRef.current && sceneRef.current) {
      // Small delay to ensure meshes are loaded and warmed up
      setTimeout(() => {
        interactionManagerRef.current?.attemptAutoAttachment();
      }, 1000); // 1 second delay for warmup
    }
  }, [selectedPolyhedra.length]);

  // Load regular polyhedra when no generated polyform
  useEffect(() => {
    if (generatedPolyform || !sceneRef.current) return;

    const loadPolyhedron = async (poly, index) => {
      try {
        console.log(`[BabylonScene] Loading polyhedron ${poly.symbol} at index ${index}`);
        
        // Try to get LOD geometry first
        let geometry = null;
        try {
          geometry = await storageService.getPolyhedronLOD(poly.symbol, lodLevel);
          console.log(`[BabylonScene] Loaded LOD geometry for ${poly.symbol}:`, geometry.vertices?.length || 0, 'vertices');
        } catch (lodError) {
          console.warn(`[BabylonScene] LOD failed for ${poly.symbol}, trying basic data:`, lodError);
          try {
            // Fallback to basic polyhedron data
            const polyData = await storageService.getPolyhedron(poly.symbol);
            geometry = {
              vertices: polyData.vertices || [],
              indices: polyData.faces || [],
              normals: []
            };
            console.log(`[BabylonScene] Loaded basic geometry for ${poly.symbol}:`, geometry.vertices?.length || 0, 'vertices');
          } catch (polyError) {
            console.warn(`[BabylonScene] Basic data failed for ${poly.symbol}, using fallback:`, polyError);
            // Use fallback geometry (always works)
            geometry = storageService.getFallbackGeometry(poly.symbol);
            console.log(`[BabylonScene] Using fallback geometry for ${poly.symbol}:`, geometry.vertices?.length || 0, 'vertices');
          }
        }

        if (geometry && geometry.vertices && geometry.vertices.length > 0) {
          console.log(`[BabylonScene] Creating mesh for ${poly.symbol}...`);
          // Create mesh from geometry data
          const vertexData = new BABYLON.VertexData();
          
          // Convert vertices to Vector3
          const positions = [];
          geometry.vertices.forEach(vertex => {
            positions.push(...vertex);
          });
          vertexData.positions = new Float32Array(positions);
          
          // Handle indices/faces
          if (geometry.indices && geometry.indices.length > 0) {
            const indices = [];
            geometry.indices.forEach(face => {
              if (Array.isArray(face)) {
                indices.push(...face);
              } else {
                indices.push(face);
              }
            });
            vertexData.indices = new Uint32Array(indices);
          } else {
            // Generate simple indices if not provided
            const indices = [];
            for (let i = 0; i < positions.length / 3 - 2; i++) {
              indices.push(0, i + 1, i + 2);
            }
            vertexData.indices = new Uint32Array(indices);
          }
          
          // Create mesh
          const mesh = new BABYLON.Mesh(`poly_${poly.symbol}`, sceneRef.current);
          vertexData.applyToMesh(mesh);
          
          // Scale mesh to be visible (fallback geometry is small)
          mesh.scaling = new BABYLON.Vector3(2, 2, 2); // Make 2x larger for visibility
          
          // Material - brighter colors for visibility
          const material = new BABYLON.StandardMaterial(`mat_${poly.symbol}`, sceneRef.current);
          material.diffuseColor = new BABYLON.Color3(0.6, 0.6, 0.9); // Brighter blue
          material.specularColor = new BABYLON.Color3(0.7, 0.7, 0.9);
          material.emissiveColor = new BABYLON.Color3(0.1, 0.1, 0.2); // Slight glow
          mesh.material = material;
          
          // Make mesh pickable and visible
          mesh.isPickable = true;
          mesh.isVisible = true;
          mesh.setEnabled(true);
          
          // Position - start in 3D space, native 3D (not flat)
          // Arrange in 3D circular pattern with vertical spacing
          const angle = (index * Math.PI * 2) / Math.max(selectedPolyhedra.length, 1);
          const radius = 3.0; // Slightly larger radius for better visibility
          const height = index * 0.5; // More vertical spacing
          mesh.position = new BABYLON.Vector3(
            Math.cos(angle) * radius,
            height, // Native 3D height
            Math.sin(angle) * radius
          );
          
          // Apply initial 3D rotation (not flat)
          mesh.rotation.x = Math.random() * 0.3 - 0.15; // More visible tilt
          mesh.rotation.y = angle; // Face outward
          mesh.rotation.z = Math.random() * 0.3 - 0.15;
          
          // Enable rotation
          mesh.rotationQuaternion = null; // Use Euler angles for now
          
          // Compute bounding box for interaction
          mesh.refreshBoundingInfo();
          
          // Add to workspace via unified entry point
          const workspace = getWorkspaceEntryPoint();
          if (workspace.isInitialized()) {
            const workspacePolygon = await workspace.addPolygon(
              poly.symbol,
              poly.sides || 4,
              mesh,
              { ...poly, index }
            );
            setWorkspacePolygons(prev => [...prev, workspacePolygon]);
            // Store polygon ID in mesh metadata
            mesh.metadata = { ...poly, polygonId: workspacePolygon.id, sides: poly.sides || 4 };
            console.log(`[BabylonScene] ✓ Added ${poly.symbol} to workspace`);
            
            // Add to interaction manager for drag/drop (use workspace polygon ID)
            if (interactionManagerRef.current) {
              interactionManagerRef.current.addPolygon(
                workspacePolygon.id,
                mesh,
                { symbol: poly.symbol, ...poly, polygonId: workspacePolygon.id }
              );
            }
          }
          
          meshesRef.current.push(mesh);
          console.log(`[BabylonScene] ✓ Successfully added ${poly.symbol} to scene:`);
          console.log(`  Position: (${mesh.position.x.toFixed(2)}, ${mesh.position.y.toFixed(2)}, ${mesh.position.z.toFixed(2)})`);
          console.log(`  Scale: (${mesh.scaling.x.toFixed(2)}, ${mesh.scaling.y.toFixed(2)}, ${mesh.scaling.z.toFixed(2)})`);
          console.log(`  Mesh count: ${meshesRef.current.length}`);
          console.log(`  IsVisible: ${mesh.isVisible}, IsPickable: ${mesh.isPickable}`);
        } else {
          console.error(`[BabylonScene] ✗ No geometry data for ${poly.symbol}`);
        }
      } catch (error) {
        console.error(`[BabylonScene] ✗ Failed to load polyhedron ${poly.symbol}:`, error);
        // Try fallback geometry as last resort
        try {
          console.log(`[BabylonScene] Attempting fallback geometry for ${poly.symbol}...`);
          const fallbackGeometry = storageService.getFallbackGeometry(poly.symbol);
          if (fallbackGeometry && fallbackGeometry.vertices && fallbackGeometry.vertices.length > 0) {
            const vertexData = new BABYLON.VertexData();
            const positions = [];
            fallbackGeometry.vertices.forEach(vertex => {
              positions.push(...vertex);
            });
            vertexData.positions = new Float32Array(positions);
            
            if (fallbackGeometry.indices && fallbackGeometry.indices.length > 0) {
              vertexData.indices = new Uint32Array(fallbackGeometry.indices);
            }
            
            const mesh = new BABYLON.Mesh(`poly_${poly.symbol}_fallback`, sceneRef.current);
            vertexData.applyToMesh(mesh);
            
            // Scale fallback mesh to be visible
            mesh.scaling = new BABYLON.Vector3(2, 2, 2);
            
            const material = new BABYLON.StandardMaterial(`mat_${poly.symbol}_fallback`, sceneRef.current);
            material.diffuseColor = new BABYLON.Color3(0.7, 0.7, 1.0); // Brighter for fallback
            material.emissiveColor = new BABYLON.Color3(0.15, 0.15, 0.25);
            mesh.material = material;
            
            // Make pickable and visible
            mesh.isPickable = true;
            mesh.isVisible = true;
            mesh.setEnabled(true);
            
            const angle = (index * Math.PI * 2) / Math.max(selectedPolyhedra.length, 1);
            const radius = 3.0;
            const height = index * 0.5;
            mesh.position = new BABYLON.Vector3(
              Math.cos(angle) * radius,
              height,
              Math.sin(angle) * radius
            );
            
            mesh.rotationQuaternion = null;
            mesh.refreshBoundingInfo();
            
            // Add to workspace via unified entry point
            const workspace = getWorkspaceEntryPoint();
            if (workspace.isInitialized()) {
              const workspacePolygon = await workspace.addPolygon(
                poly.symbol,
                poly.sides || 4,
                mesh,
                { ...poly, index }
              );
              setWorkspacePolygons(prev => [...prev, workspacePolygon]);
              // Store polygon ID in mesh metadata
              mesh.metadata = { ...poly, polygonId: workspacePolygon.id, sides: poly.sides || 4 };
              
              // Add to interaction manager
              if (interactionManagerRef.current) {
                interactionManagerRef.current.addPolygon(
                  workspacePolygon.id,
                  mesh,
                  { symbol: poly.symbol, ...poly, polygonId: workspacePolygon.id }
                );
              }
              console.log(`[BabylonScene] ✓ Added ${poly.symbol} to workspace (fallback)`);
            }
            
            meshesRef.current.push(mesh);
            console.log(`[BabylonScene] ✓ Added fallback mesh for ${poly.symbol}`);
            console.log(`  Position: (${mesh.position.x.toFixed(2)}, ${mesh.position.y.toFixed(2)}, ${mesh.position.z.toFixed(2)})`);
            console.log(`  IsVisible: ${mesh.isVisible}, IsPickable: ${mesh.isPickable}`);
          }
        } catch (fallbackError) {
          console.error(`[BabylonScene] ✗ Even fallback failed for ${poly.symbol}:`, fallbackError);
        }
      }
    };

    // Clear existing meshes
    meshesRef.current.forEach(mesh => mesh.dispose());
    meshesRef.current = [];

    // Load new polyhedra
    selectedPolyhedra.forEach((poly, index) => {
      loadPolyhedron(poly, index);
    });
  }, [selectedPolyhedra, lodLevel, generatedPolyform]);

  // Handle drop from library
  useEffect(() => {
    if (!canvasRef.current) return;

    const handleDrop = (e) => {
      e.preventDefault();
      const polyData = e.dataTransfer.getData('application/json');
      if (polyData) {
        try {
          const poly = JSON.parse(polyData);
          if (onPolygonAttached) {
            // Trigger selection which will add to workspace
            onPolygonAttached({ type: 'drop', polygon: poly });
          }
        } catch (err) {
          console.error('Failed to parse dropped polygon:', err);
        }
      }
    };

    const handleDragOver = (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
    };

    const canvas = canvasRef.current;
    canvas.addEventListener('drop', handleDrop);
    canvas.addEventListener('dragover', handleDragOver);

    return () => {
      canvas.removeEventListener('drop', handleDrop);
      canvas.removeEventListener('dragover', handleDragOver);
    };
  }, [onPolygonAttached]);

  return (
    <div className="babylon-container">
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', display: 'block' }}
      />
      <div className="scene-overlay">
        <div className="lod-indicator">LOD: {lodLevel}</div>
        <div className="polyhedra-count">
          {generatedPolyform ? 'Generated polyform loaded' : `${selectedPolyhedra.length} polyhedra loaded`}
        </div>
        {generatedPolyform && (
          <div className="generated-info">
            <div>Composition: {generatedPolyform.composition}</div>
            <div>Compression: {(generatedPolyform.compressionRatio || 0).toFixed(2)}x</div>
          </div>
        )}
      </div>
    </div>
  );
};