import React, { useState, useEffect } from 'react';
import { storageService } from '../services/storageService';

export function PolyhedraLibrary({ onSelect }) {
  const [polyhedra, setPolyhedra] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadPolyhedra();
  }, [page, filter]);

  const loadPolyhedra = async () => {
    try {
      setLoading(true);
      // Load base polyhedra
      const baseData = await storageService.getPolyhedraList(page, 20);
      const baseItems = baseData.items || [];
      
      // Load scalar variants for first page
      if (page === 0) {
        try {
          const scalarData = await storageService.getScalarVariants(undefined, undefined, 0, 100);
          const scalarItems = (scalarData.items || []).map(v => ({
            ...v,
            name: v.name || `${v.base_symbol || v.symbol} (k=${v.scale_factor || 1})`,
            classification: 'scalar_variant'
          }));
          
          // Combine base and scalar variants
          setPolyhedra([...baseItems, ...scalarItems]);
          setTotal((baseData.total || 0) + (scalarData.total || 0));
        } catch (scalarErr) {
          // Fallback to base only if scalar variants fail
          console.warn('Could not load scalar variants:', scalarErr);
          setPolyhedra(baseItems);
          setTotal(baseData.total || 0);
        }
      } else {
        setPolyhedra(baseItems);
        setTotal(baseData.total || 0);
      }
      
      setError(null);
    } catch (err) {
      console.error('Failed to load polyhedra:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filtered = polyhedra.filter(p => {
    if (search && !p.symbol.toLowerCase().includes(search.toLowerCase()) && 
        !p.name?.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }
    if (filter === 'all') return true;
    if (filter === 'platonic') return p.classification === 'platonic';
    if (filter === 'archimedean') return p.classification === 'archimedean';
    if (filter === 'johnson') return p.classification === 'johnson';
    if (filter === 'scalar_variant') return p.classification === 'scalar_variant' || p.is_scalar_variant;
    return true;
  });

  const handleSelect = (poly) => {
    if (onSelect) {
      onSelect(poly);
    }
  };

  const handleDragStart = (e, poly) => {
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('application/json', JSON.stringify(poly));
    e.dataTransfer.setData('text/plain', poly.symbol);
  };

  if (loading && polyhedra.length === 0) {
    return (
      <div className="polyhedra-library loading">
        <div>Loading polyhedra...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="polyhedra-library error">
        <div>Error: {error}</div>
        <button onClick={loadPolyhedra}>Retry</button>
      </div>
    );
  }

  return (
    <div className="polyhedra-library">
      <div className="library-header">
        <h3>Polyhedra Library</h3>
        <div className="library-stats">{total} total</div>
      </div>

      <div className="library-controls">
        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="library-search"
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="library-filter"
        >
          <option value="all">All ({total})</option>
          <option value="platonic">Platonic (5)</option>
          <option value="archimedean">Archimedean (13)</option>
          <option value="johnson">Johnson (79)</option>
          <option value="scalar_variant">Scalar Variants</option>
        </select>
      </div>

      <div className="library-grid">
        {filtered.map(p => (
          <div
            key={p.symbol}
            className="library-item"
            draggable={true}
            onDragStart={(e) => handleDragStart(e, p)}
            onClick={() => handleSelect(p)}
            title={p.name || p.symbol}
          >
            <div className="item-symbol">{p.symbol}</div>
            <div className="item-name">{p.name || p.symbol}</div>
            {p.compression_ratio && (
              <div className="item-compression">
                {p.compression_ratio.toFixed(1)}:1
              </div>
            )}
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="library-empty">
          No polyhedra found matching your search.
        </div>
      )}

      <div className="library-pagination">
        <button
          disabled={page === 0}
          onClick={() => setPage(p => Math.max(0, p - 1))}
        >
          Previous
        </button>
        <span>Page {page + 1}</span>
        <button
          disabled={(page + 1) * 20 >= total}
          onClick={() => setPage(p => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}

