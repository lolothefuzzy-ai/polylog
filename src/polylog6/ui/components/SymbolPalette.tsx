// Symbol palette UI component for selecting Unicode polyforms.
import React, { useContext } from 'react';
import { StorageContext } from '../contexts/StorageContext';

interface SymbolPaletteProps {
  onSelect: (symbol: string) => void;
}

export const SymbolPalette: React.FC<SymbolPaletteProps> = ({ onSelect }) => {
  const storageContext = useContext(StorageContext);
  
  if (!storageContext) {
    return <div>Loading...</div>;
  }
  
  const { symbols } = storageContext;
  
  return (
    <div className="symbol-palette">
      {symbols.map((symbol) => (
        <button
          key={symbol}
          className="symbol-palette__button"
          onClick={() => onSelect(symbol)}
        >
          {symbol}
        </button>
      ))}
    </div>
  );
};

export default SymbolPalette;
