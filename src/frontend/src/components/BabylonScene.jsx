import React, { useEffect, useRef } from 'react';
import * as BABYLON from '@babylonjs/core';
import '@babylonjs/loaders';
import { PolyformMesh } from '../utils/PolyformMesh';

export const BabylonScene = () => {
  const canvasRef = useRef(null);
  const sceneRef = useRef(null);
  const engineRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    // Initialize Babylon.js engine and scene
    const engine = new BABYLON.Engine(canvasRef.current, true, {
      preserveDrawingBuffer: true,
      stencil: true
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

    // Test polyform - will be replaced with polyform later
    const testPolyform = new PolyformMesh('A', scene); // Triangle
    testPolyform.initialize().then(() => {
      const mesh = testPolyform.getMesh();
      if (mesh) {
        mesh.setPosition(new BABYLON.Vector3(0, 0.5, 0));
      }
    }).catch(error => {
      console.error('Failed to initialize polyform mesh:', error);
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
      scene.dispose();
      engine.dispose();
    };
  }, []);

  return (
    <div className="babylon-container">
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', display: 'block' }}
      />
    </div>
  );
};
