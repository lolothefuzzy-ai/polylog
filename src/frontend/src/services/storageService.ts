import type { components } from '../api.generated';

export type SymbolList = components['schemas']['SymbolList'];
export type ExpandedPolyform = components['schemas']['ExpandedPolyform'];
export type TierCandidateResponse = components['schemas']['TierCandidateResponse'];
export type StorageStats = components['schemas']['StorageStats'];

interface GetSymbolsOptions {
  tier?: 0 | 1 | 3 | 4;
  page?: number;
  limit?: number;
}

export interface Polyhedron {
  symbol: string;
  name: string;
  classification: 'platonic' | 'archimedean' | 'johnson';
  vertices?: number[][];
  faces?: number[][];
  compression_ratio?: number;
  metadata?: Record<string, unknown>;
}

export interface AttachmentOption {
  fold_angle: number;
  stability: number;
  context: string;
  edge_a: number;
  edge_b: number;
}

export interface AttachmentMatrix {
  [key: string]: {
    fold_angles: number[];
    stability_scores: number[];
    contexts: string[];
  };
}

export class StorageService {
  // API URL - defaults to FastAPI server, can be overridden via env var
  private readonly baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  private readonly tier1Url = `${this.baseUrl}/tier1`;
  private readonly storageUrl = `${this.baseUrl}/api/storage`;

  async getSymbols(options: GetSymbolsOptions = {}): Promise<SymbolList> {
    const params = new URLSearchParams();
    if (options.tier !== undefined) {
      params.append('tier', String(options.tier));
    }
    if (options.page !== undefined) {
      params.append('page', String(options.page));
    }
    if (options.limit !== undefined) {
      params.append('limit', String(options.limit));
    }

    const response = await fetch(`${this.storageUrl}/symbols?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch symbols: ${response.statusText}`);
    }
    return response.json();
  }

  // Tier 1 Polyhedra API
  async getPolyhedraList(page = 0, limit = 20): Promise<{ total: number; items: Polyhedron[] }> {
    const response = await fetch(`${this.tier1Url}/polyhedra?skip=${page * limit}&limit=${limit}`);
    if (!response.ok) {
      // Fallback to empty list if API not available
      console.warn('API not available, returning empty list');
      return { total: 0, items: [] };
    }
    return response.json();
  }

  async getPolyhedron(symbol: string): Promise<Polyhedron> {
    const response = await fetch(`${this.tier1Url}/polyhedra/${symbol}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch polyhedron ${symbol}: ${response.statusText}`);
    }
    return response.json();
  }

  async getPolyhedronLOD(symbol: string, level: 'full' | 'medium' | 'low' | 'thumbnail'): Promise<any> {
    const response = await fetch(`${this.tier1Url}/polyhedra/${symbol}/lod/${level}`);
    if (!response.ok) {
      // Fallback to basic geometry
      console.warn(`LOD not available for ${symbol}, using fallback`);
      return this.getFallbackGeometry(symbol);
    }
    return response.json();
  }

  private getFallbackGeometry(symbol: string): any {
    // Basic fallback geometry for testing
    return {
      vertices: [
        [0, 0, 0],
        [1, 0, 0],
        [0.5, 0.866, 0]
      ],
      indices: [0, 1, 2],
      normals: [[0, 0, 1], [0, 0, 1], [0, 0, 1]]
    };
  }

  async getAttachmentOptions(polygonA: string, polygonB: string): Promise<{ options: AttachmentOption[] }> {
    const response = await fetch(`${this.tier1Url}/attachments/${polygonA}/${polygonB}`);
    if (!response.ok) {
      console.warn(`Attachment options not available for ${polygonA}/${polygonB}`);
      return { options: [] };
    }
    return response.json();
  }

  async getAttachmentMatrix(): Promise<AttachmentMatrix> {
    const response = await fetch(`${this.tier1Url}/attachments/matrix`);
    if (!response.ok) {
      console.warn('Attachment matrix not available');
      return {};
    }
    return response.json();
  }

  async getTier1Stats(): Promise<any> {
    const response = await fetch(`${this.tier1Url}/stats`);
    if (!response.ok) {
      console.warn('Stats not available');
      return { total: 0 };
    }
    return response.json();
  }

  // Storage API
  async expandPolyform(symbol: string): Promise<ExpandedPolyform> {
    const response = await fetch(`${this.storageUrl}/polyform/${symbol}`);
    if (!response.ok) {
      throw new Error(`Failed to expand polyform ${symbol}: ${response.statusText}`);
    }
    return response.json();
  }

  async createPolyform(composition: string, metadata: Record<string, unknown> = {}): Promise<ExpandedPolyform> {
    const response = await fetch(`${this.storageUrl}/polyform`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ composition, metadata }),
    });
    if (!response.ok) {
      throw new Error(`Failed to create polyform: ${response.statusText}`);
    }
    return response.json();
  }

  async getPromotionCandidates(): Promise<TierCandidateResponse> {
    const response = await fetch(`${this.storageUrl}/tier3-tier4/candidates`);
    if (!response.ok) {
      throw new Error(`Failed to fetch promotion candidates: ${response.statusText}`);
    }
    return response.json();
  }

  async getStats(): Promise<StorageStats> {
    const response = await fetch(`${this.storageUrl}/stats`);
    if (!response.ok) {
      throw new Error(`Failed to fetch storage stats: ${response.statusText}`);
    }
    return response.json();
  }

  // Scalar Variants
  async getScalarVariants(baseSymbol?: string, scaleFactor?: number, page = 0, limit = 20) {
    const params = new URLSearchParams();
    if (baseSymbol) params.append('base_symbol', baseSymbol);
    if (scaleFactor) params.append('scale_factor', scaleFactor.toString());
    params.append('page', page.toString());
    params.append('limit', limit.toString());

    const response = await fetch(`${this.baseUrl}/api/scalar/variants?${params}`);
    if (!response.ok) throw new Error(`Failed to fetch scalar variants: ${response.statusText}`);
    return response.json();
  }

  // Attachment Patterns
  async getAttachmentPatterns(patternType?: string, minLength?: number, page = 0, limit = 20) {
    const params = new URLSearchParams();
    if (patternType) params.append('pattern_type', patternType);
    if (minLength) params.append('min_length', minLength.toString());
    params.append('page', page.toString());
    params.append('limit', limit.toString());

    const response = await fetch(`${this.baseUrl}/api/patterns/patterns?${params}`);
    if (!response.ok) throw new Error(`Failed to fetch attachment patterns: ${response.statusText}`);
    return response.json();
  }

  // Polyform Generation
  async generatePolyform(request: {
    polygonA: string;
    polygonB: string;
    mode?: string;
    maxSteps?: number;
    attachmentOption?: any;
  }): Promise<{
    success: boolean;
    symbol?: string;
    unicode?: string;
    composition?: string;
    geometry?: any;
    metadata?: any;
    compressionRatio?: number;
    error?: string;
  }> {
    const response = await fetch(`${this.baseUrl}/api/polyform/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(error.error || `Failed to generate polyform: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  // Generated Polyforms Management
  async getGeneratedPolyforms(): Promise<{
    polyforms: Array<{
      symbol: string;
      metadata: any;
      geometry: any;
      composition: string;
    }>;
    total: number;
    error?: string;
  }> {
    const response = await fetch(`${this.baseUrl}/api/polyform/generated`);
    if (!response.ok) {
      throw new Error(`Failed to fetch generated polyforms: ${response.statusText}`);
    }
    return response.json();
  }

  async getGeneratedPolyform(composition: string): Promise<{
    success: boolean;
    polyform?: any;
    error?: string;
  }> {
    const response = await fetch(`${this.baseUrl}/api/polyform/generated/${encodeURIComponent(composition)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch generated polyform: ${response.statusText}`);
    }
    return response.json();
  }

  async getStorageStats(): Promise<{
    success: boolean;
    stats?: {
      total_polyforms: number;
      average_compression_ratio: number;
      storage_type: string;
    };
    error?: string;
  }> {
    const response = await fetch(`${this.baseUrl}/api/polyform/stats`);
    if (!response.ok) {
      throw new Error(`Failed to fetch storage stats: ${response.statusText}`);
    }
    return response.json();
  }
}

export const storageService = new StorageService();