import React, { useEffect, useRef, useState } from 'react';
import * as BABYLON from '@babylonjs/core';
import '@babylonjs/loaders';
import { PolyformMesh } from '../utils/PolyformMesh';
import { storageService } from '../services/storageService';

export const BabylonScene = ({ selectedPolyhedra = [], selectedAttachment = null }) => {
  const canvasRef = useRef(null);
  const sceneRef = useRef(null);
  const engineRef = useRef(null);
  const cameraRef = useRef(null);
  const meshesRef = useRef([]);
  const [lodLevel, setLodLevel] = useState('full');

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

    // Render loop
    engine.runRenderLoop(() => {
      scene.render();
    });

    // Handle window resize
    const handleResize = () => {
      engine.resize();
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      meshesRef.current.forEach(mesh => mesh.dispose());
      meshesRef.current = [];
      scene.dispose();
      engine.dispose();
    };
  }, []);

  // Load polyhedra when selected
  useEffect(() => {
    if (!sceneRef.current || selectedPolyhedra.length === 0) return;

    const loadPolyhedron = async (poly, index) => {
      try {
        let data;
        
        // Check if it's a generated polyform with geometry
        if (poly.geometry) {
          data = poly.geometry.lod?.[lodLevel] || poly.geometry.lod?.full;
        } else {
          // Regular polyhedron lookup
          data = await storageService.getPolyhedronLOD(poly.symbol, lodLevel);
        }
        
        if (data && data.vertices) {
          // Create mesh from vertices
          const vertices = data.vertices.map(v => new BABYLON.Vector3(v[0], v[1], v[2] || 0));
          
          // Create custom mesh
          const mesh = new BABYLON.Mesh(`polyhedron_${poly.symbol}_${index}`, sceneRef.current);
          
          // Create vertex data
          const vertexData = new BABYLON.VertexData();
          vertexData.positions = vertices.flatMap(v => [v.x, v.y, v.z]);
          
          // Use provided indices or simple triangulation
          if (data.indices && data.indices.length > 0) {
            vertexData.indices = data.indices;
          } else {
            const indices = [];
            for (let i = 1; i < vertices.length - 1; i++) {
              indices.push(0, i, i + 1);
            }
            vertexData.indices = indices;
          }
          
          vertexData.applyToMesh(mesh);
          
          // Material - different color for generated polyforms
          const material = new BABYLON.StandardMaterial(`mat_${poly.symbol}`, sceneRef.current);
          if (poly.classification === 'generated') {
            material.diffuseColor = new BABYLON.Color3(0.8, 0.4, 0.8); // Purple for generated
          } else {
            material.diffuseColor = new BABYLON.Color3(0.4, 0.4, 0.8);
          }
          material.specularColor = new BABYLON.Color3(0.5, 0.5, 0.5);
          mesh.material = material;
          
          // Position
          mesh.position = new BABYLON.Vector3(index * 3, 0.5, 0);
          
          meshesRef.current.push(mesh);
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
  }, [selectedPolyhedra, lodLevel]);

  return (
    <div className="babylon-container">
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', display: 'block' }}
      />
      <div className="scene-overlay">
        <div className="lod-indicator">LOD: {lodLevel}</div>
        <div className="polyhedra-count">
          {selectedPolyhedra.length} polyhedra loaded
        </div>
      </div>
    </div>
  );
};
