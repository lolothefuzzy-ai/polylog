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

export class StorageService {
  private readonly baseUrl = '/api/storage';

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

    const response = await fetch(`${this.baseUrl}/symbols?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch symbols: ${response.statusText}`);
    }
    return response.json();
  }

  async expandPolyform(symbol: string): Promise<ExpandedPolyform> {
    const response = await fetch(`${this.baseUrl}/polyform/${symbol}`);
    if (!response.ok) {
      throw new Error(`Failed to expand polyform ${symbol}: ${response.statusText}`);
    }
    return response.json();
  }

  async createPolyform(composition: string, metadata: Record<string, unknown> = {}): Promise<ExpandedPolyform> {
    const response = await fetch(`${this.baseUrl}/polyform`, {
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
    const response = await fetch(`${this.baseUrl}/tier3-tier4/candidates`);
    if (!response.ok) {
      throw new Error(`Failed to fetch promotion candidates: ${response.statusText}`);
    }
    return response.json();
  }

  async getStats(): Promise<StorageStats> {
    const response = await fetch(`${this.baseUrl}/stats`);
    if (!response.ok) {
      throw new Error(`Failed to fetch storage stats: ${response.statusText}`);
    }
    return response.json();
  }
}

export const storageService = new StorageService();
