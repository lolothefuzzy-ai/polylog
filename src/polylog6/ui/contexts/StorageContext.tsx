// Storage Context wiring for the StorageService abstraction.
import React from 'react';
import { StorageService, storageService } from '../../../services/storageService';

export const StorageContext = React.createContext<StorageService>(storageService);

interface StorageProviderProps {
  service?: StorageService;
  children: React.ReactNode;
}

export const StorageProvider: React.FC<StorageProviderProps> = ({ service = storageService, children }) => {
  return <StorageContext.Provider value={service}>{children}</StorageContext.Provider>;
};
