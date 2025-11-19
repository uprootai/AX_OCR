"""
Utility functions for Skin Model API
"""
from typing import Dict, Any


def format_tolerance_value(value: float, precision: int = 4) -> float:
    """
    Format tolerance value to specified precision

    Args:
        value: Tolerance value
        precision: Number of decimal places

    Returns:
        Formatted value
    """
    return round(value, precision)


def validate_manufacturing_process(process: str) -> bool:
    """
    Validate manufacturing process type

    Args:
        process: Manufacturing process name

    Returns:
        True if valid, False otherwise
    """
    valid_processes = ["machining", "casting", "3d_printing"]
    return process.lower() in valid_processes


def get_material_factor(material_name: str) -> float:
    """
    Get material tolerance factor

    Args:
        material_name: Material name

    Returns:
        Material factor (1.0 = baseline)
    """
    material_factors = {
        "Steel": 1.0,
        "Aluminum": 0.8,
        "Titanium": 1.5,
        "Plastic": 0.6
    }
    return material_factors.get(material_name, 1.0)


def calculate_size_factor(max_dimension: float) -> float:
    """
    Calculate size-based tolerance factor

    Larger parts typically have looser tolerances

    Args:
        max_dimension: Maximum dimension in mm

    Returns:
        Size factor
    """
    return 1.0 + (max_dimension / 1000.0) * 0.5


def calculate_correlation_factor(correlation_length: float) -> float:
    """
    Calculate correlation length factor

    Args:
        correlation_length: Random field correlation length

    Returns:
        Correlation factor
    """
    return 1.0 + (correlation_length - 1.0) * 0.3
