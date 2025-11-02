"""
Base Protocol for Polyform Generation Engines

Defines standardized interface that all generators must implement
for consistent behavior across the unified system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol


class GeneratorProtocol(Protocol):
    """Protocol defining required methods for all generators."""
    
    def generate(self, **kwargs) -> List[str]:
        """
        Generate polyforms and add them to the assembly.
        
        Returns:
            List of generated polyform IDs
        """
        ...
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about generation performance.
        
        Returns:
            Dict with stats like count, success_rate, avg_time, etc.
        """
        ...
    
    def set_3d_mode(self, enabled: bool):
        """
        Enable or disable 3D mode for generation.
        
        Args:
            enabled: True for 3D mode, False for 2D mode
        """
        ...
    
    def is_3d_mode(self) -> bool:
        """Check if 3D mode is enabled."""
        ...


class BaseGenerator(ABC):
    """
    Abstract base class for all polyform generators.
    
    Provides common functionality and enforces interface contracts.
    All generator engines should inherit from this class.
    """
    
    def __init__(self, assembly, enable_3d_mode: bool = False):
        """
        Initialize base generator.
        
        Args:
            assembly: Assembly object to generate into
            enable_3d_mode: Whether to generate 3D meshes
        """
        self.assembly = assembly
        self._enable_3d_mode = enable_3d_mode
        self._generation_stats = {
            'total_generated': 0,
            'total_time': 0.0,
            'success_count': 0,
            'failure_count': 0
        }
    
    @abstractmethod
    def generate(self, **kwargs) -> List[str]:
        """
        Generate polyforms. Must be implemented by subclasses.
        
        Args:
            **kwargs: Generator-specific parameters
        
        Returns:
            List of generated polyform IDs
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        stats = dict(self._generation_stats)
        if stats['total_generated'] > 0:
            stats['success_rate'] = stats['success_count'] / stats['total_generated']
            stats['avg_time'] = stats['total_time'] / stats['total_generated']
        else:
            stats['success_rate'] = 0.0
            stats['avg_time'] = 0.0
        return stats
    
    def reset_stats(self):
        """Reset generation statistics."""
        self._generation_stats = {
            'total_generated': 0,
            'total_time': 0.0,
            'success_count': 0,
            'failure_count': 0
        }
    
    def set_3d_mode(self, enabled: bool):
        """Enable or disable 3D mode."""
        self._enable_3d_mode = enabled
    
    def is_3d_mode(self) -> bool:
        """Check if 3D mode is enabled."""
        return self._enable_3d_mode
    
    def _record_generation(self, count: int, success: bool, time_taken: float):
        """Record generation statistics."""
        self._generation_stats['total_generated'] += count
        self._generation_stats['total_time'] += time_taken
        if success:
            self._generation_stats['success_count'] += count
        else:
            self._generation_stats['failure_count'] += count
    
    def _create_polyform(self, sides: int, position: tuple = (0.0, 0.0, 0.0)) -> Dict[str, Any]:
        """
        Create a polyform with 2D or 3D mesh based on mode.
        
        Args:
            sides: Number of sides
            position: Center position (x, y, z)
        
        Returns:
            Polyform dictionary
        """
        if self._enable_3d_mode:
            from polygon_utils import create_polygon_3d
            return create_polygon_3d(sides, position, thickness=0.1)
        else:
            from polygon_utils import create_polygon
            return create_polygon(sides, position)
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate generated assembly (optional override).
        
        Returns:
            Validation result dict with 'is_valid' and optional 'reason'
        """
        return {'is_valid': True}


class GeneratorCapability:
    """
    Enum-like class for generator capabilities.
    
    Allows querying what features a generator supports.
    """
    BASIC = 'basic'
    CONSTRAINT_SOLVING = 'constraint_solving'
    FRACTAL = 'fractal'
    EVOLUTIONARY = 'evolutionary'
    PHYSICS = 'physics'
    AUTONOMOUS = 'autonomous'
    TEMPLATE_BASED = 'template_based'
    LEARNING = 'learning'


class GeneratorRegistry:
    """
    Registry for all available generators.
    
    Allows dynamic discovery and selection of generators.
    """
    
    def __init__(self):
        self._generators: Dict[str, type] = {}
        self._capabilities: Dict[str, List[str]] = {}
    
    def register(self, name: str, generator_class: type, capabilities: List[str]):
        """
        Register a generator.
        
        Args:
            name: Unique name for the generator
            generator_class: Generator class (must inherit from BaseGenerator)
            capabilities: List of capability strings
        """
        if not issubclass(generator_class, BaseGenerator):
            raise TypeError(f"{generator_class} must inherit from BaseGenerator")
        
        self._generators[name] = generator_class
        self._capabilities[name] = capabilities
    
    def get(self, name: str) -> Optional[type]:
        """Get generator class by name."""
        return self._generators.get(name)
    
    def list_generators(self) -> List[str]:
        """List all registered generator names."""
        return list(self._generators.keys())
    
    def find_by_capability(self, capability: str) -> List[str]:
        """Find generators with a specific capability."""
        return [
            name for name, caps in self._capabilities.items()
            if capability in caps
        ]
    
    def get_capabilities(self, name: str) -> List[str]:
        """Get capabilities for a generator."""
        return self._capabilities.get(name, [])


# Global registry instance
_global_registry = GeneratorRegistry()


def register_generator(name: str, capabilities: List[str]):
    """
    Decorator to register a generator class.
    
    Usage:
        @register_generator('my_generator', ['basic', 'fractal'])
        class MyGenerator(BaseGenerator):
            ...
    """
    def decorator(cls):
        _global_registry.register(name, cls, capabilities)
        return cls
    return decorator


def get_generator_registry() -> GeneratorRegistry:
    """Get the global generator registry."""
    return _global_registry
