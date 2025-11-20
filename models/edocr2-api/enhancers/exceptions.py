"""
Custom Exceptions for Enhancement Pipeline

Provides a clear exception hierarchy for error handling.
"""


class EnhancementError(Exception):
    """Base exception for all enhancement-related errors"""
    pass


class EDGNetError(EnhancementError):
    """EDGNet preprocessor errors"""
    pass


class EDGNetConnectionError(EDGNetError):
    """EDGNet API connection failed"""
    pass


class EDGNetSegmentationError(EDGNetError):
    """EDGNet segmentation failed"""
    pass


class VLDetectorError(EnhancementError):
    """VL detector errors"""
    pass


class VLAPIKeyMissingError(VLDetectorError):
    """VL API key not configured"""
    pass


class VLProviderError(VLDetectorError):
    """VL provider not supported or failed"""
    pass


class VLResponseError(VLDetectorError):
    """VL model returned invalid response"""
    pass


class StrategyError(EnhancementError):
    """Strategy execution errors"""
    pass


class UnknownStrategyError(StrategyError):
    """Unknown enhancement strategy"""
    pass
