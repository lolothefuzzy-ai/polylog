// Symbol palette UI component for selecting Unicode polyforms.
import React from 'react';
import { useSymbols } from '../hooks/useSymbols';
import type { SymbolList } from '../../../services/storageService';

interface SymbolPaletteProps {
  onSelect: (symbol: string) => void;
  tier?: 0 | 1 | 3 | 4;
  page?: number;
  limit?: number;
}

export const SymbolPalette: React.FC<SymbolPaletteProps> = ({ onSelect, tier = 0, page = 0, limit = 100 }) => {
  const { data, isLoading, error } = useSymbols({ tier, page, limit });

  if (isLoading) {
    return <div className="symbol-palette symbol-palette--loading">Loading symbols…</div>;
  }

  if (error) {
    return (
      <div className="symbol-palette symbol-palette--error" role="alert">
        Failed to load symbols: {error.message}
      </div>
    );
  }

  const symbols: SymbolList['symbols'] = data?.symbols ?? [];

  return (
    <div className="symbol-palette" data-testid="symbol-palette">
      {symbols.map((summary: SymbolList['symbols'][number]) => (
        <button
          key={summary.symbol}
          data-testid="symbol-item"
          className="symbol-palette__button"
          onClick={() => onSelect(summary.symbol)}
        >
          {summary.symbol}
        </button>
      ))}
    </div>
  );
};

export default SymbolPalette;
