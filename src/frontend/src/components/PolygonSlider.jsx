import React, { useState, useEffect } from 'react';
import { storageService } from '../services/storageService';
import './PolygonSlider.css';

/**
 * Simple polygon slider - minimal initial interface
 * Shows polygon selector until warmup complete
 */
export function PolygonSlider({ onSelect }) {
  const [polygons, setPolygons] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPrimitives = async () => {
      try {
        // Load only primitives (A-R, 18 polygons)
        const data = await storageService.getPolyhedraList();
        const primitives = (data || []).slice(0, 18);
        setPolygons(primitives);
        if (primitives.length > 0) {
          setSelectedIndex(0);
        }
      } catch (error) {
        console.error('Failed to load primitives:', error);
      } finally {
        setLoading(false);
      }
    };
    loadPrimitives();
  }, []);

  const handleSelect = (index) => {
    setSelectedIndex(index);
    if (onSelect && polygons[index]) {
      onSelect(polygons[index]);
    }
  };

  const handleAdd = () => {
    if (polygons[selectedIndex] && onSelect) {
      onSelect(polygons[selectedIndex]);
    }
  };

  if (loading) {
    return (
      <div className="polygon-slider">
        <div className="slider-loading">Loading polygons...</div>
      </div>
    );
  }

  if (polygons.length === 0) {
    return (
      <div className="polygon-slider">
        <div className="slider-error">No polygons available</div>
      </div>
    );
  }

  const currentPoly = polygons[selectedIndex];

  return (
    <div className="polygon-slider">
      <div className="slider-header">
        <h3>Select Polygon</h3>
        <div className="slider-counter">
          {selectedIndex + 1} / {polygons.length}
        </div>
      </div>
      
      <div className="slider-controls">
        <button 
          className="slider-btn prev"
          onClick={() => handleSelect((selectedIndex - 1 + polygons.length) % polygons.length)}
          disabled={polygons.length === 0}
        >
          ←
        </button>
        
        <div className="slider-display">
          <div className="polygon-preview">
            <div className="polygon-symbol">{currentPoly?.symbol || 'A'}</div>
            <div className="polygon-name">{currentPoly?.name || 'Triangle'}</div>
            <div className="polygon-sides">{currentPoly?.sides || 3} sides</div>
          </div>
        </div>
        
        <button 
          className="slider-btn next"
          onClick={() => handleSelect((selectedIndex + 1) % polygons.length)}
          disabled={polygons.length === 0}
        >
          →
        </button>
      </div>

      <button 
        className="slider-add-btn"
        onClick={handleAdd}
        disabled={!currentPoly}
      >
        Add to Workspace
      </button>

      <div className="slider-indicators">
        {polygons.slice(0, 10).map((poly, idx) => (
          <button
            key={idx}
            className={`slider-dot ${idx === selectedIndex ? 'active' : ''}`}
            onClick={() => handleSelect(idx)}
            title={poly.name || poly.symbol}
          />
        ))}
      </div>
    </div>
  );
}

