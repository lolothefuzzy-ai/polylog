/**
 * 3D Polygon Geometry for Polylog Visualizer
 * 
 * Generates proper 3D polygon meshes with:
 * - Unit edge length enforcement
 * - Vertex-level precision
 * - Edge tracking for attachment validation
 */

import * as THREE from 'three';

export const UNIT_EDGE_LENGTH = 1.0;

export interface Polygon3D {
  id: string;
  sides: number;
  position: THREE.Vector3;
  rotation: THREE.Euler;
  mesh: THREE.Mesh;
  edges: Edge3D[];
  openEdges: Set<number>;
}

export interface Edge3D {
  index: number;
  start: THREE.Vector3;
  end: THREE.Vector3;
  midpoint: THREE.Vector3;
  normal: THREE.Vector3;
  length: number;
  isOpen: boolean;
  attachedTo?: { polygonId: string; edgeIndex: number };
}

/**
 * Calculate the radius needed to achieve unit edge length for a regular polygon
 */
export function calculateRadiusForUnitEdge(sides: number): number {
  // For regular polygon: edge = 2 * radius * sin(π / sides)
  // Solving for radius: radius = edge / (2 * sin(π / sides))
  return UNIT_EDGE_LENGTH / (2 * Math.sin(Math.PI / sides));
}

/**
 * Create a 3D polygon mesh with proper geometry
 */
export function createPolygon3D(
  id: string,
  sides: number,
  position: THREE.Vector3 = new THREE.Vector3(),
  rotation: THREE.Euler = new THREE.Euler()
): Polygon3D {
  const radius = calculateRadiusForUnitEdge(sides);
  
  // Create geometry
  const geometry = new THREE.BufferGeometry();
  const vertices: number[] = [];
  const indices: number[] = [];
  
  // Generate vertices for the polygon face
  const angleStep = (2 * Math.PI) / sides;
  const startAngle = -Math.PI / 2; // Start from top
  
  // Center vertex
  vertices.push(0, 0, 0);
  
  // Perimeter vertices
  for (let i = 0; i < sides; i++) {
    const angle = startAngle + i * angleStep;
    const x = radius * Math.cos(angle);
    const y = radius * Math.sin(angle);
    vertices.push(x, y, 0);
  }
  
  // Create triangular faces from center to perimeter
  for (let i = 0; i < sides; i++) {
    indices.push(0, i + 1, ((i + 1) % sides) + 1);
  }
  
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  
  // Create material with double-sided rendering
  const material = new THREE.MeshStandardMaterial({
    color: 0x6366f1,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.8,
    metalness: 0.3,
    roughness: 0.7,
  });
  
  // Create mesh
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.copy(position);
  mesh.rotation.copy(rotation);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  
  // Calculate edges
  const edges = calculateEdges(mesh, sides, radius);
  
  // All edges start as open
  const openEdges = new Set(Array.from({ length: sides }, (_, i) => i));
  
  return {
    id,
    sides,
    position,
    rotation,
    mesh,
    edges,
    openEdges,
  };
}

/**
 * Calculate edge information for a polygon mesh
 */
function calculateEdges(mesh: THREE.Mesh, sides: number, radius: number): Edge3D[] {
  const edges: Edge3D[] = [];
  const angleStep = (2 * Math.PI) / sides;
  const startAngle = -Math.PI / 2;
  
  for (let i = 0; i < sides; i++) {
    const angle1 = startAngle + i * angleStep;
    const angle2 = startAngle + ((i + 1) % sides) * angleStep;
    
    // Local coordinates (before transformation)
    const localStart = new THREE.Vector3(
      radius * Math.cos(angle1),
      radius * Math.sin(angle1),
      0
    );
    const localEnd = new THREE.Vector3(
      radius * Math.cos(angle2),
      radius * Math.sin(angle2),
      0
    );
    
    // Transform to world coordinates
    const start = localStart.clone().applyMatrix4(mesh.matrixWorld);
    const end = localEnd.clone().applyMatrix4(mesh.matrixWorld);
    
    const midpoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    
    // Calculate edge normal (perpendicular to edge, pointing outward)
    const edgeVector = new THREE.Vector3().subVectors(end, start);
    const normal = new THREE.Vector3(-edgeVector.y, edgeVector.x, 0).normalize();
    normal.applyQuaternion(mesh.quaternion);
    
    const length = start.distanceTo(end);
    
    edges.push({
      index: i,
      start,
      end,
      midpoint,
      normal,
      length,
      isOpen: true,
    });
  }
  
  return edges;
}

/**
 * Update edge information after polygon transformation
 */
export function updateEdges(polygon: Polygon3D): void {
  polygon.mesh.updateMatrixWorld();
  const radius = calculateRadiusForUnitEdge(polygon.sides);
  polygon.edges = calculateEdges(polygon.mesh, polygon.sides, radius);
}

/**
 * Get edge color based on state
 */
function getEdgeColor(edge: Edge3D): THREE.Color {
  if (!edge.isOpen) {
    return new THREE.Color(0x00ff00); // GREEN for closed/attached edges
  }
  
  // Check if edge length is valid (unit length)
  const lengthError = Math.abs(edge.length - UNIT_EDGE_LENGTH);
  if (lengthError > 0.05) {
    return new THREE.Color(0xff0000); // RED for invalid edges
  }
  
  // YELLOW for valid open edges (ready for attachment)
  if (lengthError < 0.01) {
    return new THREE.Color(0xffaa00); // YELLOW-ORANGE for conditional/ready
  }
  
  return new THREE.Color(0xff0000); // RED for open edges
}

/**
 * Create edge helper lines for visualization
 */
export function createEdgeHelpers(polygon: Polygon3D): THREE.LineSegments {
  const geometry = new THREE.BufferGeometry();
  const positions: number[] = [];
  const colors: number[] = [];
  
  for (const edge of polygon.edges) {
    positions.push(edge.start.x, edge.start.y, edge.start.z);
    positions.push(edge.end.x, edge.end.y, edge.end.z);
    
    const color = getEdgeColor(edge);
    colors.push(color.r, color.g, color.b);
    colors.push(color.r, color.g, color.b);
  }
  
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  
  const material = new THREE.LineBasicMaterial({
    vertexColors: true,
    linewidth: 3,
    transparent: true,
    opacity: 0.9,
  });
  
  return new THREE.LineSegments(geometry, material);
}

/**
 * Check if two edges can attach (same length, opposite orientation)
 */
export function canAttachEdges(edge1: Edge3D, edge2: Edge3D, tolerance: number = 0.01): boolean {
  // Check edge lengths match (unit length)
  const lengthDiff = Math.abs(edge1.length - edge2.length);
  if (lengthDiff > tolerance) return false;
  
  // Both must be unit length
  if (Math.abs(edge1.length - UNIT_EDGE_LENGTH) > tolerance) return false;
  if (Math.abs(edge2.length - UNIT_EDGE_LENGTH) > tolerance) return false;
  
  // Edges must be open
  if (!edge1.isOpen || !edge2.isOpen) return false;
  
  return true;
}

/**
 * Calculate attachment transform to align two edges
 */
export function calculateAttachmentTransform(
  sourceEdge: Edge3D,
  targetEdge: Edge3D
): { position: THREE.Vector3; rotation: THREE.Quaternion } {
  // Target position: align edge midpoints
  const position = targetEdge.midpoint.clone();
  
  // Calculate rotation to align edges
  const sourceDirection = new THREE.Vector3().subVectors(sourceEdge.end, sourceEdge.start).normalize();
  const targetDirection = new THREE.Vector3().subVectors(targetEdge.start, targetEdge.end).normalize(); // Reverse for opposite orientation
  
  const rotation = new THREE.Quaternion().setFromUnitVectors(sourceDirection, targetDirection);
  
  return { position, rotation };
}
