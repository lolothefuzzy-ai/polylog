import React, { useEffect, useRef, useState } from 'react';
import * as BABYLON from '@babylonjs/core';
import '@babylonjs/loaders';
import { PolyformMesh } from '../utils/PolyformMesh';
import { PolygonInteractionManager } from '../utils/polygonInteraction.js';
import { storageService } from '../services/storageService';

export const BabylonScene = ({ selectedPolyhedra = [], selectedAttachment = null, generatedPolyform = null, onPolygonAttached }) => {
  const canvasRef = useRef(null);
  const sceneRef = useRef(null);
  const engineRef = useRef(null);
  const cameraRef = useRef(null);
  const meshesRef = useRef([]);
  const interactionManagerRef = useRef(null);
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

    // Camera setup
    const camera = new BABYLON.ArcRotateCamera(
      'camera',
      -Math.PI / 2,
      Math.PI / 3,
      10,
      BABYLON.Vector3.Zero(),
      scene
    );
    camera.attachControl(canvasRef.current, true);
    camera.wheelPrecision = 50;
    camera.lowerRadiusLimit = 2;
    camera.upperRadiusLimit = 50;
    cameraRef.current = camera;

    // Initialize interaction manager
    interactionManagerRef.current = new PolygonInteractionManager(
      scene,
      camera,
      (attachment) => {
        if (onPolygonAttached) {
          onPolygonAttached(attachment);
        }
      }
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

    // Handle resize
    const handleResize = () => {
      engine.resize();
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
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
      }, 1000);
    }
  }, [selectedPolyhedra.length]);

  // Load regular polyhedra when no generated polyform
  useEffect(() => {
    if (generatedPolyform || !sceneRef.current) return;

    const loadPolyhedron = async (poly, index) => {
      try {
        // Try to get LOD geometry first
        let geometry = null;
        try {
          geometry = await storageService.getPolyhedronLOD(poly.symbol, lodLevel);
        } catch (lodError) {
          // Fallback to basic polyhedron data
          const polyData = await storageService.getPolyhedron(poly.symbol);
          geometry = {
            vertices: polyData.vertices || [],
            indices: polyData.faces || [],
            normals: []
          };
        }

        if (geometry && geometry.vertices && geometry.vertices.length > 0) {
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
          
          // Material
          const material = new BABYLON.StandardMaterial(`mat_${poly.symbol}`, sceneRef.current);
          material.diffuseColor = new BABYLON.Color3(0.4, 0.4, 0.8);
          material.specularColor = new BABYLON.Color3(0.5, 0.5, 0.5);
          mesh.material = material;
          
          // Position - start in 3D space, not flat
          const angle = (index * Math.PI * 2) / Math.max(selectedPolyhedra.length, 1);
          const radius = 2;
          mesh.position = new BABYLON.Vector3(
            Math.cos(angle) * radius,
            0.5 + index * 0.1, // Slight vertical offset
            Math.sin(angle) * radius
          );
          
          // Enable rotation
          mesh.rotationQuaternion = BABYLON.Quaternion.Identity();
          
          meshesRef.current.push(mesh);
          
          // Add to interaction manager for drag/drop
          if (interactionManagerRef.current) {
            interactionManagerRef.current.addPolygon(
              `poly_${poly.symbol}_${index}`,
              mesh,
              { symbol: poly.symbol, ...poly }
            );
          }
        }
      } catch (error) {
        console.error(`Failed to load polyhedron ${poly.symbol}:`, error);
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