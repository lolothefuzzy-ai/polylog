import * as THREE from 'three';

/**
 * Generate a regular polygon geometry with n sides
 * All polygons are equilateral with unit edge length
 */
export function createRegularPolygon(sides: number, edgeLength: number = 1): THREE.Shape {
  const shape = new THREE.Shape();
  
  // Calculate radius from edge length for a regular polygon
  // For a regular polygon: radius = edgeLength / (2 * sin(π/n))
  const angle = Math.PI / sides;
  const radius = edgeLength / (2 * Math.sin(angle));
  
  // Start at the top and go clockwise
  const startAngle = -Math.PI / 2;
  
  for (let i = 0; i <= sides; i++) {
    const theta = startAngle + (i * 2 * Math.PI) / sides;
    const x = radius * Math.cos(theta);
    const y = radius * Math.sin(theta);
    
    if (i === 0) {
      shape.moveTo(x, y);
    } else {
      shape.lineTo(x, y);
    }
  }
  
  return shape;
}

/**
 * Create a 3D extruded polygon mesh
 */
export function createPolygonMesh(
  sides: number,
  edgeLength: number = 1,
  thickness: number = 0.05,
  color: string = '#6366f1'
): THREE.Mesh {
  const shape = createRegularPolygon(sides, edgeLength);
  
  const extrudeSettings = {
    depth: thickness,
    bevelEnabled: true,
    bevelThickness: 0.01,
    bevelSize: 0.01,
    bevelSegments: 2,
  };
  
  const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
  
  // Center the geometry
  geometry.center();
  
  const material = new THREE.MeshStandardMaterial({
    color: new THREE.Color(color),
    metalness: 0.2,
    roughness: 0.4,
    side: THREE.DoubleSide,
  });
  
  return new THREE.Mesh(geometry, material);
}

/**
 * Get polygon name from number of sides
 */
export function getPolygonName(sides: number): string {
  const names: Record<number, string> = {
    3: 'Triangle',
    4: 'Square',
    5: 'Pentagon',
    6: 'Hexagon',
    7: 'Heptagon',
    8: 'Octagon',
    9: 'Nonagon',
    10: 'Decagon',
    11: 'Hendecagon',
    12: 'Dodecagon',
    13: 'Tridecagon',
    14: 'Tetradecagon',
    15: 'Pentadecagon',
    16: 'Hexadecagon',
    17: 'Heptadecagon',
    18: 'Octadecagon',
    19: 'Enneadecagon',
    20: 'Icosagon',
  };
  
  return names[sides] || `${sides}-gon`;
}

/**
 * Calculate edge length from polygon radius
 */
export function edgeLengthFromRadius(sides: number, radius: number): number {
  const angle = Math.PI / sides;
  return 2 * radius * Math.sin(angle);
}

/**
 * Calculate polygon radius from edge length
 */
export function radiusFromEdgeLength(sides: number, edgeLength: number): number {
  const angle = Math.PI / sides;
  return edgeLength / (2 * Math.sin(angle));
}

/**
 * Get vertices of a regular polygon
 */
export function getPolygonVertices(sides: number, edgeLength: number = 1): THREE.Vector2[] {
  const angle = Math.PI / sides;
  const radius = edgeLength / (2 * Math.sin(angle));
  const startAngle = -Math.PI / 2;
  
  const vertices: THREE.Vector2[] = [];
  
  for (let i = 0; i < sides; i++) {
    const theta = startAngle + (i * 2 * Math.PI) / sides;
    const x = radius * Math.cos(theta);
    const y = radius * Math.sin(theta);
    vertices.push(new THREE.Vector2(x, y));
  }
  
  return vertices;
}

/**
 * Calculate internal angle of a regular polygon
 */
export function getInternalAngle(sides: number): number {
  return ((sides - 2) * 180) / sides;
}

/**
 * Get all polygon types (3-20 sides)
 */
export function getAllPolygonTypes(): number[] {
  return Array.from({ length: 18 }, (_, i) => i + 3);
}
