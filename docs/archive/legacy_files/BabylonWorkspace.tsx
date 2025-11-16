/**
 * Babylon.js Workspace for Polylog6
 * 
 * Foundation milestone: Polygon slider + drag-drop + attachment validation
 */

import { useEffect, useRef, useState } from 'react';
import * as BABYLON from '@babylonjs/core';
import { GridMaterial } from '@babylonjs/materials/grid';
import '@babylonjs/loaders';
import { createPolygonMesh as createPrecisePolygon } from '@/lib/precisePolygonGeometry';
import { findSnapCandidates, highlightEdge, removeHighlight, calculateSnapTransform, extractEdges, type SnapCandidate } from '@/lib/edgeSnappingBabylon';

interface BabylonWorkspaceProps {
  selectedPolygonSides: number | null;
  placeTrigger: number;  // Increments when user clicks Place button
}

export default function BabylonWorkspace({ selectedPolygonSides, placeTrigger }: BabylonWorkspaceProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<BABYLON.Engine | null>(null);
  const sceneRef = useRef<BABYLON.Scene | null>(null);
  const [isReady, setIsReady] = useState(false);
  
  // Drag and snap state
  const draggedMeshRef = useRef<BABYLON.Mesh | null>(null);
  const edgeHighlightRef = useRef<BABYLON.LinesMesh | null>(null);
  const allPolygonsRef = useRef<BABYLON.Mesh[]>([]);
  const currentSnapCandidateRef = useRef<SnapCandidate | null>(null);

  // Watch placeTrigger and create polygon when it changes
  useEffect(() => {
    if (placeTrigger > 0 && selectedPolygonSides && sceneRef.current) {
      handlePlacePolygon();
    }
  }, [placeTrigger, selectedPolygonSides]);

  useEffect(() => {
    if (!canvasRef.current) return;

    // Create Babylon.js engine
    const engine = new BABYLON.Engine(canvasRef.current, true, {
      preserveDrawingBuffer: true,
      stencil: true,
      antialias: true
    });
    engineRef.current = engine;

    // Create scene
    const scene = new BABYLON.Scene(engine);
    scene.clearColor = new BABYLON.Color4(0.95, 0.95, 0.98, 1);
    sceneRef.current = scene;

    // Camera - CAD-style navigation
    const camera = new BABYLON.ArcRotateCamera(
      'camera',
      -Math.PI / 2,  // Alpha: side view
      Math.PI / 3,   // Beta: 60° from top
      25,            // Radius: distance from target
      new BABYLON.Vector3(0, 0, 0),  // Target: origin
      scene
    );
    
    // Enable CAD-style controls
    camera.attachControl(canvasRef.current, true);
    camera.panningSensibility = 50;  // Pan sensitivity
    camera.wheelPrecision = 10;      // Zoom sensitivity
    camera.pinchPrecision = 50;      // Touch zoom
    camera.lowerRadiusLimit = 5;     // Min zoom
    camera.upperRadiusLimit = 100;   // Max zoom
    camera.lowerBetaLimit = 0.1;     // Prevent flipping
    camera.upperBetaLimit = Math.PI / 2 - 0.1;  // Keep above ground
    
    // Enable panning with middle mouse or Ctrl+Left mouse
    camera.panningAxis = new BABYLON.Vector3(1, 0, 1);  // Pan on XZ plane
    camera.panningInertia = 0.5;

    // Lighting
    const hemisphericLight = new BABYLON.HemisphericLight(
      'hemiLight',
      new BABYLON.Vector3(0, 1, 0),
      scene
    );
    hemisphericLight.intensity = 0.7;

    const directionalLight = new BABYLON.DirectionalLight(
      'dirLight',
      new BABYLON.Vector3(-1, -2, -1),
      scene
    );
    directionalLight.position = new BABYLON.Vector3(10, 20, 10);
    directionalLight.intensity = 0.5;

    // Ground plane (2D base)
    const ground = BABYLON.MeshBuilder.CreateGround(
      'ground',
      { width: 30, height: 30, subdivisions: 30 },
      scene
    );
    const groundMaterial = new BABYLON.StandardMaterial('groundMat', scene);
    groundMaterial.diffuseColor = new BABYLON.Color3(0.9, 0.9, 0.95);
    groundMaterial.specularColor = new BABYLON.Color3(0.1, 0.1, 0.1);
    groundMaterial.wireframe = true;
    groundMaterial.alpha = 0.3;
    ground.material = groundMaterial;

    // Grid helper
    const gridMaterial = new GridMaterial('gridMat', scene);
    gridMaterial.majorUnitFrequency = 1;
    gridMaterial.minorUnitVisibility = 0.3;
    gridMaterial.gridRatio = 1;
    gridMaterial.backFaceCulling = false;
    gridMaterial.mainColor = new BABYLON.Color3(0.6, 0.6, 0.8);
    gridMaterial.lineColor = new BABYLON.Color3(0.7, 0.7, 0.9);
    gridMaterial.opacity = 0.5;
    ground.material = gridMaterial;

    // Test box removed - polygons now visible

    // Pointer event handlers for drag-and-drop
    let startingPoint: BABYLON.Vector3 | null = null;
    let currentMesh: BABYLON.Mesh | null = null;

    const getGroundPosition = () => {
      const pickInfo = scene.pick(scene.pointerX, scene.pointerY, (mesh) => mesh.name === 'ground');
      if (pickInfo?.hit) {
        return pickInfo.pickedPoint;
      }
      return null;
    };

    scene.onPointerDown = (evt) => {
      // Only handle left click for dragging
      if (evt.button !== 0) return;
      
      const pickInfo = scene.pick(scene.pointerX, scene.pointerY, (mesh) => {
        return mesh.name.startsWith('polygon-');
      });
      
      if (pickInfo?.hit && pickInfo.pickedMesh) {
        currentMesh = pickInfo.pickedMesh as BABYLON.Mesh;
        draggedMeshRef.current = currentMesh;
        startingPoint = getGroundPosition();
        
        // Disable camera rotation during drag
        camera.detachControl();
        
        console.log('Started dragging:', currentMesh.name);
      }
    };

    scene.onPointerMove = () => {
      if (!currentMesh || !startingPoint) return;
      
      const current = getGroundPosition();
      if (!current) return;
      
      const diff = current.subtract(startingPoint);
      currentMesh.position.addInPlace(diff);
      startingPoint = current;
      
      // Check for snap candidates
      const candidates = findSnapCandidates(
        currentMesh,
        allPolygonsRef.current.filter(m => m !== currentMesh)
      );
      
      // Remove old highlight
      if (edgeHighlightRef.current) {
        removeHighlight(edgeHighlightRef.current);
        edgeHighlightRef.current = null;
      }
      
      // Highlight closest snap target and apply rotation
      if (candidates.length > 0) {
        const best = candidates[0];
        currentSnapCandidateRef.current = best;  // Store for snap-on-release
        
        edgeHighlightRef.current = highlightEdge(
          best.targetEdge,
          scene,
          new BABYLON.Color3(0, 1, 0)  // Green
        );
        
        // Use the moving edge from the snap candidate
        const snapTransform = calculateSnapTransform(best.movingEdge, best.targetEdge);
        
        // Initialize rotationQuaternion if not set
        if (!currentMesh.rotationQuaternion) {
          currentMesh.rotationQuaternion = BABYLON.Quaternion.Identity();
        }
        
        // Apply rotation to align edges
        currentMesh.rotationQuaternion = snapTransform.rotation;
        
        console.log('Snap candidate found:', best.distance.toFixed(2), 'units away - rotating to align edges', best.movingEdgeIndex, '→', best.targetEdgeIndex);
      } else {
        currentSnapCandidateRef.current = null;  // Clear when no candidates
      }
    };

    scene.onPointerUp = () => {
      if (currentMesh) {
        console.log('Stopped dragging:', currentMesh.name);
        
        // Snap-on-release: if valid snap candidate exists, move to exact position
        if (currentSnapCandidateRef.current) {
          const snapCandidate = currentSnapCandidateRef.current;
          const snapTransform = calculateSnapTransform(
            snapCandidate.movingEdge,
            snapCandidate.targetEdge
          );
          
          // Apply position to align edge midpoints
          currentMesh.position = snapTransform.position.clone();
          
          // Rotation already applied during drag, ensure it's set
          if (!currentMesh.rotationQuaternion) {
            currentMesh.rotationQuaternion = BABYLON.Quaternion.Identity();
          }
          currentMesh.rotationQuaternion = snapTransform.rotation;
          
          console.log('SNAPPED! Polygon', currentMesh.name, 'attached to edge', snapCandidate.targetEdgeIndex, 'of', snapCandidate.targetMesh.name);
          
          // TODO: Add to connection graph for pair movement
          // TODO: Check if 3+ polygons connected for 3D folding
        }
        
        // Remove highlight
        if (edgeHighlightRef.current) {
          removeHighlight(edgeHighlightRef.current);
          edgeHighlightRef.current = null;
        }
        
        // Clear snap candidate
        currentSnapCandidateRef.current = null;
        
        // Re-enable camera
        camera.attachControl(canvasRef.current, true);
        
        currentMesh = null;
        draggedMeshRef.current = null;
        startingPoint = null;
      }
    };

    // Render loop
    engine.runRenderLoop(() => {
      scene.render();
    });

    // Handle resize
    const handleResize = () => {
      engine.resize();
    };
    window.addEventListener('resize', handleResize);

    setIsReady(true);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      scene.dispose();
      engine.dispose();
    };
  }, []);

  // Handle polygon placement
  const handlePlacePolygon = () => {
    if (!sceneRef.current || !selectedPolygonSides) return;

    const scene = sceneRef.current;
    
    // Create polygon mesh
    const polygon = createPolygonMesh(selectedPolygonSides, scene);
    console.log('Polygon created:', polygon.name, 'Position:', polygon.position, 'Visible:', polygon.isVisible);
    
    // Random position on ground
    const x = (Math.random() - 0.5) * 10;
    const z = (Math.random() - 0.5) * 10;
    polygon.position = new BABYLON.Vector3(x, 0.1, z);
    console.log('Polygon moved to:', polygon.position);
    
    // Add to tracking array for snap detection
    allPolygonsRef.current.push(polygon);

    // Stats updated in parent component via placeTrigger
  };

  return (
    <div className="relative w-full h-full">
      <canvas
        ref={canvasRef}
        className="w-full h-full outline-none"
        style={{ touchAction: 'none' }}
      />
      
      {isReady && selectedPolygonSides && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
          <button
            onClick={handlePlacePolygon}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg shadow-lg hover:shadow-xl transition-all font-semibold"
          >
            Place {selectedPolygonSides}-sided Polygon
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Create a polygon mesh with given number of sides
 */
function createPolygonMesh(sides: number, scene: BABYLON.Scene): BABYLON.Mesh {
  // Use precise polygon geometry with unit edge lengths
  const polygon = createPrecisePolygon(sides, scene, `polygon-${sides}`);
  
  // Scale 3x for better visibility (unit edge length = 1.0, scaled to 3.0)
  polygon.scaling = new BABYLON.Vector3(3, 3, 3);
  
  // Position slightly above ground to avoid z-fighting
  polygon.position.y = 0.05;

  // Material
  const material = new BABYLON.StandardMaterial(`polygonMat-${sides}`, scene);
  material.diffuseColor = new BABYLON.Color3(0.4, 0.6, 0.9);  // Blue
  material.specularColor = new BABYLON.Color3(0.3, 0.3, 0.3);
  material.emissiveColor = new BABYLON.Color3(0.1, 0.15, 0.2);  // Slight glow
  material.backFaceCulling = false;  // Show both sides
  polygon.material = material;

  // Enable picking
  polygon.isPickable = true;
  
  // Add edge rendering for better visibility
  polygon.enableEdgesRendering();
  polygon.edgesWidth = 3.0;
  polygon.edgesColor = new BABYLON.Color4(0.2, 0.3, 0.6, 1);

  console.log(`Created precise ${sides}-sided polygon with unit edge length`);
  console.log('Polygon metadata:', polygon.metadata);

  return polygon;
}
