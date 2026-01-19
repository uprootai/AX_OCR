"""
Pipeline Helper Functions
Extracted from process_router.py for better modularity
"""

import json
import base64
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path

from utils import (
    ProgressTracker,
    match_yolo_with_ocr, redraw_yolo_visualization,
    create_ocr_visualization, create_edgnet_visualization, create_ensemble_visualization
)
from services import ensemble_ocr_results
from constants import RESULTS_DIR

logger = logging.getLogger(__name__)


def process_parallel_results(
    result: Dict, tracker: ProgressTracker, results: List,
    use_ocr: bool, use_segmentation: bool,
    image_bytes: bytes, is_pdf: bool, file_bytes: bytes
) -> None:
    """Process parallel task results"""
    idx = 0

    if use_ocr:
        process_ocr_result(result, tracker, results[idx], image_bytes, is_pdf, file_bytes)
        idx += 1

    if use_segmentation:
        process_segmentation_result(result, tracker, results[idx], image_bytes, is_pdf, file_bytes)


def process_ocr_result(result: Dict, tracker: ProgressTracker, ocr_result, image_bytes: bytes, is_pdf: bool, file_bytes: bytes) -> None:
    """Process OCR result"""
    if isinstance(ocr_result, Exception):
        result["ocr_results"] = {"error": str(ocr_result)}
        tracker.update("ocr", "error", f"OCR failed: {ocr_result}")
        return

    result["ocr_results"] = ocr_result
    dims_count = len(ocr_result.get("dimensions", []))
    tracker.update("ocr", "completed", f"OCR: {dims_count} dimensions", {"dimensions_count": dims_count})

    try:
        ocr_vis = create_ocr_visualization(
            image_bytes if not is_pdf else file_bytes,
            result["ocr_results"]
        )
        if ocr_vis:
            result["ocr_results"]["visualized_image"] = ocr_vis
            logger.info("Created OCR visualization")
    except Exception as e:
        logger.warning(f"Failed to create OCR visualization: {e}")


def process_segmentation_result(result: Dict, tracker: ProgressTracker, seg_result, image_bytes: bytes, is_pdf: bool, file_bytes: bytes) -> None:
    """Process segmentation result"""
    if isinstance(seg_result, Exception):
        result["segmentation_results"] = {"error": str(seg_result)}
        tracker.update("edgnet", "error", f"EDGNet failed: {seg_result}")
        return

    edgnet_data = seg_result.get("data", {})
    result["segmentation_results"] = {
        "components": edgnet_data.get("components", []),
        "total_components": edgnet_data.get("total_components", edgnet_data.get("num_components", 0)),
        "processing_time": seg_result.get("processing_time", 0)
    }
    comps_count = result["segmentation_results"]["total_components"]
    tracker.update("edgnet", "completed", f"EDGNet: {comps_count} components", {"components_count": comps_count})

    try:
        if result["segmentation_results"].get("components"):
            edgnet_vis = create_edgnet_visualization(
                image_bytes if not is_pdf else file_bytes,
                result["segmentation_results"]
            )
            if edgnet_vis:
                result["segmentation_results"]["visualized_image"] = edgnet_vis
                logger.info("Created EDGNet visualization")
    except Exception as e:
        logger.warning(f"Failed to create EDGNet visualization: {e}")


def run_ensemble_merging(
    result: Dict, tracker: ProgressTracker,
    file_bytes: bytes, is_pdf: bool,
    use_ensemble: bool, use_yolo_crop_ocr: bool
) -> None:
    """Run ensemble merging of OCR results (sync version for internal use)"""
    logger.info("Ensemble merging")
    tracker.update("ensemble", "running", "Ensemble merging...")

    ensemble_dimensions = []

    if result.get("yolo_results") and result.get("ocr_results"):
        yolo_detections = result["yolo_results"].get("detections", [])
        ocr_dimensions = result["ocr_results"].get("dimensions", [])

        # Match YOLO with OCR
        logger.info(f"Matching {len(yolo_detections)} YOLO detections with {len(ocr_dimensions)} OCR dimensions")
        matched_yolo_detections = match_yolo_with_ocr(
            yolo_detections=yolo_detections,
            ocr_dimensions=ocr_dimensions,
            iou_threshold=0.3
        )
        result["yolo_results"]["detections"] = matched_yolo_detections
        matched_count = sum(1 for d in matched_yolo_detections if d.get('value'))
        logger.info(f"Matched {matched_count}/{len(yolo_detections)} detections")

        # Update visualization with matched values
        if result["yolo_results"].get("visualized_image") and matched_count > 0:
            try:
                updated_viz = redraw_yolo_visualization(file_bytes, matched_yolo_detections)
                result["yolo_results"]["visualized_image"] = updated_viz
            except Exception as e:
                logger.error(f"Failed to update visualization: {e}")

        # Advanced ensemble
        if use_ensemble and use_yolo_crop_ocr and result.get("yolo_crop_ocr_results"):
            yolo_crop_dims = result["yolo_crop_ocr_results"].get("dimensions", [])
            ensemble_dimensions = ensemble_ocr_results(
                yolo_crop_results=yolo_crop_dims,
                edocr_results=ocr_dimensions,
                yolo_weight=0.6,
                edocr_weight=0.4,
                similarity_threshold=0.7
            )
            result["ensemble"] = {
                "dimensions": ensemble_dimensions,
                "yolo_detections_count": len(yolo_detections),
                "ocr_dimensions_count": len(ocr_dimensions),
                "yolo_crop_ocr_count": len(yolo_crop_dims),
                "strategy": "Advanced Ensemble"
            }
            tracker.update("ensemble", "completed", f"Advanced ensemble: {len(ensemble_dimensions)} dimensions")

        elif use_yolo_crop_ocr and result.get("yolo_crop_ocr_results"):
            yolo_crop_dims = result["yolo_crop_ocr_results"].get("dimensions", [])
            ensemble_dimensions = ocr_dimensions.copy()
            existing_texts = {d.get("value", "") for d in ensemble_dimensions}
            for dim in yolo_crop_dims:
                if dim.get("value", "") not in existing_texts:
                    ensemble_dimensions.append(dim)
                    existing_texts.add(dim.get("value", ""))
            result["ensemble"] = {
                "dimensions": ensemble_dimensions,
                "yolo_detections_count": len(yolo_detections),
                "ocr_dimensions_count": len(ocr_dimensions),
                "yolo_crop_ocr_count": len(yolo_crop_dims),
                "strategy": "Simple Merge"
            }
            tracker.update("ensemble", "completed", f"Simple merge: {len(ensemble_dimensions)} dimensions")
        else:
            ensemble_dimensions = ocr_dimensions.copy()
            result["ensemble"] = {
                "dimensions": ensemble_dimensions,
                "yolo_detections_count": len(yolo_detections),
                "ocr_dimensions_count": len(ocr_dimensions),
                "strategy": "eDOCr + YOLO bbox"
            }
            tracker.update("ensemble", "completed", f"Ensemble: {len(ensemble_dimensions)} dimensions")

    elif result.get("ocr_results"):
        ensemble_dimensions = result["ocr_results"].get("dimensions", [])
        result["ensemble"] = {
            "dimensions": ensemble_dimensions,
            "source": "eDOCr only"
        }
        tracker.update("ensemble", "completed", f"eDOCr only: {len(ensemble_dimensions)} dimensions")

    # Create ensemble visualization
    if result.get("ensemble"):
        try:
            yolo_count = result.get("yolo_results", {}).get("total_detections", 0)
            ocr_count = len(result.get("ocr_results", {}).get("dimensions", []))
            ensemble_vis = create_ensemble_visualization(
                file_bytes if not is_pdf else file_bytes,
                result["ensemble"],
                yolo_count=yolo_count,
                ocr_count=ocr_count
            )
            if ensemble_vis:
                result["ensemble"]["visualized_image"] = ensemble_vis
        except Exception as e:
            logger.warning(f"Failed to create ensemble visualization: {e}")


def save_results(
    result: Dict, file_id: str, filename: str, file_bytes: bytes,
    processing_time: float, pipeline_mode: str
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Save result files and return paths"""
    saved_files = {}

    project_dir = RESULTS_DIR / file_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # JSON result
    result_json_path = project_dir / "result.json"
    with open(result_json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "file_id": file_id,
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "pipeline_mode": pipeline_mode,
            "processing_time": round(processing_time, 2),
            "data": result
        }, f, indent=2, ensure_ascii=False, default=str)
    saved_files["result_json"] = str(result_json_path)
    logger.info(f"Saved result JSON: {result_json_path}")

    # YOLO visualization
    if result.get("yolo_results", {}).get("visualized_image"):
        try:
            viz_img_base64 = result["yolo_results"]["visualized_image"]
            viz_img_data = base64.b64decode(viz_img_base64)
            viz_img_path = project_dir / "yolo_visualization.jpg"
            with open(viz_img_path, 'wb') as f:
                f.write(viz_img_data)
            saved_files["yolo_visualization"] = str(viz_img_path)
            logger.info(f"Saved YOLO visualization: {viz_img_path}")
        except Exception as e:
            logger.error(f"Failed to save YOLO visualization: {e}")

    # Original file
    suffix = Path(filename).suffix if filename else '.bin'
    original_file_path = project_dir / f"original{suffix}"
    with open(original_file_path, 'wb') as f:
        f.write(file_bytes)
    saved_files["original_file"] = str(original_file_path)
    logger.info(f"Saved original file: {original_file_path}")

    # Download URLs
    download_urls = {}
    if "yolo_visualization" in saved_files:
        download_urls["yolo_visualization"] = f"/api/v1/download/{file_id}/yolo_visualization"
    if "result_json" in saved_files:
        download_urls["result_json"] = f"/api/v1/download/{file_id}/result_json"
    if "original_file" in saved_files:
        download_urls["original"] = f"/api/v1/download/{file_id}/original"

    return saved_files, download_urls
