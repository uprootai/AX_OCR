"""
Strategy Factory

Implements Factory Pattern for creating enhancement strategies.
"""

import logging
from typing import Optional

from .base import EnhancementStrategy
from .strategies import BasicStrategy, EDGNetStrategy, VLStrategy, HybridStrategy
from .exceptions import UnknownStrategyError

logger = logging.getLogger(__name__)


class StrategyFactory:
    """
    Factory for creating enhancement strategies

    Implements Factory Pattern to decouple strategy creation.
    """

    # Strategy registry
    _strategies = {
        'basic': BasicStrategy,
        'edgnet': EDGNetStrategy,
        'vl': VLStrategy,
        'hybrid': HybridStrategy
    }

    @classmethod
    def create(
        cls,
        strategy_name: str,
        vl_provider: Optional[str] = None
    ) -> EnhancementStrategy:
        """
        Create enhancement strategy instance

        Args:
            strategy_name: Strategy identifier ('basic', 'edgnet', 'vl', 'hybrid')
            vl_provider: VL provider for VL/Hybrid strategies ('openai', 'anthropic')

        Returns:
            EnhancementStrategy instance

        Raises:
            UnknownStrategyError: If strategy not found
        """
        strategy_class = cls._strategies.get(strategy_name.lower())

        if not strategy_class:
            raise UnknownStrategyError(
                f"Unknown strategy: {strategy_name}. "
                f"Available: {list(cls._strategies.keys())}"
            )

        # Create instance with provider if needed
        if strategy_name.lower() in ['vl', 'hybrid'] and vl_provider:
            strategy = strategy_class(vl_provider=vl_provider)
        else:
            strategy = strategy_class()

        logger.info(f"✅ Created strategy: {strategy.name}")
        return strategy

    @classmethod
    def list_strategies(cls) -> dict:
        """List all available strategies"""
        return {
            name: cls._strategies[name].__doc__.split('\n')[0].strip()
            for name in cls._strategies
        }

    @classmethod
    def register(cls, name: str, strategy_class: type):
        """
        Register custom strategy

        Args:
            name: Strategy identifier
            strategy_class: Strategy class (must inherit EnhancementStrategy)
        """
        if not issubclass(strategy_class, EnhancementStrategy):
            raise TypeError(
                f"Strategy class must inherit from EnhancementStrategy"
            )

        cls._strategies[name.lower()] = strategy_class
        logger.info(f"✅ Registered custom strategy: {name}")
