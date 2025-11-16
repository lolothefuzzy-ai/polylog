import * as BABYLON from '@babylonjs/core';
import { UnicodeDecoder, DecodedGeometry } from './UnicodeDecoder';

export class PolyformMesh {
  private mesh: BABYLON.Mesh | null = null;
  private scene: BABYLON.Scene;
  private decoder: UnicodeDecoder;
  private encoding: string;

  constructor(encoding: string, scene: BABYLON.Scene) {
    this.scene = scene;
    this.decoder = new UnicodeDecoder();
    this.encoding = encoding;
  }

  async initialize(): Promise<void> {
    if (this.mesh) return;
    
    // Decode the geometry
    const geometry = await this.decoder.decode(this.encoding);
    
    // Create Babylon.js mesh
    this.mesh = this.createMeshFromGeometry(geometry, this.encoding);
  }

  private createMeshFromGeometry(geometry: DecodedGeometry, name: string): BABYLON.Mesh {
    // Create the mesh
    const mesh = new BABYLON.Mesh(name, this.scene);

    // Create vertex data
    const vertexData = new BABYLON.VertexData();

    // Set positions
    vertexData.positions = geometry.vertices;

    // Set indices
    vertexData.indices = geometry.indices;

    // Set normals
    vertexData.normals = geometry.normals;

    // Apply vertex data to mesh
    vertexData.applyToMesh(mesh);

    // Create and apply material
    const material = new BABYLON.StandardMaterial(`${name}_material`, this.scene);
    material.diffuseColor = new BABYLON.Color3(0.2, 0.6, 1.0);
    material.specularColor = new BABYLON.Color3(0.2, 0.2, 0.2);
    material.emissiveColor = new BABYLON.Color3(0.05, 0.1, 0.15);
    material.backFaceCulling = false;
    mesh.material = material;

    // Enable collisions
    mesh.checkCollisions = true;

    return mesh;
  }

  /**
   * Get the Babylon.js mesh instance
   */
  getMesh(): BABYLON.Mesh | null {
    return this.mesh;
  }

  /**
   * Set mesh position
   */
  setPosition(position: BABYLON.Vector3): void {
    if (this.mesh) {
      this.mesh.position = position;
    }
  }

  /**
   * Set mesh rotation
   */
  setRotation(rotation: BABYLON.Vector3): void {
    if (this.mesh) {
      this.mesh.rotation = rotation;
    }
  }

  /**
   * Set mesh scale
   */
  setScale(scale: BABYLON.Vector3): void {
    if (this.mesh) {
      this.mesh.scaling = scale;
    }
  }

  /**
   * Dispose of the mesh
   */
  dispose(): void {
    if (this.mesh) {
      if (this.mesh.material) {
        this.mesh.material.dispose();
      }
      this.mesh.dispose();
      this.mesh = null;
    }
  }

  /**
   * Create an instance of this mesh for instancing
   */
  createInstance(name?: string): BABYLON.InstancedMesh | null {
    return this.mesh ? this.mesh.createInstance(name || `${this.mesh.name}_instance_${Date.now()}`) : null;
  }

  /**
   * Get mesh bounding information
   */
  getBoundingInfo(): BABYLON.BoundingInfo | null {
    return this.mesh ? this.mesh.getBoundingInfo() : null;
  }
}
