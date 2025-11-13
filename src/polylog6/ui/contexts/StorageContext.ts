"""
Storage Context
"""
import React from 'react';
import { PolyformStorage } from '../../../storage/polyform_storage';

interface StorageContextValue {
  storage: PolyformStorage;
  symbols: string[];
}

export const StorageContext = React.createContext<StorageContextValue | null>(null);

interface StorageProviderProps {
  storage: PolyformStorage;
  symbols: string[];
  children: React.ReactNode;
}

export const StorageProvider: React.FC<StorageProviderProps> = ({ 
  storage, 
  symbols, 
  children 
}) => {
  return (
    <StorageContext.Provider value={{ storage, symbols }}>
      {children}
    </StorageContext.Provider>
  );
};
