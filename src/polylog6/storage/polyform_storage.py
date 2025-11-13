"""Storage system for polyforms using tiered Unicode compression."""
from .encoder import TieredUnicodeEncoder
import json
import mmap

class PolyformStorage:
    """Stores polyforms with efficient Unicode-based compression."""
    
    def __init__(self, use_mmap=False):
        self.encoder = TieredUnicodeEncoder()
        self.store = {}
        self.use_mmap = use_mmap
        if use_mmap:
            self.file = open("polyform_store.dat", "w+b")
            self.mmap = mmap.mmap(self.file.fileno(), 0)
    
    def add(self, polyform_id: str, data: dict, frequency: int):
        """Add a polyform to storage."""
        symbol = self.encoder.allocate(polyform_id, frequency)
        if self.use_mmap:
            # Store in memory-mapped file
            pos = self.mmap.tell()
            self.mmap.write(json.dumps(data).encode('utf-8'))
            return f"mmap:{pos}"
        else:
            self.store[symbol] = data
            return symbol
    
    def get(self, symbol: str) -> dict:
        """Retrieve polyform data by symbol."""
        if symbol.startswith("mmap:"):
            pos = int(symbol[5:])
            self.mmap.seek(pos)
            data = self.mmap.read()
            return json.loads(data.decode('utf-8'))
        else:
            return self.store.get(symbol)
