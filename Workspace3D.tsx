import { useEffect, useRef, useState } from 'react';
import { Canvas, useThree, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { Polygon3D, updateEdges, createEdgeHelpers } from '@/lib/polygon3D';
import { findSnapGuide, applyAttachment, findAttachments } from '@/lib/attachmentResolver';
import SnapGuide from './SnapGuide';
import type { SnapGuide as SnapGuideType } from '@/lib/attachmentResolver';

interface Workspace3DProps {
  polygons: Polygon3D[];
  selectedPolygonId: string | null;
  onPolygonClick?: (id: string) => void;
  onPolygonsUpdate?: (polygons: Polygon3D[]) => void;
  showEdgeHelpers?: boolean;
  enableSnapping?: boolean;
}

export default function Workspace3D({
  polygons,
  selectedPolygonId,
  onPolygonClick,
  onPolygonsUpdate,
  showEdgeHelpers = true,
  enableSnapping = true,
}: Workspace3DProps) {
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{
          position: [8, 8, 8],
          fov: 50,
        }}
        shadows
        gl={{
          antialias: true,
          alpha: true,
        }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={0.8}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <directionalLight position={[-5, 5, -5]} intensity={0.3} />
        <pointLight position={[0, 10, 0]} intensity={0.5} />
        
        {/* Grid */}
        <gridHelper args={[20, 20, '#6366f1', '#8b5cf6']} />
        
        {/* Ground plane for shadows */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
          <planeGeometry args={[50, 50]} />
          <shadowMaterial opacity={0.2} />
        </mesh>
        
        {/* Polygons */}
        <PolygonRenderer
          polygons={polygons}
          selectedPolygonId={selectedPolygonId}
          onPolygonClick={onPolygonClick}
          onPolygonsUpdate={onPolygonsUpdate}
          showEdgeHelpers={showEdgeHelpers}
          enableSnapping={enableSnapping}
        />
        
        {/* Controls */}
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={3}
          maxDistance={50}
          maxPolarAngle={Math.PI / 2}
        />
      </Canvas>
    </div>
  );
}

function PolygonRenderer({
  polygons,
  selectedPolygonId,
  onPolygonClick,
  onPolygonsUpdate,
  showEdgeHelpers,
  enableSnapping,
}: {
  polygons: Polygon3D[];
  selectedPolygonId: string | null;
  onPolygonClick?: (id: string) => void;
  onPolygonsUpdate?: (polygons: Polygon3D[]) => void;
  showEdgeHelpers: boolean;
  enableSnapping: boolean;
}) {
  const { scene, camera, raycaster, gl } = useThree();
  const edgeHelpersRef = useRef<Map<string, THREE.LineSegments>>(new Map());
  const [snapGuide, setSnapGuide] = useState<SnapGuideType | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{ point: THREE.Vector3; polygonPosition: THREE.Vector3 } | null>(null);
  
  useEffect(() => {
    // Add polygons to scene
    polygons.forEach((polygon) => {
      if (!scene.getObjectByProperty('uuid', polygon.mesh.uuid)) {
        scene.add(polygon.mesh);
        
        // Add edge helpers
        if (showEdgeHelpers) {
          const helper = createEdgeHelpers(polygon);
          helper.userData.polygonId = polygon.id;
          scene.add(helper);
          edgeHelpersRef.current.set(polygon.id, helper);
        }
      }
      
      // Update selection state
      const material = polygon.mesh.material as THREE.MeshStandardMaterial;
      if (polygon.id === selectedPolygonId) {
        material.color.setHex(0x8b5cf6);
        material.emissive.setHex(0x4c1d95);
        material.emissiveIntensity = 0.3;
      } else {
        material.color.setHex(0x6366f1);
        material.emissive.setHex(0x000000);
        material.emissiveIntensity = 0;
      }
    });
    
    // Cleanup removed polygons
    const polygonIds = new Set(polygons.map(p => p.id));
    const objectsToRemove: THREE.Object3D[] = [];
    
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh && object.userData.polygonId) {
        if (!polygonIds.has(object.userData.polygonId)) {
          objectsToRemove.push(object);
        }
      }
    });
    
    objectsToRemove.forEach(obj => {
      scene.remove(obj);
      const helper = edgeHelpersRef.current.get(obj.userData.polygonId);
      if (helper) {
        scene.remove(helper);
        edgeHelpersRef.current.delete(obj.userData.polygonId);
      }
    });
  }, [polygons, selectedPolygonId, scene, showEdgeHelpers]);
  
  // Handle mouse events for dragging
  useEffect(() => {
    const canvas = gl.domElement;
    
    const onMouseDown = (event: MouseEvent) => {
      if (!selectedPolygonId) return;
      
      const rect = canvas.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1
      );
      
      raycaster.setFromCamera(mouse, camera);
      
      const selectedPolygon = polygons.find(p => p.id === selectedPolygonId);
      if (!selectedPolygon) return;
      
      const intersects = raycaster.intersectObject(selectedPolygon.mesh);
      
      if (intersects.length > 0) {
        setIsDragging(true);
        dragStartRef.current = {
          point: intersects[0].point,
          polygonPosition: selectedPolygon.mesh.position.clone(),
        };
      }
    };
    
    const onMouseMove = (event: MouseEvent) => {
      if (!isDragging || !selectedPolygonId || !dragStartRef.current) return;
      
      const rect = canvas.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1
      );
      
      raycaster.setFromCamera(mouse, camera);
      
      // Raycast to ground plane
      const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
      const intersection = new THREE.Vector3();
      raycaster.ray.intersectPlane(plane, intersection);
      
      if (intersection) {
        const selectedPolygon = polygons.find(p => p.id === selectedPolygonId);
        if (!selectedPolygon) return;
        
        // Calculate new position
        const offset = new THREE.Vector3().subVectors(intersection, dragStartRef.current.point);
        const newPosition = new THREE.Vector3().addVectors(dragStartRef.current.polygonPosition, offset);
        newPosition.y = 0.5; // Keep at fixed height
        
        selectedPolygon.mesh.position.copy(newPosition);
        selectedPolygon.position.copy(newPosition);
        selectedPolygon.mesh.updateMatrixWorld();
        updateEdges(selectedPolygon);
        
        // Find snap guide if snapping is enabled
        if (enableSnapping) {
          const otherPolygons = polygons.filter(p => p.id !== selectedPolygonId);
          const guide = findSnapGuide(selectedPolygon, otherPolygons);
          setSnapGuide(guide);
        }
        
        // Trigger update
        if (onPolygonsUpdate) {
          onPolygonsUpdate([...polygons]);
        }
      }
    };
    
    const onMouseUp = () => {
      if (isDragging && selectedPolygonId && snapGuide && snapGuide.isValid && enableSnapping) {
        // Apply snap
        const selectedPolygon = polygons.find(p => p.id === selectedPolygonId);
        if (selectedPolygon) {
          const otherPolygons = polygons.filter(p => p.id !== selectedPolygonId);
          const attachments = findAttachments(selectedPolygon, otherPolygons, 0.5);
          
          if (attachments.length > 0) {
            applyAttachment(attachments[0]);
            updateEdges(selectedPolygon);
            updateEdges(attachments[0].targetPolygon);
            
            if (onPolygonsUpdate) {
              onPolygonsUpdate([...polygons]);
            }
          }
        }
      }
      
      setIsDragging(false);
      setSnapGuide(null);
      dragStartRef.current = null;
    };
    
    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseup', onMouseUp);
    
    return () => {
      canvas.removeEventListener('mousedown', onMouseDown);
      canvas.removeEventListener('mousemove', onMouseMove);
      canvas.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDragging, selectedPolygonId, polygons, snapGuide, enableSnapping, camera, raycaster, gl, onPolygonsUpdate]);
  
  // Update edge helpers
  useFrame(() => {
    if (showEdgeHelpers) {
      polygons.forEach((polygon) => {
        updateEdges(polygon);
        const helper = edgeHelpersRef.current.get(polygon.id);
        if (helper) {
          scene.remove(helper);
          const newHelper = createEdgeHelpers(polygon);
          newHelper.userData.polygonId = polygon.id;
          scene.add(newHelper);
          edgeHelpersRef.current.set(polygon.id, newHelper);
        }
      });
    }
  });
  
  return (
    <>
      {enableSnapping && <SnapGuide snapGuide={snapGuide} />}
    </>
  );
}
