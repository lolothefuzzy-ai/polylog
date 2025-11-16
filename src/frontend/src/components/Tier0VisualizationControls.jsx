/**
 * Tier 0 Visualization Controls
 * Advanced controls for visualizing Tier 0 symbols, atomic chains, and scaffolds
 */

import React, { useState } from 'react';
import { visualizeTier0Symbol, visualizeAtomicChain, visualizeScaffold } from '../utils/tier0Visualizer.js';
import { getWorkspaceEntryPoint } from '../utils/workspaceEntryPoint.js';
import { detectAtomicChain, getJohnsonSolidScaffold } from '../services/tier0Service.js';
import './Tier0VisualizationControls.css';

export function Tier0VisualizationControls({ scene }) {
  const [selectedChain, setSelectedChain] = useState(null);
  const [visualizationType, setVisualizationType] = useState('tier0'); // 'tier0', 'atomic', 'scaffold'

  const handleVisualizeChain = async () => {
    if (!selectedChain || !scene) return;

    const workspace = getWorkspaceEntryPoint();
    if (!workspace.isInitialized()) return;

    const chain = workspace.getChainForPolygon(selectedChain);
    if (!chain || !chain.tier0Symbol) {
      console.warn('[Tier0VisualizationControls] No Tier 0 symbol for selected chain');
      return;
    }

    try {
      if (visualizationType === 'tier0') {
        await visualizeTier0Symbol(chain.tier0Symbol, scene);
      } else if (visualizationType === 'atomic') {
        const atomicChain = await detectAtomicChain(chain.tier0Symbol);
        if (atomicChain) {
          await visualizeAtomicChain(atomicChain, scene);
        }
      } else if (visualizationType === 'scaffold') {
        // Try to get scaffold for Johnson solid
        const scaffold = await getJohnsonSolidScaffold('square_pyramid');
        if (scaffold) {
          await visualizeScaffold(scaffold, scene);
        }
      }
    } catch (error) {
      console.error('[Tier0VisualizationControls] Visualization error:', error);
    }
  };

  const workspace = getWorkspaceEntryPoint();
  const chains = workspace.isInitialized() ? workspace.getAllChains() : [];

  return (
    <div className="tier0-visualization-controls">
      <h4>Visualization Controls</h4>
      
      <div className="control-group">
        <label>Select Chain:</label>
        <select 
          value={selectedChain || ''} 
          onChange={(e) => setSelectedChain(e.target.value)}
        >
          <option value="">-- Select Chain --</option>
          {chains.map(chain => (
            <option key={chain.id} value={chain.polygonIds[0]}>
              {chain.id} {chain.tier0Symbol ? `(${chain.tier0Symbol})` : ''}
            </option>
          ))}
        </select>
      </div>

      <div className="control-group">
        <label>Visualization Type:</label>
        <select 
          value={visualizationType} 
          onChange={(e) => setVisualizationType(e.target.value)}
        >
          <option value="tier0">Tier 0 Symbol</option>
          <option value="atomic">Atomic Chain</option>
          <option value="scaffold">Scaffold</option>
        </select>
      </div>

      <button 
        className="visualize-btn"
        onClick={handleVisualizeChain}
        disabled={!selectedChain || !scene}
      >
        Visualize
      </button>
    </div>
  );
}

