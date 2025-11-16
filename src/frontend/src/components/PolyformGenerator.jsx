import React, { useState } from 'react';
import { storageService } from '../services/storageService';
import './PolyformGenerator.css';

export function PolyformGenerator({ selectedPolyhedra, onPolyformGenerated }) {
  const [generating, setGenerating] = useState(false);
  const [generatedPolyforms, setGeneratedPolyforms] = useState([]);
  const [error, setError] = useState(null);
  const [generationMode, setGenerationMode] = useState('linear'); // 'linear' or 'exponential'

  const canGenerate = selectedPolyhedra.length >= 2;

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
        
        if (onPolyformGenerated) {
          onPolyformGenerated(newPolyform);
        }
      } else {
        setError(response.error || 'Generation failed');
      }
    } catch (err) {
      console.error('Generation error:', err);
      setError(err.message || 'Failed to generate polyform');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="polyform-generator">
      <div className="generator-header">
        <h3>Polyform Generator</h3>
        <div className="generator-status">
          {selectedPolyhedra.length >= 2 ? (
            <span className="status-ready">Ready to generate</span>
          ) : (
            <span className="status-waiting">Select 2+ polygons</span>
          )}
        </div>
      </div>

      {selectedPolyhedra.length >= 2 && (
        <div className="generator-controls">
          <div className="control-group">
            <label>Generation Mode:</label>
            <select 
              value={generationMode} 
              onChange={(e) => setGenerationMode(e.target.value)}
              disabled={generating}
            >
              <option value="linear">Linear (1→2→3)</option>
              <option value="exponential">Exponential (1→2→4)</option>
            </select>
          </div>

          <button
            className="generate-button"
            onClick={handleGenerate}
            disabled={!canGenerate || generating}
          >
            {generating ? 'Generating...' : 'Generate Polyform'}
          </button>
        </div>
      )}

      {error && (
        <div className="generator-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {generatedPolyforms.length > 0 && (
        <div className="generated-polyforms">
          <h4>Generated Polyforms ({generatedPolyforms.length})</h4>
          <div className="polyform-list">
            {generatedPolyforms.map((polyform, idx) => (
              <div key={idx} className="generated-polyform-item">
                <div className="polyform-symbol">{polyform.symbol || polyform.unicode}</div>
                <div className="polyform-info">
                  <div className="polyform-composition">{polyform.composition}</div>
                  {polyform.compressionRatio && (
                    <div className="polyform-compression">
                      Compression: {polyform.compressionRatio.toFixed(1)}:1
                    </div>
                  )}
                  {polyform.metadata?.polygon_count && (
                    <div className="polyform-count">
                      {polyform.metadata.polygon_count} polygons
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!canGenerate && (
        <div className="generator-hint">
          Select at least 2 polygons from the library to generate a new polyform
        </div>
      )}
    </div>
  );
}

