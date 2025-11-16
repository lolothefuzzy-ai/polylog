"""Storage system for polyforms using tiered Unicode compression."""
from .encoder import TieredUnicodeEncoder
import json
import mmap
from typing import Dict, List, Optional, Any
from pathlib import Path

class PolyformStorage:
    """Stores polyforms with efficient Unicode-based compression."""
    
    def __init__(self, use_mmap=False, storage_path: Optional[Path] = None):
        self.encoder = TieredUnicodeEncoder()
        self.store = {}
        self.metadata = {}
        self.use_mmap = use_mmap
        self._mmap_data = {}  # Track mmap data positions and sizes
        
        if storage_path is None:
            storage_path = Path("polyform_store.dat")
        self.storage_path = storage_path
        
        if use_mmap:
            self.file = open(storage_path, "w+b")
            # Initialize file with some data to allow mmap
            self.file.write(b'\x00' * 1024)  # Write 1KB of null bytes
            self.file.flush()
            self.file.seek(0)
            self.mmap = mmap.mmap(self.file.fileno(), 0)
    
    def add(self, polyform_id: str, data: dict, frequency: int) -> str:
        """Add a polyform to storage."""
        symbol = self.encoder.allocate(polyform_id, frequency)
        
        # Store metadata
        self.metadata[symbol] = {
            "polyform_id": polyform_id,
            "frequency": frequency,
            "created_at": json.dumps({"timestamp": "now"}),  # Simplified
            "compression_ratio": data.get("compression_ratio", 0)
        }
        
        if self.use_mmap:
            # Store in memory-mapped file
            pos = self.mmap.tell()
            json_data = json.dumps(data).encode('utf-8')
            self.mmap.write(json_data)
            
            # Track data position and size for retrieval
            self._mmap_data[symbol] = {
                "pos": pos,
                "size": len(json_data)
            }
            
            return f"mmap:{pos}"
        else:
            self.store[symbol] = data
            return symbol
    
    def get(self, symbol: str) -> Optional[dict]:
        """Retrieve polyform data by symbol."""
        if symbol.startswith("mmap:"):
            pos = int(symbol[5:])
            # Find the corresponding symbol to get size
            data_size = None
            for sym, info in self._mmap_data.items():
                if info["pos"] == pos:
                    data_size = info["size"]
                    break
            
            if data_size is None:
                return None
                
            self.mmap.seek(pos)
            data = self.mmap.read(data_size)
            return json.loads(data.decode('utf-8'))
        else:
            return self.store.get(symbol)
    
    def get_metadata(self, symbol: str) -> Optional[dict]:
        """Get metadata for a stored polyform."""
        return self.metadata.get(symbol)
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all stored polyforms with metadata."""
        results = []
        for symbol, data in self.store.items():
            metadata = self.metadata.get(symbol, {})
            results.append({
                "symbol": symbol,
                "metadata": metadata,
                "geometry": data.get("geometry", {}),
                "composition": data.get("composition", "")
            })
        return results
    
    def get_by_composition(self, composition: str) -> Optional[dict]:
        """Find polyform by composition string."""
        for symbol, metadata in self.metadata.items():
            if metadata.get("polyform_id") == composition:
                return self.get(symbol)
        return None
    
    def update_frequency(self, symbol: str, new_frequency: int) -> bool:
        """Update frequency for a stored polyform."""
        if symbol in self.metadata:
            self.metadata[symbol]["frequency"] = new_frequency
            return True
        return False
    
    def delete(self, symbol: str) -> bool:
        """Delete a polyform from storage."""
        if symbol in self.store:
            del self.store[symbol]
            if symbol in self.metadata:
                del self.metadata[symbol]
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_polyforms = len(self.store)
        avg_compression = 0
        if self.metadata:
            ratios = [m.get("compression_ratio", 0) for m in self.metadata.values()]
            avg_compression = sum(ratios) / len(ratios) if ratios else 0
        
        return {
            "total_polyforms": total_polyforms,
            "average_compression_ratio": avg_compression,
            "storage_type": "mmap" if self.use_mmap else "memory"
        }