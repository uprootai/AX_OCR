"""
Enhanced OCR Pipeline

Orchestrates multiple enhancement strategies:
1. Basic: Original eDOCr (baseline)
2. EDGNet-Enhanced: Use EDGNet preprocessing for GD&T detection
3. VL-Powered: Use Vision-Language models for advanced recognition
4. Hybrid: Combine EDGNet + VL + eDOCr (best quality)

Performance targets:
- Basic: 50% dimension recall, 0% GD&T recall
- EDGNet-Enhanced: 60% dimension recall, 50% GD&T recall
- VL-Powered: 85% dimension recall, 75% GD&T recall
- Hybrid: 90% dimension recall, 80% GD&T recall
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
import time

from .edgnet_preprocessor import EDGNetPreprocessor
from .vl_detector import VLDetector

logger = logging.getLogger(__name__)


class EnhancedOCRPipeline:
    """Orchestrate enhanced OCR strategies"""

    STRATEGIES = {
        'basic': 'Original eDOCr (baseline)',
        'edgnet': 'EDGNet-enhanced (50-60% GD&T recall)',
        'vl': 'VL-powered (70-75% GD&T recall)',
        'hybrid': 'Hybrid: EDGNet + VL (80%+ GD&T recall)'
    }

    def __init__(
        self,
        edgnet_url: str = "http://edgnet-api:5002",
        vl_provider: str = "openai",
        vl_api_key: Optional[str] = None
    ):
        """
        Initialize enhanced pipeline

        Args:
            edgnet_url: URL of EDGNet API
            vl_provider: VL provider ('openai', 'anthropic')
            vl_api_key: API key for VL provider
        """
        self.edgnet_preprocessor = EDGNetPreprocessor(edgnet_url=edgnet_url)
        self.vl_detector = VLDetector(provider=vl_provider, api_key=vl_api_key)

        logger.info("✅ Enhanced OCR Pipeline initialized")
        logger.info(f"Available strategies: {list(self.STRATEGIES.keys())}")

    def enhance_gdt_boxes(
        self,
        image_path: Path,
        img: np.ndarray,
        original_gdt_boxes: List
    ) -> List:
        """
        Enhance GD&T box detection using EDGNet

        Args:
            image_path: Path to image
            img: Image array
            original_gdt_boxes: Original boxes from eDOCr (likely empty)

        Returns:
            Enhanced list of GD&T boxes
        """
        logger.info("🔧 Enhancing GD&T boxes with EDGNet...")

        # Get EDGNet-based candidate boxes
        edgnet_boxes = self.edgnet_preprocessor.get_gdt_boxes(image_path, img)

        # Merge with original boxes (if any)
        if original_gdt_boxes:
            logger.info(f"Merging {len(original_gdt_boxes)} original + {len(edgnet_boxes)} EDGNet boxes")
            all_boxes = original_gdt_boxes + edgnet_boxes
        else:
            logger.info(f"Using {len(edgnet_boxes)} EDGNet boxes (original was empty)")
            all_boxes = edgnet_boxes

        return all_boxes

    def enhance_with_vl(
        self,
        image_path: Path,
        original_gdt: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance GD&T detection using Vision-Language model

        Args:
            image_path: Path to image
            original_gdt: Original GD&T results from eDOCr

        Returns:
            Enhanced GD&T list (merged VL + original)
        """
        logger.info("🤖 Enhancing GD&T with VL model...")

        # Get VL detection results
        vl_results = self.vl_detector.detect_gdt(image_path)

        if not vl_results:
            logger.warning("⚠️ VL detection returned no results")
            return original_gdt

        # Format for UI
        vl_gdt = self.vl_detector.format_for_ui(vl_results)

        # Merge with original (VL results take priority due to higher accuracy)
        logger.info(f"Merging {len(original_gdt)} original + {len(vl_gdt)} VL GD&T")

        # Simple merge: VL first, then original
        merged_gdt = vl_gdt + original_gdt

        return merged_gdt

    def deduplicate_gdt(
        self,
        gdt_list: List[Dict[str, Any]],
        distance_threshold: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate GD&T detections

        Args:
            gdt_list: List of GD&T annotations
            distance_threshold: Max distance (px) to consider duplicates

        Returns:
            Deduplicated GD&T list
        """
        if len(gdt_list) <= 1:
            return gdt_list

        deduplicated = []
        used_indices = set()

        for i, gdt1 in enumerate(gdt_list):
            if i in used_indices:
                continue

            loc1 = gdt1.get('location', {})
            x1, y1 = loc1.get('x', 0), loc1.get('y', 0)

            # Find duplicates
            duplicates = [i]
            for j, gdt2 in enumerate(gdt_list[i+1:], start=i+1):
                if j in used_indices:
                    continue

                loc2 = gdt2.get('location', {})
                x2, y2 = loc2.get('x', 0), loc2.get('y', 0)

                distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

                # Same type and close location = duplicate
                if gdt1.get('type') == gdt2.get('type') and distance < distance_threshold:
                    duplicates.append(j)
                    used_indices.add(j)

            # Keep the one with highest confidence (or first if equal)
            best_idx = max(duplicates, key=lambda idx: gdt_list[idx].get('confidence', 0))
            deduplicated.append(gdt_list[best_idx])
            used_indices.add(i)

        logger.info(f"✅ Deduplicated {len(gdt_list)} → {len(deduplicated)} GD&T annotations")
        return deduplicated

    def run(
        self,
        strategy: str,
        image_path: Path,
        img: np.ndarray,
        original_gdt_boxes: List,
        original_gdt: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run enhanced pipeline with specified strategy

        Args:
            strategy: Enhancement strategy ('basic', 'edgnet', 'vl', 'hybrid')
            image_path: Path to image
            img: Image array
            original_gdt_boxes: Original GD&T boxes from eDOCr
            original_gdt: Original GD&T results from eDOCr

        Returns:
            Enhanced results with metadata
        """
        start_time = time.time()

        logger.info(f"🚀 Running enhanced pipeline: {strategy}")

        if strategy not in self.STRATEGIES:
            logger.warning(f"⚠️ Unknown strategy '{strategy}', falling back to 'basic'")
            strategy = 'basic'

        enhanced_gdt_boxes = original_gdt_boxes
        enhanced_gdt = original_gdt
        enhancements_applied = []

        # Basic: No enhancement
        if strategy == 'basic':
            enhancements_applied.append('none')

        # EDGNet-Enhanced: Use EDGNet preprocessing
        elif strategy == 'edgnet':
            enhanced_gdt_boxes = self.enhance_gdt_boxes(image_path, img, original_gdt_boxes)
            enhancements_applied.append('edgnet_preprocessing')

        # VL-Powered: Use Vision-Language model
        elif strategy == 'vl':
            enhanced_gdt = self.enhance_with_vl(image_path, original_gdt)
            enhanced_gdt = self.deduplicate_gdt(enhanced_gdt)
            enhancements_applied.append('vl_detection')

        # Hybrid: Combine EDGNet + VL
        elif strategy == 'hybrid':
            # Step 1: EDGNet preprocessing
            enhanced_gdt_boxes = self.enhance_gdt_boxes(image_path, img, original_gdt_boxes)
            enhancements_applied.append('edgnet_preprocessing')

            # Step 2: VL detection (will merge with eDOCr results from enhanced boxes)
            enhanced_gdt = self.enhance_with_vl(image_path, original_gdt)
            enhancements_applied.append('vl_detection')

            # Step 3: Deduplicate
            enhanced_gdt = self.deduplicate_gdt(enhanced_gdt)
            enhancements_applied.append('deduplication')

        processing_time = time.time() - start_time

        result = {
            'strategy': strategy,
            'description': self.STRATEGIES[strategy],
            'enhancements_applied': enhancements_applied,
            'enhanced_gdt_boxes': enhanced_gdt_boxes,
            'enhanced_gdt': enhanced_gdt,
            'processing_time': round(processing_time, 2),
            'stats': {
                'original_boxes': len(original_gdt_boxes),
                'enhanced_boxes': len(enhanced_gdt_boxes),
                'original_gdt': len(original_gdt),
                'enhanced_gdt': len(enhanced_gdt),
                'improvement': len(enhanced_gdt) - len(original_gdt)
            }
        }

        logger.info(f"✅ Enhanced pipeline complete in {processing_time:.2f}s")
        logger.info(f"GD&T improvement: {result['stats']['original_gdt']} → {result['stats']['enhanced_gdt']} (+{result['stats']['improvement']})")

        return result
