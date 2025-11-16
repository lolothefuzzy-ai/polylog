import React, { useState, useEffect } from 'react';
import { storageService } from '../services/storageService';
import './PolyformGenerator.css';

export function PolyformGenerator({ selectedPolyhedra, onPolyformGenerated }) {
  const [generating, setGenerating] = useState(false);
  const [generatedPolyforms, setGeneratedPolyforms] = useState([]);
  const [error, setError] = useState(null);
  const [generationMode, setGenerationMode] = useState('linear'); // 'linear' or 'exponential'
  const [storageStats, setStorageStats] = useState(null);

  const canGenerate = selectedPolyhedra.length >= 2;

  // Load existing generated polyforms on mount
  useEffect(() => {
    loadGeneratedPolyforms();
    loadStorageStats();
  }, []);

  const loadGeneratedPolyforms = async () => {
    try {
      const response = await storageService.getGeneratedPolyforms();
      if (response.error) {
        console.warn('Could not load generated polyforms:', response.error);
        return;
      }
      setGeneratedPolyforms(response.polyforms || []);
    } catch (err) {
      console.warn('Error loading generated polyforms:', err);
    }
  };

  const loadStorageStats = async () => {
    try {
      const response = await storageService.getStorageStats();
      if (response.success) {
        setStorageStats(response.stats);
      }
    } catch (err) {
      console.warn('Error loading storage stats:', err);
    }
  };

  const handleGenerate = async () => {
    if (!canGenerate) return;

    setGenerating(true);
    setError(null);

    try {
      // Get last two selected polyhedra
      const polyA = selectedPolyhedra[selectedPolyhedra.length - 2];
      const polyB = selectedPolyhedra[selectedPolyhedra.length - 1];

      // Call generation API
      const response = await storageService.generatePolyform({
        polygonA: polyA.symbol,
        polygonB: polyB.symbol,
        mode: generationMode,
        maxSteps: 5
      });

      if (response.success) {
        const newPolyform = {
          symbol: response.symbol,
          composition: response.composition,
          metadata: response.metadata,
          geometry: response.geometry,
          unicode: response.unicode,
          compressionRatio: response.compressionRatio
        };

        setGeneratedPolyforms(prev => [newPolyform, ...prev]);
        
        // Refresh storage stats
        loadStorageStats();
        
        if (onPolyformGenerated) {
          onPolyformGenerated(newPolyform);
        }
      } else {
        setError(response.error || 'Generation failed');
      }
    } catch (err) {
      setError(err.message || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleLoadPolyform = async (composition) => {
    try {
      const response = await storageService.getGeneratedPolyform(composition);
      if (response.success && onPolyformGenerated) {
        onPolyformGenerated(response.polyform);
      }
    } catch (err) {
      setError(`Failed to load polyform: ${err.message}`);
    }
  };

  const handleDeletePolyform = async (composition) => {
    try {
      // Note: Delete endpoint not implemented yet
      console.warn('Delete functionality not yet implemented');
      // For now, just refresh the list
      loadGeneratedPolyforms();
    } catch (err) {
      setError(`Failed to delete polyform: ${err.message}`);
    }
  };

  return (
    <div className="polyform-generator">
      <h3>Polyform Generator</h3>
      
      {/* Generation Controls */}
      <div className="generation-controls">
        <div className="mode-selector">
          <label>Generation Mode:</label>
          <select 
            value={generationMode} 
            onChange={(e) => setGenerationMode(e.target.value)}
            disabled={generating}
          >
            <option value="linear">Linear</option>
            <option value="exponential">Exponential</option>
          </select>
        </div>
        
        <button 
          className="generate-btn"
          onClick={handleGenerate}
          disabled={!canGenerate || generating}
        >
          {generating ? 'Generating...' : 'Generate Polyform'}
        </button>
        
        {!canGenerate && (
          <small className="help-text">
            Select at least 2 polyhedra to generate a polyform
          </small>
        )}
      </div>

      {/* Storage Stats */}
      {storageStats && (
        <div className="storage-stats">
          <h4>Storage Statistics</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <label>Total Polyforms:</label>
              <span>{storageStats.total_polyforms}</span>
            </div>
            <div className="stat-item">
              <label>Avg Compression:</label>
              <span>{storageStats.average_compression_ratio.toFixed(2)}</span>
            </div>
            <div className="stat-item">
              <label>Storage Type:</label>
              <span>{storageStats.storage_type}</span>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Generated Polyforms List */}
      {generatedPolyforms.length > 0 && (
        <div className="generated-polyforms">
          <h4>Generated Polyforms ({generatedPolyforms.length})</h4>
          <div className="polyforms-list">
            {generatedPolyforms.map((polyform, index) => (
              <div key={index} className="polyform-item">
                <div className="polyform-header">
                  <span className="composition">{polyform.composition}</span>
                  <span className="unicode">({polyform.unicode})</span>
                </div>
                
                <div className="polyform-details">
                  <div className="detail-item">
                    <label>Compression:</label>
                    <span>{(polyform.compressionRatio || 0).toFixed(2)}x</span>
                  </div>
                  
                  {polyform.metadata && (
                    <>
                      <div className="detail-item">
                        <label>Polygons:</label>
                        <span>{polyform.metadata.polygon_count || 0}</span>
                      </div>
                      <div className="detail-item">
                        <label>Stability:</label>
                        <span>{(polyform.metadata.stability || 0).toFixed(3)}</span>
                      </div>
                    </>
                  )}
                </div>
                
                <div className="polyform-actions">
                  <button 
                    className="load-btn"
                    onClick={() => handleLoadPolyform(polyform.composition)}
                  >
                    Load in Scene
                  </button>
                  <button 
                    className="delete-btn"
                    onClick={() => handleDeletePolyform(polyform.composition)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {generatedPolyforms.length === 0 && !generating && (
        <div className="empty-state">
          <p>No polyforms generated yet. Select polyhedra and click Generate to create your first polyform.</p>
        </div>
      )}
    </div>
  );
}