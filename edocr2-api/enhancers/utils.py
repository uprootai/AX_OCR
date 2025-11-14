"""
Utility Classes and Functions

Provides reusable utilities for enhancement pipeline.
"""

import logging
from typing import List, Dict, Any
import numpy as np

from .base import ResultMerger

logger = logging.getLogger(__name__)


class GDTResultMerger(ResultMerger):
    """
    GD&T Result Merger

    Handles merging and deduplication of GD&T detection results.
    """

    def merge(
        self,
        *result_lists: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple GD&T result lists

        Args:
            *result_lists: Variable number of result lists

        Returns:
            Merged results (prioritizes earlier lists)
        """
        merged = []

        for result_list in result_lists:
            if result_list:
                merged.extend(result_list)

        logger.info(f"Merged {len(result_lists)} result lists → {len(merged)} total")
        return merged

    def deduplicate(
        self,
        results: List[Dict[str, Any]],
        distance_threshold: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate GD&T detections

        Uses spatial proximity and type matching to identify duplicates.

        Args:
            results: GD&T detection results
            distance_threshold: Max distance (px) to consider duplicates

        Returns:
            Deduplicated results (keeps highest confidence)
        """
        if len(results) <= 1:
            return results

        deduplicated = []
        used_indices = set()

        for i, gdt1 in enumerate(results):
            if i in used_indices:
                continue

            loc1 = gdt1.get('location', {})
            x1, y1 = loc1.get('x', 0), loc1.get('y', 0)

            # Find duplicates
            duplicates = [i]
            for j, gdt2 in enumerate(results[i+1:], start=i+1):
                if j in used_indices:
                    continue

                loc2 = gdt2.get('location', {})
                x2, y2 = loc2.get('x', 0), loc2.get('y', 0)

                distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

                # Same type and close location = duplicate
                if gdt1.get('type') == gdt2.get('type') and distance < distance_threshold:
                    duplicates.append(j)
                    used_indices.add(j)

            # Keep the one with highest confidence
            best_idx = max(duplicates, key=lambda idx: results[idx].get('confidence', 0))
            deduplicated.append(results[best_idx])
            used_indices.add(i)

        logger.info(f"Deduplicated {len(results)} → {len(deduplicated)} results")
        return deduplicated


def validate_gdt_format(gdt: Dict[str, Any]) -> bool:
    """
    Validate GD&T annotation format

    Args:
        gdt: GD&T annotation dict

    Returns:
        True if valid, False otherwise
    """
    required_fields = ['type', 'value', 'location']

    for field in required_fields:
        if field not in gdt:
            logger.warning(f"Invalid GD&T: missing '{field}'")
            return False

    # Validate location
    location = gdt.get('location', {})
    if not isinstance(location, dict) or 'x' not in location or 'y' not in location:
        logger.warning("Invalid GD&T: invalid location")
        return False

    return True


def calculate_improvement_stats(
    original: List[Dict[str, Any]],
    enhanced: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate improvement statistics

    Args:
        original: Original detection results
        enhanced: Enhanced detection results

    Returns:
        Statistics dict
    """
    return {
        "original_count": len(original),
        "enhanced_count": len(enhanced),
        "improvement": len(enhanced) - len(original),
        "improvement_pct": round(
            ((len(enhanced) - len(original)) / max(len(original), 1)) * 100,
            1
        ) if original else 0
    }
