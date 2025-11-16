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
        // First try to load from backend API
        try {
          const data = await storageService.getPolyhedraList(0, 18);
          const items = data?.items || [];
          if (items.length > 0) {
            setPolygons(items);
            setSelectedIndex(0);
            setLoading(false);
            return;
          }
        } catch (apiError) {
          console.warn('Backend API not available, using fallback:', apiError);
        }
        
        // Fallback: Create basic primitives (A-R)
        const fallbackPrimitives = [];
        const symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R'];
        const names = ['Triangle', 'Square', 'Pentagon', 'Hexagon', 'Heptagon', 'Octagon', 'Nonagon', 'Decagon', 
                      'Hendecagon', 'Dodecagon', 'Tridecagon', 'Tetradecagon', 'Pentadecagon', 'Hexadecagon',
                      'Heptadecagon', 'Octadecagon', 'Enneadecagon', 'Icosagon'];
        const sides = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];
        
        for (let i = 0; i < symbols.length; i++) {
          fallbackPrimitives.push({
            symbol: symbols[i],
            name: names[i],
            sides: sides[i],
            classification: 'primitive'
          });
        }
        
        setPolygons(fallbackPrimitives);
        setSelectedIndex(0);
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

