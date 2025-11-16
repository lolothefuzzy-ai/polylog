/**
 * Tier 0 Display Component
 * Shows Tier 0 symbols, atomic chain types, and scaffold information
 */

import React, { useState, useEffect } from 'react';
import { getWorkspaceEntryPoint } from '../utils/workspaceEntryPoint.js';
import { getAtomicChainLibrary } from '../services/tier0Service.js';
import './Tier0Display.css';

export function Tier0Display({ scene = null }) {
  const [chains, setChains] = useState([]);
  const [showVisualization, setShowVisualization] = useState(true); // Default to showing
  const [atomicChains, setAtomicChains] = useState([]);

  useEffect(() => {
    // Update chains when workspace changes
    const updateChains = () => {
      const workspace = getWorkspaceEntryPoint();
      if (workspace.isInitialized()) {
        const allChains = workspace.getAllChains();
        setChains(allChains);
      }
    };

    // Poll for updates (could be replaced with event system)
    const interval = setInterval(updateChains, 1000);
    updateChains();

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Load atomic chain library
    fetchAtomicChainLibrary().then(library => {
      if (library) {
        const allChains = [
          ...(library.square_chains || []),
          ...(library.triangle_clusters || []),
          ...(library.mixed_chains || [])
        ];
        setAtomicChains(allChains);
      }
    }).catch(err => {
      console.warn('[Tier0Display] Error loading atomic chain library:', err);
    });
  }, []);

  return (
    <div className="tier0-display">
      <div className="tier0-header">
        <h3>Tier 0 Symbols</h3>
        <label className="toggle-visualization">
          <input
            type="checkbox"
            checked={showVisualization}
            onChange={(e) => {
              setShowVisualization(e.target.checked);
              // Dispatch event to BabylonScene
              window.dispatchEvent(new CustomEvent('tier0-visualization-toggle', {
                detail: { enabled: e.target.checked }
              }));
            }}
          />
          Show Visualization
        </label>
      </div>

      <div className="chains-list">
        {chains.length === 0 ? (
          <div className="empty-state">
            No chains yet. Attach polygons to create chains.
          </div>
        ) : (
          chains.map(chain => (
            <div key={chain.id} className="chain-item">
              <div className="chain-header">
                <span className="chain-id">Chain {chain.id}</span>
                {chain.tier0Symbol && (
                  <span className="tier0-symbol">{chain.tier0Symbol}</span>
                )}
              </div>
              
              {chain.tier0Symbol && (
                <div className="chain-details">
                  <div className="polygon-count">
                    {chain.polygonIds.length} polygon{chain.polygonIds.length !== 1 ? 's' : ''}
                  </div>
                  
                  {chain.atomicChainType && (
                    <div className="atomic-chain-type">
                      Type: <strong>{chain.atomicChainType}</strong>
                    </div>
                  )}
                  
                  {chain.scaffoldApplications && chain.scaffoldApplications.length > 0 && (
                    <div className="scaffold-applications">
                      Scaffolds: {chain.scaffoldApplications.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {atomicChains.length > 0 && (
        <div className="atomic-chains-library">
          <h4>Atomic Chains Library</h4>
          <div className="library-stats">
            <div>Square Chains: {atomicChains.filter(c => c.chain_type === 'square_chain').length}</div>
            <div>Triangle Clusters: {atomicChains.filter(c => c.chain_type === 'triangle_cluster').length}</div>
            <div>Mixed Chains: {atomicChains.filter(c => c.chain_type === 'mixed_chain').length}</div>
          </div>
        </div>
      )}

      {scene && (
        <Tier0VisualizationControls scene={scene} />
      )}
    </div>
  );
}

