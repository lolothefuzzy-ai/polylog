/**
 * Attachment Matrix for Polylog6
 * 
 * Provides O(1) lookup for polygon compatibility, fold angles, and stability scores
 */

export interface AttachmentData {
  valid: boolean;
  fold_angles: number[];  // Possible dihedral angles in degrees
  stability: number;  // 0.0 to 1.0
  notes?: string;
}

/**
 * Attachment matrix: maps polygon pairs to attachment metadata
 * Key format: "${sides1}-${sides2}"
 */
export const ATTACHMENT_MATRIX: Record<string, AttachmentData> = {
  // Triangle-Triangle (most common, forms tetrahedron, octahedron, icosahedron)
  '3-3': {
    valid: true,
    fold_angles: [60, 70.5, 109.5, 120, 138.2],
    stability: 0.95,
    notes: 'Tetrahedron: 70.5°, Octahedron: 109.5°, Icosahedron: 138.2°'
  },
  
  // Triangle-Square (forms square pyramid, cuboctahedron)
  '3-4': {
    valid: true,
    fold_angles: [54.7, 90, 125.3],
    stability: 0.9,
    notes: 'Square pyramid: 54.7°, Cuboctahedron: 125.3°'
  },
  
  // Triangle-Pentagon (forms icosidodecahedron)
  '3-5': {
    valid: true,
    fold_angles: [37.4, 108, 142.6],
    stability: 0.85,
    notes: 'Icosidodecahedron: 142.6°'
  },
  
  // Triangle-Hexagon (forms truncated tetrahedron)
  '3-6': {
    valid: true,
    fold_angles: [70.5, 109.5],
    stability: 0.8,
    notes: 'Truncated tetrahedron'
  },
  
  // Square-Square (forms cube, cuboid)
  '4-4': {
    valid: true,
    fold_angles: [90, 180],
    stability: 1.0,
    notes: 'Cube: 90°, Flat: 180°'
  },
  
  // Square-Pentagon (forms truncated icosahedron)
  '4-5': {
    valid: true,
    fold_angles: [116.6, 138.2],
    stability: 0.85,
    notes: 'Truncated icosahedron (soccer ball)'
  },
  
  // Square-Hexagon (forms truncated octahedron)
  '4-6': {
    valid: true,
    fold_angles: [125.3],
    stability: 0.9,
    notes: 'Truncated octahedron'
  },
  
  // Pentagon-Pentagon (forms dodecahedron)
  '5-5': {
    valid: true,
    fold_angles: [116.6, 180],
    stability: 0.95,
    notes: 'Dodecahedron: 116.6°'
  },
  
  // Pentagon-Hexagon (forms truncated icosahedron)
  '5-6': {
    valid: true,
    fold_angles: [138.2, 142.6],
    stability: 0.85,
    notes: 'Truncated icosahedron'
  },
  
  // Hexagon-Hexagon (forms honeycomb, but requires gap filling)
  '6-6': {
    valid: true,
    fold_angles: [120, 180],
    stability: 0.7,
    notes: 'Flat honeycomb: 120°, requires gap filling for 3D'
  },
  
  // Higher-order polygons (7-20 sides)
  // Generally valid but with lower stability
  '7-7': { valid: true, fold_angles: [128.6, 180], stability: 0.6 },
  '8-8': { valid: true, fold_angles: [135, 180], stability: 0.6 },
  '9-9': { valid: true, fold_angles: [140, 180], stability: 0.5 },
  '10-10': { valid: true, fold_angles: [144, 180], stability: 0.5 },
  '11-11': { valid: true, fold_angles: [147.3, 180], stability: 0.4 },
  '12-12': { valid: true, fold_angles: [150, 180], stability: 0.4 },
  
  // Mixed higher-order (lower stability, experimental)
  '3-7': { valid: true, fold_angles: [90, 120], stability: 0.6 },
  '3-8': { valid: true, fold_angles: [90, 135], stability: 0.6 },
  '4-7': { valid: true, fold_angles: [90, 128.6], stability: 0.6 },
  '4-8': { valid: true, fold_angles: [90, 135], stability: 0.7 },
  '5-7': { valid: true, fold_angles: [108, 128.6], stability: 0.5 },
  '5-8': { valid: true, fold_angles: [108, 135], stability: 0.6 },
  '6-7': { valid: true, fold_angles: [120, 128.6], stability: 0.5 },
  '6-8': { valid: true, fold_angles: [120, 135], stability: 0.6 },
};

/**
 * Get attachment data for two polygons
 * Handles both orderings (3-4 and 4-3 are equivalent)
 */
export function getAttachmentData(sides1: number, sides2: number): AttachmentData | null {
  const key1 = `${sides1}-${sides2}`;
  const key2 = `${sides2}-${sides1}`;
  
  return ATTACHMENT_MATRIX[key1] || ATTACHMENT_MATRIX[key2] || null;
}

/**
 * Check if two polygons can attach
 */
export function canAttach(sides1: number, sides2: number): boolean {
  const data = getAttachmentData(sides1, sides2);
  return data !== null && data.valid;
}

/**
 * Get stability score for attachment (0.0 to 1.0)
 */
export function getStabilityScore(sides1: number, sides2: number): number {
  const data = getAttachmentData(sides1, sides2);
  return data?.stability ?? 0.0;
}

/**
 * Get possible fold angles for attachment
 */
export function getFoldAngles(sides1: number, sides2: number): number[] {
  const data = getAttachmentData(sides1, sides2);
  return data?.fold_angles ?? [];
}

/**
 * Get best fold angle (first in list, typically most stable)
 */
export function getBestFoldAngle(sides1: number, sides2: number): number | null {
  const angles = getFoldAngles(sides1, sides2);
  return angles.length > 0 ? angles[0] : null;
}

/**
 * Calculate stability color for visual feedback
 * Returns: 'green' (high), 'yellow' (medium), 'red' (low/invalid)
 */
export function getStabilityColor(sides1: number, sides2: number): string {
  const stability = getStabilityScore(sides1, sides2);
  
  if (stability >= 0.8) return 'green';
  if (stability >= 0.5) return 'yellow';
  return 'red';
}

/**
 * Get attachment notes/description
 */
export function getAttachmentNotes(sides1: number, sides2: number): string {
  const data = getAttachmentData(sides1, sides2);
  return data?.notes ?? 'No specific polyhedra known';
}

/**
 * Generate full attachment matrix for all combinations (3-20 sides)
 * This fills in missing entries with default values
 */
export function generateFullAttachmentMatrix(): Record<string, AttachmentData> {
  const matrix: Record<string, AttachmentData> = { ...ATTACHMENT_MATRIX };
  
  for (let i = 3; i <= 20; i++) {
    for (let j = i; j <= 20; j++) {
      const key = `${i}-${j}`;
      
      if (!matrix[key]) {
        // Calculate interior angle for each polygon
        const angle_i = ((i - 2) * 180) / i;
        const angle_j = ((j - 2) * 180) / j;
        
        // Default fold angle (heuristic: average of interior angles)
        const default_fold = (angle_i + angle_j) / 2;
        
        // Stability decreases with polygon complexity
        const stability = Math.max(0.3, 1.0 - (i + j) / 40);
        
        matrix[key] = {
          valid: true,
          fold_angles: [default_fold, 180],
          stability,
          notes: `Experimental: ${i}-gon + ${j}-gon`
        };
      }
    }
  }
  
  return matrix;
}

/**
 * Calculate required rotation to align two edges
 * Returns rotation angle in radians
 */
export function calculateAlignmentRotation(
  edge1_angle: number,
  edge2_angle: number
): number {
  // Edges should be anti-parallel (180° apart) for attachment
  const target_angle = edge1_angle + Math.PI;
  let rotation = target_angle - edge2_angle;
  
  // Normalize to [-π, π]
  while (rotation > Math.PI) rotation -= 2 * Math.PI;
  while (rotation < -Math.PI) rotation += 2 * Math.PI;
  
  return rotation;
}

/**
 * Check if edge lengths are compatible (within tolerance)
 */
export function areEdgeLengthsCompatible(
  length1: number,
  length2: number,
  tolerance: number = 0.01
): boolean {
  return Math.abs(length1 - length2) < tolerance;
}
