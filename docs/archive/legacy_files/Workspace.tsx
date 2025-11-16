import { useRef, useState } from 'react';
import * as THREE from 'three';
import { createPolygonMesh } from '@/lib/polygonGeometry';
import { useFrame } from '@react-three/fiber';

interface PlacedPolygon {
  id: string;
  sides: number;
  position: THREE.Vector3;
  rotation: THREE.Euler;
  color: string;
}

interface WorkspaceProps {
  polygonToPlace: number | null;
  onPolygonPlaced: (polygon: PlacedPolygon) => void;
}

export function Workspace({ polygonToPlace, onPolygonPlaced }: WorkspaceProps) {
  const [placedPolygons, setPlacedPolygons] = useState<PlacedPolygon[]>([]);
  const [hoveredPosition, setHoveredPosition] = useState<THREE.Vector3 | null>(null);

  const handleClick = (event: any) => {
    if (!polygonToPlace) return;

    const point = event.point;
    const newPolygon: PlacedPolygon = {
      id: `polygon-${Date.now()}`,
      sides: polygonToPlace,
      position: new THREE.Vector3(point.x, 0.025, point.z),
      rotation: new THREE.Euler(0, 0, 0),
      color: '#6366f1',
    };

    setPlacedPolygons([...placedPolygons, newPolygon]);
    onPolygonPlaced(newPolygon);
  };

  const handlePointerMove = (event: any) => {
    if (polygonToPlace && event.point) {
      setHoveredPosition(new THREE.Vector3(event.point.x, 0.025, event.point.z));
    }
  };

  return (
    <>
      {/* Invisible plane for click detection */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0, 0]}
        onClick={handleClick}
        onPointerMove={handlePointerMove}
      >
        <planeGeometry args={[100, 100]} />
        <meshBasicMaterial visible={false} />
      </mesh>

      {/* Preview polygon at hover position */}
      {polygonToPlace && hoveredPosition && (
        <PreviewPolygon sides={polygonToPlace} position={hoveredPosition} />
      )}

      {/* Placed polygons */}
      {placedPolygons.map((polygon) => (
        <PlacedPolygonMesh key={polygon.id} polygon={polygon} />
      ))}
    </>
  );
}

function PreviewPolygon({ sides, position }: { sides: number; position: THREE.Vector3 }) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.position.copy(position);
    }
  });

  const mesh = createPolygonMesh(sides, 1, 0.05, '#8b5cf6');
  if (mesh.material instanceof THREE.MeshStandardMaterial) {
    mesh.material.transparent = true;
    mesh.material.opacity = 0.5;
  }

  return <primitive ref={meshRef} object={mesh} />;
}

function PlacedPolygonMesh({ polygon }: { polygon: PlacedPolygon }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const mesh = createPolygonMesh(polygon.sides, 1, 0.05, polygon.color);

  if (meshRef.current) {
    meshRef.current.position.copy(polygon.position);
    meshRef.current.rotation.copy(polygon.rotation);
    
    if (hovered) {
      (mesh.material as THREE.MeshStandardMaterial).emissive = new THREE.Color('#ffffff');
      (mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.2;
    }
  }

  return (
    <primitive
      ref={meshRef}
      object={mesh}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    />
  );
}
