import { useQuery, UseQueryResult } from '@tanstack/react-query';

import type { SymbolList } from '../../../services/storageService';
import { useStorage } from './useStorage';

export interface UseSymbolsOptions {
  tier?: 0 | 1 | 3 | 4;
  page?: number;
  limit?: number;
}

export const useSymbols = (options: UseSymbolsOptions = {}): UseQueryResult<SymbolList> => {
  const storage = useStorage();

  const {
    tier,
    page = 0,
    limit = 100,
  } = options;

  return useQuery<SymbolList>({
    queryKey: ['symbols', tier ?? 'all', page, limit],
    queryFn: () => storage.getSymbols({ tier, page, limit }),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  });
};
