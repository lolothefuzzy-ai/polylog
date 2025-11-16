"""Unicode-driven polyform storage package."""

from .attachment_schemas import (
    CLOSURE_SCHEMAS,
    DIMENSION_SCHEMAS,
    FOLD_ANGLE_SCHEMAS,
    GENERATION_SCHEMAS,
    POLYGON_PAIR_ATTACHMENT_MATRIX,
    SCHEMA_PARTITIONS,
    STABILITY_SCHEMAS,
    ContextSchema,
    is_placeholder_context,
)
from .compression_tree import CompressionResult, CompressionTree
from .descriptors import DihedralAngleSet, PolyformDescriptor, SymmetryDescriptor
from .encoder import PolyformDecoder, PolyformEncoder
from .symbol_registry import SymbolRegistry

__all__ = [
    "CLOSURE_SCHEMAS",
    "CompressionResult",
    "CompressionTree",
    "DihedralAngleSet",
    "DIMENSION_SCHEMAS",
    "FOLD_ANGLE_SCHEMAS",
    "GENERATION_SCHEMAS",
    "POLYGON_PAIR_ATTACHMENT_MATRIX",
    "PolyformDecoder",
    "PolyformDescriptor",
    "PolyformEncoder",
    "SCHEMA_PARTITIONS",
    "SymmetryDescriptor",
    "SymbolRegistry",
    "STABILITY_SCHEMAS",
    "ContextSchema",
    "is_placeholder_context",
]
