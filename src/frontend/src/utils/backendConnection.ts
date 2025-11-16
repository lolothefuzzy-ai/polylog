/**
 * Backend connection utilities
 * Handles connection to backend API and provides fallbacks
 */

import { storageService } from '../services/storageService';

export interface BackendStatus {
  connected: boolean;
  apiUrl: string;
  error?: string;
}

export async function checkBackendConnection(): Promise<BackendStatus> {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  
  try {
    const response = await fetch(`${apiUrl}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(2000) // 2 second timeout
    });
    
    if (response.ok) {
      return { connected: true, apiUrl };
    } else {
      return { connected: false, apiUrl, error: `HTTP ${response.status}` };
    }
  } catch (error: any) {
    return { 
      connected: false, 
      apiUrl, 
      error: error.message || 'Connection failed' 
    };
  }
}

export async function loadPolyhedraWithFallback() {
  try {
    // Try backend first
    const data = await storageService.getPolyhedraList(0, 100);
    if (data?.items && data.items.length > 0) {
      return data.items;
    }
  } catch (error) {
    console.warn('Backend not available, using fallback data:', error);
  }
  
  // Fallback: Return basic primitives
  return generateFallbackPrimitives();
}

function generateFallbackPrimitives() {
  const symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R'];
  const names = ['Triangle', 'Square', 'Pentagon', 'Hexagon', 'Heptagon', 'Octagon', 'Nonagon', 'Decagon', 
                'Hendecagon', 'Dodecagon', 'Tridecagon', 'Tetradecagon', 'Pentadecagon', 'Hexadecagon',
                'Heptadecagon', 'Octadecagon', 'Enneadecagon', 'Icosagon'];
  const sides = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];
  
  return symbols.map((symbol, i) => ({
    symbol,
    name: names[i],
    sides: sides[i],
    classification: 'primitive' as const,
    vertices: generatePrimitiveVertices(sides[i]),
    compression_ratio: 500
  }));
}

function generatePrimitiveVertices(sides: number): number[][] {
  const vertices: number[][] = [];
  const radius = 1.0;
  
  for (let i = 0; i < sides; i++) {
    const angle = (i * 2 * Math.PI) / sides;
    vertices.push([
      radius * Math.cos(angle),
      radius * Math.sin(angle),
      0 // Start in 3D space (z=0 plane)
    ]);
  }
  
  return vertices;
}

