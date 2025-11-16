import React, { useState, useEffect } from 'react';
import { storageService } from '../services/storageService';

export function AttachmentValidator({ polygonA, polygonB, onSelect }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (polygonA && polygonB) {
      loadAttachmentOptions();
    } else {
      setOptions([]);
    }
  }, [polygonA, polygonB]);

  const loadAttachmentOptions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await storageService.getAttachmentOptions(polygonA, polygonB);
      setOptions(data.options || []);
    } catch (err) {
      console.error('Failed to load attachment options:', err);
      setError(err.message);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (option) => {
    setSelected(option);
    if (onSelect) {
      onSelect(option);
    }
  };

  const getStabilityClass = (stability) => {
    if (stability >= 0.85) return 'stable-high';
    if (stability >= 0.70) return 'stable-medium';
    if (stability >= 0.50) return 'stable-low';
    return 'unstable';
  };

  const getStabilityLabel = (stability) => {
    if (stability >= 0.85) return 'Stable';
    if (stability >= 0.70) return 'Conditional';
    if (stability >= 0.50) return 'Unstable';
    return 'Invalid';
  };

  if (!polygonA || !polygonB) {
    return (
      <div className="attachment-validator">
        <div className="validator-empty">
          Select two polygons to see attachment options
        </div>
      </div>
    );
  }

  return (
    <div className="attachment-validator">
      <div className="validator-header">
        <h3>Valid Attachments</h3>
        <div className="validator-pair">
          {polygonA} ↔ {polygonB}
        </div>
      </div>

      {loading && (
        <div className="validator-loading">Loading options...</div>
      )}

      {error && (
        <div className="validator-error">
          Error: {error}
          <button onClick={loadAttachmentOptions}>Retry</button>
        </div>
      )}

      {!loading && !error && options.length === 0 && (
        <div className="validator-empty">
          No valid attachments found for this pair
        </div>
      )}

      {!loading && !error && options.length > 0 && (
        <div className="validator-options">
          {options.map((opt, idx) => (
            <div
              key={idx}
              className={`validator-option ${getStabilityClass(opt.stability)} ${
                selected === opt ? 'selected' : ''
              }`}
              onClick={() => handleSelect(opt)}
            >
              <div className="option-header">
                <div className="option-angle">
                  {opt.fold_angle.toFixed(1)}°
                </div>
                <div className={`option-stability ${getStabilityClass(opt.stability)}`}>
                  {getStabilityLabel(opt.stability)}
                </div>
              </div>
              <div className="option-stability-score">
                Score: {opt.stability.toFixed(2)}
              </div>
              {opt.context && (
                <div className="option-context">{opt.context}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

