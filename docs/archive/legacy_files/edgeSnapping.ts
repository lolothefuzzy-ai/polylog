/**
 * Edge Snapping Utility
 * Implements the core Polylog principle: polygons attach edge-to-edge
 * without deformation, maintaining unit edge length
 */

export interface Point {
  x: number;
  y: number;
}

export interface Edge {
  start: Point;
  end: Point;
  length: number;
}

export interface PolygonData {
  id: string;
  sides: number;
  x: number;
  y: number;
  rotation: number;
  radius: number;
}

const SNAP_THRESHOLD = 15; // pixels
const UNIT_EDGE_LENGTH = 60; // pixels (visual representation of unit length)

/**
 * Calculate vertices of a polygon given center, radius, sides, and rotation
 */
export function getPolygonVertices(
  centerX: number,
  centerY: number,
  radius: number,
  sides: number,
  rotation: number = 0
): Point[] {
  const startAngle = -Math.PI / 2 + rotation;
  return Array.from({ length: sides }, (_, i) => {
    const angle = startAngle + (i * 2 * Math.PI) / sides;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });
}

/**
 * Get all edges of a polygon
 */
export function getPolygonEdges(polygon: PolygonData): Edge[] {
  const vertices = getPolygonVertices(
    polygon.x,
    polygon.y,
    polygon.radius,
    polygon.sides,
    polygon.rotation
  );
  
  const edges: Edge[] = [];
  for (let i = 0; i < vertices.length; i++) {
    const start = vertices[i];
    const end = vertices[(i + 1) % vertices.length];
    const length = Math.sqrt(
      Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2)
    );
    edges.push({ start, end, length });
  }
  
  return edges;
}

/**
 * Calculate distance between two points
 */
function distance(p1: Point, p2: Point): number {
  return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
}

/**
 * Find the closest edge from existing polygons to snap to
 */
export function findSnapTarget(
  newPolygon: PolygonData,
  existingPolygons: PolygonData[]
): { polygon: PolygonData; edgeIndex: number; snapPoint: Point; rotation: number } | null {
  const newVertices = getPolygonVertices(
    newPolygon.x,
    newPolygon.y,
    newPolygon.radius,
    newPolygon.sides,
    newPolygon.rotation
  );
  
  let closestSnap: {
    polygon: PolygonData;
    edgeIndex: number;
    snapPoint: Point;
    rotation: number;
    distance: number;
  } | null = null;
  
  // Check each existing polygon
  for (const existingPolygon of existingPolygons) {
    const existingEdges = getPolygonEdges(existingPolygon);
    
    // Check each edge of the existing polygon
    existingEdges.forEach((edge, edgeIndex) => {
      // Check each vertex of the new polygon
      newVertices.forEach((vertex) => {
        // Calculate distance to edge midpoint
        const edgeMidpoint = {
          x: (edge.start.x + edge.end.x) / 2,
          y: (edge.start.y + edge.end.y) / 2,
        };
        
        const dist = distance(vertex, edgeMidpoint);
        
        if (dist < SNAP_THRESHOLD && (!closestSnap || dist < closestSnap.distance)) {
          // Calculate rotation to align edges
          const edgeAngle = Math.atan2(
            edge.end.y - edge.start.y,
            edge.end.x - edge.start.x
          );
          
          closestSnap = {
            polygon: existingPolygon,
            edgeIndex,
            snapPoint: edgeMidpoint,
            rotation: edgeAngle + Math.PI, // Flip to attach on opposite side
            distance: dist,
          };
        }
      });
    });
  }
  
  return closestSnap;
}

/**
 * Validate that a polygon attachment is geometrically valid
 * (edges align, no gaps, unit edge length preserved)
 */
export function validateAttachment(
  polygon1: PolygonData,
  polygon2: PolygonData,
  edgeIndex1: number,
  edgeIndex2: number
): boolean {
  const edges1 = getPolygonEdges(polygon1);
  const edges2 = getPolygonEdges(polygon2);
  
  const edge1 = edges1[edgeIndex1];
  const edge2 = edges2[edgeIndex2];
  
  // Check if edge lengths match (within tolerance)
  const lengthDiff = Math.abs(edge1.length - edge2.length);
  if (lengthDiff > 1) return false;
  
  // Check if edges are aligned (vertices match)
  const dist1 = distance(edge1.start, edge2.end);
  const dist2 = distance(edge1.end, edge2.start);
  
  return dist1 < 2 && dist2 < 2;
}

/**
 * Calculate the unit edge length for a polygon with given radius
 */
export function calculateEdgeLength(radius: number, sides: number): number {
  // For a regular polygon: edge = 2 * radius * sin(π / sides)
  return 2 * radius * Math.sin(Math.PI / sides);
}

/**
 * Calculate the radius needed to achieve unit edge length
 */
export function calculateRadiusForUnitEdge(sides: number): number {
  // Inverse of edge length formula
  return UNIT_EDGE_LENGTH / (2 * Math.sin(Math.PI / sides));
}
