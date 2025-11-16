/**
 * Liaison Graph for Polylog6
 * 
 * Tracks all polygon connections and attachments in the workspace
 */

import * as THREE from 'three';

export interface PolygonNode {
  id: string;
  sides: number;
  position: THREE.Vector3;
  rotation: THREE.Euler;
  attachments: string[];  // List of attachment edge IDs
  openEdges: Set<number>;  // Indices of edges that are not attached
}

export interface AttachmentEdge {
  id: string;
  polygon1_id: string;
  polygon2_id: string;
  edge1_index: number;
  edge2_index: number;
  fold_angle: number;  // Dihedral angle in degrees
  stability: number;  // 0.0 to 1.0
  created_at: number;  // Timestamp
}

export interface OpenEdge {
  polygon_id: string;
  edge_index: number;
  start_vertex: THREE.Vector3;
  end_vertex: THREE.Vector3;
  normal: THREE.Vector3;
  midpoint: THREE.Vector3;
  length: number;
}

export class LiaisonGraph {
  private nodes: Map<string, PolygonNode>;
  private edges: Map<string, AttachmentEdge>;
  private openEdgeRegistry: Map<string, OpenEdge>;
  
  constructor() {
    this.nodes = new Map();
    this.edges = new Map();
    this.openEdgeRegistry = new Map();
  }
  
  /**
   * Add a polygon to the graph
   */
  addPolygon(
    id: string,
    sides: number,
    position: THREE.Vector3,
    rotation: THREE.Euler
  ): void {
    const node: PolygonNode = {
      id,
      sides,
      position: position.clone(),
      rotation: rotation.clone(),
      attachments: [],
      openEdges: new Set(Array.from({ length: sides }, (_, i) => i))
    };
    
    this.nodes.set(id, node);
    
    // Add all edges to open edge registry
    this.updateOpenEdges(id);
  }
  
  /**
   * Remove a polygon from the graph
   */
  removePolygon(id: string): void {
    const node = this.nodes.get(id);
    if (!node) return;
    
    // Remove all attachments involving this polygon
    for (const edgeId of node.attachments) {
      this.removeAttachment(edgeId);
    }
    
    // Remove from open edge registry
    for (let i = 0; i < node.sides; i++) {
      const edgeKey = `${id}-${i}`;
      this.openEdgeRegistry.delete(edgeKey);
    }
    
    this.nodes.delete(id);
  }
  
  /**
   * Add an attachment between two polygons
   */
  addAttachment(
    polygon1_id: string,
    polygon2_id: string,
    edge1_index: number,
    edge2_index: number,
    fold_angle: number,
    stability: number
  ): string {
    const edgeId = `${polygon1_id}-${edge1_index}_${polygon2_id}-${edge2_index}`;
    
    const attachment: AttachmentEdge = {
      id: edgeId,
      polygon1_id,
      polygon2_id,
      edge1_index,
      edge2_index,
      fold_angle,
      stability,
      created_at: Date.now()
    };
    
    this.edges.set(edgeId, attachment);
    
    // Update nodes
    const node1 = this.nodes.get(polygon1_id);
    const node2 = this.nodes.get(polygon2_id);
    
    if (node1) {
      node1.attachments.push(edgeId);
      node1.openEdges.delete(edge1_index);
      this.openEdgeRegistry.delete(`${polygon1_id}-${edge1_index}`);
    }
    
    if (node2) {
      node2.attachments.push(edgeId);
      node2.openEdges.delete(edge2_index);
      this.openEdgeRegistry.delete(`${polygon2_id}-${edge2_index}`);
    }
    
    return edgeId;
  }
  
  /**
   * Remove an attachment
   */
  removeAttachment(edgeId: string): void {
    const attachment = this.edges.get(edgeId);
    if (!attachment) return;
    
    const node1 = this.nodes.get(attachment.polygon1_id);
    const node2 = this.nodes.get(attachment.polygon2_id);
    
    if (node1) {
      node1.attachments = node1.attachments.filter(id => id !== edgeId);
      node1.openEdges.add(attachment.edge1_index);
      this.updateOpenEdges(attachment.polygon1_id);
    }
    
    if (node2) {
      node2.attachments = node2.attachments.filter(id => id !== edgeId);
      node2.openEdges.add(attachment.edge2_index);
      this.updateOpenEdges(attachment.polygon2_id);
    }
    
    this.edges.delete(edgeId);
  }
  
  /**
   * Update open edge registry for a polygon
   */
  private updateOpenEdges(polygonId: string): void {
    const node = this.nodes.get(polygonId);
    if (!node) return;
    
    // Calculate edge vertices based on position and rotation
    const vertices = this.calculatePolygonVertices(node.sides, node.position, node.rotation);
    
    Array.from(node.openEdges).forEach(edgeIndex => {
      const start = vertices[edgeIndex];
      const end = vertices[(edgeIndex + 1) % node.sides];
      const midpoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
      
      // Calculate edge normal (perpendicular to edge, in XY plane for now)
      const edgeVector = new THREE.Vector3().subVectors(end, start);
      const normal = new THREE.Vector3(-edgeVector.y, edgeVector.x, 0).normalize();
      
      const openEdge: OpenEdge = {
        polygon_id: polygonId,
        edge_index: edgeIndex,
        start_vertex: start,
        end_vertex: end,
        normal,
        midpoint,
        length: edgeVector.length()
      };
      
      this.openEdgeRegistry.set(`${polygonId}-${edgeIndex}`, openEdge);
    });
  }
  
  /**
   * Calculate polygon vertices based on position and rotation
   */
  private calculatePolygonVertices(
    sides: number,
    position: THREE.Vector3,
    rotation: THREE.Euler
  ): THREE.Vector3[] {
    const vertices: THREE.Vector3[] = [];
    const radius = 1 / (2 * Math.sin(Math.PI / sides));  // Circumradius for unit edge length
    
    for (let i = 0; i < sides; i++) {
      const angle = (i * 2 * Math.PI) / sides - Math.PI / 2;
      const x = radius * Math.cos(angle);
      const y = radius * Math.sin(angle);
      const z = 0;
      
      const vertex = new THREE.Vector3(x, y, z);
      vertex.applyEuler(rotation);
      vertex.add(position);
      
      vertices.push(vertex);
    }
    
    return vertices;
  }
  
  /**
   * Get all open edges
   */
  getOpenEdges(): OpenEdge[] {
    return Array.from(this.openEdgeRegistry.values());
  }
  
  /**
   * Get open edges near a point
   */
  getOpenEdgesNear(point: THREE.Vector3, maxDistance: number): OpenEdge[] {
    const nearbyEdges: OpenEdge[] = [];
    
    Array.from(this.openEdgeRegistry.values()).forEach(edge => {
      const distance = point.distanceTo(edge.midpoint);
      if (distance <= maxDistance) {
        nearbyEdges.push(edge);
      }
    });
    
    // Sort by distance
    nearbyEdges.sort((a, b) => {
      const distA = point.distanceTo(a.midpoint);
      const distB = point.distanceTo(b.midpoint);
      return distA - distB;
    });
    
    return nearbyEdges;
  }
  
  /**
   * Get polygon node
   */
  getPolygon(id: string): PolygonNode | undefined {
    return this.nodes.get(id);
  }
  
  /**
   * Get all polygons
   */
  getAllPolygons(): PolygonNode[] {
    return Array.from(this.nodes.values());
  }
  
  /**
   * Get attachment edge
   */
  getAttachment(id: string): AttachmentEdge | undefined {
    return this.edges.get(id);
  }
  
  /**
   * Get all attachments
   */
  getAllAttachments(): AttachmentEdge[] {
    return Array.from(this.edges.values());
  }
  
  /**
   * Get total open edge count
   */
  getTotalOpenEdges(): number {
    return this.openEdgeRegistry.size;
  }
  
  /**
   * Check if assembly is closed (no open edges)
   */
  isClosed(): boolean {
    return this.openEdgeRegistry.size === 0;
  }
  
  /**
   * Get assembly composition (list of polygon sides)
   */
  getComposition(): number[] {
    return Array.from(this.nodes.values()).map(node => node.sides);
  }
  
  /**
   * Clear the graph
   */
  clear(): void {
    this.nodes.clear();
    this.edges.clear();
    this.openEdgeRegistry.clear();
  }
  
  /**
   * Export graph to JSON
   */
  toJSON(): any {
    return {
      nodes: Array.from(this.nodes.entries()).map(([id, node]) => ({
        id,
        sides: node.sides,
        position: node.position.toArray(),
        rotation: [node.rotation.x, node.rotation.y, node.rotation.z],
        attachments: node.attachments,
        openEdges: Array.from(node.openEdges)
      })),
      edges: Array.from(this.edges.values())
    };
  }
  
  /**
   * Import graph from JSON
   */
  fromJSON(data: any): void {
    this.clear();
    
    // Restore nodes
    for (const nodeData of data.nodes) {
      const position = new THREE.Vector3().fromArray(nodeData.position);
      const rotation = new THREE.Euler().fromArray(nodeData.rotation);
      
      this.addPolygon(nodeData.id, nodeData.sides, position, rotation);
      
      const node = this.nodes.get(nodeData.id);
      if (node) {
        node.attachments = nodeData.attachments;
        node.openEdges = new Set(nodeData.openEdges);
      }
    }
    
    // Restore edges
    for (const edgeData of data.edges) {
      this.edges.set(edgeData.id, edgeData);
    }
    
    // Update open edge registry
    Array.from(this.nodes.values()).forEach(node => {
      this.updateOpenEdges(node.id);
    });
  }
}
