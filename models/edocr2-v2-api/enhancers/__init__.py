"""
Enhanced OCR Pipeline Modules

Modular components for improving OCR performance using design patterns:
- Strategy Pattern: Different enhancement approaches (Basic, EDGNet, VL, Hybrid)
- Factory Pattern: Centralized strategy creation
- Singleton Pattern: Configuration management
- Template Method: Common enhancement logic

Architecture:
    base.py         - Abstract interfaces (Strategy, Detector, Preprocessor)
    strategies.py   - Concrete strategy implementations
    factory.py      - Strategy factory
    config.py       - Configuration manager (Singleton)
    exceptions.py   - Custom exception hierarchy
    utils.py        - Utility classes and functions
"""

# Core components
from .factory import StrategyFactory
from .config import config, ConfigManager
from .exceptions import (
    EnhancementError,
    EDGNetError,
    VLDetectorError,
    StrategyError,
    UnknownStrategyError
)

# Base classes (for extension)
from .base import (
    EnhancementStrategy,
    GDTDetector,
    BoxPreprocessor,
    ResultMerger
)

# Concrete implementations
from .strategies import (
    BasicStrategy,
    EDGNetStrategy,
    VLStrategy,
    HybridStrategy
)

# Legacy support (backward compatibility)
from .edgnet_preprocessor import EDGNetPreprocessor
from .vl_detector import VLDetector
from .enhanced_pipeline import EnhancedOCRPipeline

__version__ = "2.0.0"

__all__ = [
    # Factory (recommended interface)
    'StrategyFactory',

    # Configuration
    'config',
    'ConfigManager',

    # Exceptions
    'EnhancementError',
    'EDGNetError',
    'VLDetectorError',
    'StrategyError',
    'UnknownStrategyError',

    # Base classes
    'EnhancementStrategy',
    'GDTDetector',
    'BoxPreprocessor',
    'ResultMerger',

    # Strategies
    'BasicStrategy',
    'EDGNetStrategy',
    'VLStrategy',
    'HybridStrategy',

    # Legacy (backward compatibility)
    'EDGNetPreprocessor',
    'VLDetector',
    'EnhancedOCRPipeline',
]
