"""
Base Classes and Interfaces

Defines abstract interfaces for enhancement strategies.
Follows Strategy Pattern and Template Method Pattern.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger(__name__)


class GDTDetector(ABC):
    """
    Abstract base class for GD&T detectors

    Implements Strategy Pattern for different detection approaches.
    """

    @abstractmethod
    def detect(
        self,
        image_path: Path,
        img: Optional[np.ndarray] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect GD&T symbols from image

        Args:
            image_path: Path to image file
            img: Optional pre-loaded image array

        Returns:
            List of GD&T annotations
        """
        pass

    @abstractmethod
    def format_for_ui(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format detections to UI-compatible structure

        Args:
            detections: Raw detection results

        Returns:
            UI-compatible GD&T list
        """
        pass


class BoxPreprocessor(ABC):
    """
    Abstract base class for box detection preprocessors

    Used to improve GD&T box detection before OCR.
    """

    @abstractmethod
    def get_boxes(
        self,
        image_path: Path,
        img: np.ndarray
    ) -> List[List[int]]:
        """
        Get GD&T candidate bounding boxes

        Args:
            image_path: Path to image file
            img: Image array

        Returns:
            List of bounding boxes [[x1, y1, x2, y2], ...]
        """
        pass


class EnhancementStrategy(ABC):
    """
    Abstract base class for enhancement strategies

    Implements Strategy Pattern with Template Method for common logic.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def enhance_gdt(
        self,
        image_path: Path,
        img: np.ndarray,
        original_gdt: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance GD&T detection

        Args:
            image_path: Path to image file
            img: Image array
            original_gdt: Original GD&T results from eDOCr

        Returns:
            Enhanced GD&T list
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get strategy metadata"""
        return {
            "name": self.name,
            "description": self.description
        }


class ResultMerger(ABC):
    """
    Abstract base class for result merging

    Handles merging and deduplication of detection results.
    """

    @abstractmethod
    def merge(
        self,
        *result_lists: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple detection result lists

        Args:
            *result_lists: Variable number of result lists

        Returns:
            Merged and deduplicated results
        """
        pass

    @abstractmethod
    def deduplicate(
        self,
        results: List[Dict[str, Any]],
        distance_threshold: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate detections

        Args:
            results: Detection results
            distance_threshold: Max distance for duplicates

        Returns:
            Deduplicated results
        """
        pass
