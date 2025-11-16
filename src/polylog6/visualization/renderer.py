"""Renderer for polyform visualization using Unicode symbols."""
from polylog6.storage.polyform_storage import PolyformStorage


class Renderer:
    """Renders polyforms using their Unicode symbols."""
    
    def __init__(self, storage: PolyformStorage):
        self.storage = storage
    
    def render(self, entity) -> str:
        """Render an entity as its Unicode symbol."""
        return entity.symbol  # Directly use stored symbol
