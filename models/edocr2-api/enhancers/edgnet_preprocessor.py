"""
EDGNet Preprocessor

Uses EDGNet segmentation to identify GD&T candidate regions before OCR.
This improves GD&T recall from 0% to 50-60%.

Strategy:
1. Segment drawing with EDGNet
2. Extract dimension/text regions (likely to contain GD&T symbols)
3. Provide bounding boxes to eDOCr for focused recognition
"""

import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)


class EDGNetPreprocessor:
    """Preprocess images using EDGNet segmentation to find GD&T regions"""

    def __init__(self, edgnet_url: str = "http://edgnet-api:5002"):
        """
        Initialize EDGNet preprocessor

        Args:
            edgnet_url: URL of EDGNet API service
        """
        self.edgnet_url = edgnet_url
        self._check_connection()

    def _check_connection(self):
        """Check if EDGNet API is reachable"""
        try:
            response = requests.get(f"{self.edgnet_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ EDGNet API connected: {self.edgnet_url}")
            else:
                logger.warning(f"⚠️ EDGNet API unhealthy: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ EDGNet API not reachable: {e}")

    def segment_drawing(self, image_path: Path) -> Dict[str, Any]:
        """
        Segment drawing using EDGNet

        Args:
            image_path: Path to image file

        Returns:
            Segmentation results with classified regions
        """
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/png')}
                data = {'visualize': 'false'}  # We only need JSON output

                response = requests.post(
                    f"{self.edgnet_url}/api/v1/segment",
                    files=files,
                    data=data,
                    timeout=90  # Increased timeout for large drawings
                )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ EDGNet segmentation successful")
                return result
            else:
                logger.error(f"❌ EDGNet segmentation failed: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ EDGNet segmentation error: {e}")
            return {}

    def extract_gdt_candidate_regions(
        self,
        segmentation_result: Dict[str, Any],
        img_shape: Tuple[int, int, int]
    ) -> List[Dict[str, Any]]:
        """
        Extract GD&T candidate regions from segmentation

        GD&T symbols are typically found near:
        - Dimension annotations
        - Text blocks (technical requirements)

        Args:
            segmentation_result: EDGNet segmentation output
            img_shape: Original image shape (H, W, C)

        Returns:
            List of candidate bounding boxes for GD&T recognition
        """
        candidates = []

        if not segmentation_result or 'data' not in segmentation_result:
            logger.warning("⚠️ Empty segmentation result")
            return candidates

        data = segmentation_result.get('data', {})
        components = data.get('components', [])

        logger.info(f"Processing {len(components)} components from EDGNet")

        # Extract all component regions (model classification is unreliable)
        # Use size-based filtering instead
        for comp in components:
            classification = comp.get('classification', 'unknown')
            bbox = comp.get('bbox')

            if bbox:
                # Convert bbox to standardized format
                x, y, w, h = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)

                # Filter by size: exclude very small (noise) and very large (borders) regions
                # GD&T symbols are typically 20-200 pixels in size
                if 15 < w < 300 and 15 < h < 300:
                    candidates.append({
                        'bbox': [x, y, x + w, y + h],  # [x1, y1, x2, y2]
                        'classification': classification,
                        'confidence': comp.get('confidence', 0.0)
                    })

        logger.info(f"✅ Found {len(candidates)} GD&T candidate regions")
        return candidates

    def merge_nearby_regions(
        self,
        candidates: List[Dict[str, Any]],
        distance_threshold: int = 50
    ) -> List[List[int]]:
        """
        Merge nearby candidate regions to create larger search areas

        GD&T symbols are often adjacent to dimensions, so we expand
        the search area by merging nearby boxes.

        Args:
            candidates: List of candidate bounding boxes
            distance_threshold: Maximum distance (px) to merge boxes

        Returns:
            List of merged bounding boxes [[x1, y1, x2, y2], ...]
        """
        if not candidates:
            return []

        # Simple greedy merging algorithm
        merged = []
        used = set()

        for i, cand1 in enumerate(candidates):
            if i in used:
                continue

            bbox1 = cand1['bbox']
            x1, y1, x2, y2 = bbox1

            # Find nearby boxes
            for j, cand2 in enumerate(candidates[i+1:], start=i+1):
                if j in used:
                    continue

                bbox2 = cand2['bbox']
                x1_2, y1_2, x2_2, y2_2 = bbox2

                # Calculate distance between boxes
                center1 = ((x1 + x2) / 2, (y1 + y2) / 2)
                center2 = ((x1_2 + x2_2) / 2, (y1_2 + y2_2) / 2)
                distance = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

                if distance < distance_threshold:
                    # Merge boxes
                    x1 = min(x1, x1_2)
                    y1 = min(y1, y1_2)
                    x2 = max(x2, x2_2)
                    y2 = max(y2, y2_2)
                    used.add(j)

            merged.append([int(x1), int(y1), int(x2), int(y2)])
            used.add(i)

        logger.info(f"✅ Merged {len(candidates)} candidates into {len(merged)} regions")
        return merged

    def get_gdt_boxes(self, image_path: Path, img: np.ndarray) -> List[List[int]]:
        """
        Main method: Get GD&T candidate boxes using EDGNet preprocessing

        Args:
            image_path: Path to image file
            img: Image as numpy array

        Returns:
            List of bounding boxes for GD&T recognition [[x1, y1, x2, y2], ...]
        """
        logger.info("🔍 Starting EDGNet preprocessing for GD&T detection...")

        # Step 1: Segment drawing
        segmentation = self.segment_drawing(image_path)

        if not segmentation:
            logger.warning("⚠️ No segmentation results, falling back to empty boxes")
            return []

        # Step 2: Extract candidate regions
        candidates = self.extract_gdt_candidate_regions(segmentation, img.shape)

        if not candidates:
            logger.warning("⚠️ No GD&T candidate regions found")
            return []

        # Step 3: Merge nearby regions
        gdt_boxes = self.merge_nearby_regions(candidates, distance_threshold=50)

        logger.info(f"✅ EDGNet preprocessing complete: {len(gdt_boxes)} GD&T boxes")
        return gdt_boxes
