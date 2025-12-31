"""
Process Router - /api/v1/process endpoint
Pipeline processing for engineering drawings

Refactored from api_server.py (2025-12-31)
"""

import time
import json
import asyncio
import logging
import base64
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse

from models import ProcessResponse
from utils import (
    ProgressTracker, progress_store,
    is_false_positive, pdf_to_image, crop_bbox,
    match_yolo_with_ocr, redraw_yolo_visualization,
    create_ocr_visualization, create_edgnet_visualization, create_ensemble_visualization
)
from services import (
    call_yolo_detect, call_edocr2_ocr,
    call_edgnet_segment, call_skinmodel_tolerance,
    process_yolo_crop_ocr, ensemble_ocr_results
)
from constants import RESULTS_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["process"])


@router.get("/progress/{job_id}")
async def get_progress_stream(job_id: str):
    """Server-Sent Events endpoint for real-time progress updates"""

    async def event_generator():
        """Generate SSE events"""
        last_index = 0
        timeout_count = 0
        max_timeout = 120  # 2 minutes timeout

        while timeout_count < max_timeout:
            # Get progress updates
            progress_list = progress_store.get(job_id, [])

            # Send new updates
            if len(progress_list) > last_index:
                for update in progress_list[last_index:]:
                    yield f"data: {json.dumps(update)}\n\n"
                last_index = len(progress_list)
                timeout_count = 0  # Reset timeout

            # Check if job is complete
            if progress_list:
                last_update = progress_list[-1]
                if last_update.get("step") == "complete" and last_update.get("status") == "completed":
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                    break
                if last_update.get("status") == "error":
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                    break

            await asyncio.sleep(0.5)
            timeout_count += 1

        if timeout_count >= max_timeout:
            yield f"data: {json.dumps({'status': 'timeout'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/process", response_model=ProcessResponse)
async def process_drawing(
    file: UploadFile = File(..., description="Drawing file"),
    pipeline_mode: str = Form(default="speed", description="Pipeline mode: hybrid or speed"),
    use_segmentation: bool = Form(True),
    use_ocr: bool = Form(True),
    use_tolerance: bool = Form(True),
    use_yolo_crop_ocr: bool = Form(default=False, description="YOLO crop-based OCR"),
    use_ensemble: bool = Form(default=False, description="Ensemble strategy"),
    visualize: bool = Form(True),
    # YOLO hyperparameters
    yolo_conf_threshold: float = Form(default=0.25),
    yolo_iou_threshold: float = Form(default=0.7),
    yolo_imgsz: int = Form(default=1280),
    yolo_visualize: bool = Form(default=True),
    # eDOCr2 hyperparameters
    edocr_extract_dimensions: bool = Form(default=True),
    edocr_extract_gdt: bool = Form(default=True),
    edocr_extract_text: bool = Form(default=True),
    edocr_extract_tables: bool = Form(default=True),
    edocr_visualize: bool = Form(default=False),
    edocr_language: str = Form(default='eng'),
    edocr_cluster_threshold: int = Form(default=20),
    # EDGNet hyperparameters
    edgnet_num_classes: int = Form(default=3),
    edgnet_visualize: bool = Form(default=True),
    edgnet_save_graph: bool = Form(default=False),
    # PaddleOCR hyperparameters
    paddle_det_db_thresh: float = Form(default=0.3),
    paddle_det_db_box_thresh: float = Form(default=0.5),
    paddle_min_confidence: float = Form(default=0.5),
    paddle_use_angle_cls: bool = Form(default=True),
    # Skin Model hyperparameters
    skin_material: str = Form(default='steel'),
    skin_manufacturing_process: str = Form(default='machining'),
    skin_correlation_length: float = Form(default=10.0)
):
    """
    Full pipeline processing

    - **file**: Drawing file (PDF or image)
    - **pipeline_mode**: Pipeline mode
      - **hybrid**: Accuracy priority (~95%, 10-15s)
      - **speed**: Speed priority (~93%, 8-10s)
    """
    start_time = time.time()

    file_bytes = await file.read()
    file_id = f"{int(time.time())}_{file.filename}"

    tracker = ProgressTracker(file_id)
    tracker.update("initialize", "started", f"Pipeline started: {pipeline_mode} mode", {
        "filename": file.filename,
        "pipeline_mode": pipeline_mode,
        "options": {
            "use_ocr": use_ocr,
            "use_segmentation": use_segmentation,
            "use_tolerance": use_tolerance,
            "visualize": visualize
        }
    })

    logger.info(f"Processing pipeline for {file_id}")
    logger.info(f"Pipeline mode: {pipeline_mode}")
    logger.info(f"Options: segment={use_segmentation}, ocr={use_ocr}, tolerance={use_tolerance}")

    result: Dict[str, Any] = {
        "yolo_results": None,
        "segmentation_results": None,
        "ocr_results": None,
        "tolerance_results": None,
        "ensemble": None,
        "pipeline_mode": pipeline_mode,
        "job_id": file_id
    }

    try:
        is_pdf = file.filename.lower().endswith('.pdf')

        image_bytes = file_bytes
        image_filename = file.filename
        if is_pdf:
            logger.info(f"PDF detected, converting to image: {file.filename}")
            image_bytes = pdf_to_image(file_bytes)
            image_filename = file.filename.rsplit('.', 1)[0] + '.png'

        # Run pipeline based on mode
        if pipeline_mode == "hybrid":
            await _run_hybrid_pipeline(
                result, tracker, file_bytes, image_bytes, image_filename, is_pdf,
                file, use_ocr, use_segmentation,
                yolo_conf_threshold, yolo_iou_threshold, yolo_imgsz, yolo_visualize,
                edocr_extract_dimensions, edocr_extract_gdt, edocr_extract_text,
                edocr_extract_tables, edocr_visualize, edocr_language, edocr_cluster_threshold,
                edgnet_num_classes, edgnet_visualize, edgnet_save_graph
            )
        else:
            await _run_speed_pipeline(
                result, tracker, file_bytes, image_bytes, image_filename, is_pdf,
                file, use_ocr, use_segmentation,
                yolo_conf_threshold, yolo_iou_threshold, yolo_imgsz, yolo_visualize,
                edocr_extract_dimensions, edocr_extract_gdt, edocr_extract_text,
                edocr_extract_tables, edocr_visualize, edocr_language, edocr_cluster_threshold,
                edgnet_num_classes, edgnet_visualize, edgnet_save_graph
            )

        # YOLO Crop OCR (optional)
        if use_yolo_crop_ocr and result.get("yolo_results"):
            await _run_yolo_crop_ocr(result, tracker, file_bytes, paddle_min_confidence)

        # Ensemble merging
        await _run_ensemble_merging(
            result, tracker, file_bytes, is_pdf, use_ensemble, use_yolo_crop_ocr
        )

        # Tolerance prediction
        if use_tolerance and result.get("ensemble", {}).get("dimensions"):
            await _run_tolerance_prediction(
                result, tracker, skin_material, skin_manufacturing_process, skin_correlation_length
            )

        processing_time = time.time() - start_time

        tracker.update("complete", "completed", f"Pipeline completed ({round(processing_time, 2)}s)", {
            "total_time": round(processing_time, 2),
            "pipeline_mode": pipeline_mode
        })

        # Save results
        saved_files, download_urls = _save_results(
            result, file_id, file.filename, file_bytes, processing_time, pipeline_mode
        )

        return {
            "status": "success",
            "data": result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id,
            "saved_files": saved_files,
            "download_urls": download_urls
        }

    except Exception as e:
        logger.error(f"Error in pipeline processing: {e}")
        tracker.update("error", "error", f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_hybrid_pipeline(
    result: Dict, tracker: ProgressTracker,
    file_bytes: bytes, image_bytes: bytes, image_filename: str, is_pdf: bool,
    file: UploadFile, use_ocr: bool, use_segmentation: bool,
    yolo_conf_threshold: float, yolo_iou_threshold: float, yolo_imgsz: int, yolo_visualize: bool,
    edocr_extract_dimensions: bool, edocr_extract_gdt: bool, edocr_extract_text: bool,
    edocr_extract_tables: bool, edocr_visualize: bool, edocr_language: str, edocr_cluster_threshold: int,
    edgnet_num_classes: int, edgnet_visualize: bool, edgnet_save_graph: bool
):
    """Run hybrid pipeline: YOLO -> Parallel (OCR + Segmentation)"""
    logger.info("Running HYBRID pipeline (accuracy priority)")
    tracker.update("pipeline", "started", "Hybrid pipeline started")

    # Step 1: YOLO detection
    tracker.update("yolo", "running", "Step 1: YOLO detection...")
    yolo_result = await call_yolo_detect(
        file_bytes=image_bytes,
        filename=image_filename,
        conf_threshold=yolo_conf_threshold,
        iou_threshold=yolo_iou_threshold,
        imgsz=yolo_imgsz,
        visualize=yolo_visualize,
        model_type="engineering",
        task="detect",
        use_sahi=False,
        slice_height=512,
        slice_width=512,
        overlap_ratio=0.25
    )
    result["yolo_results"] = yolo_result

    detections_count = yolo_result.get("total_detections", 0) if yolo_result else 0
    tracker.update("yolo", "completed", f"Step 1: {detections_count} objects detected", {
        "detection_count": detections_count,
        "processing_time": yolo_result.get("processing_time", 0) if yolo_result else 0
    })

    # Step 2: Parallel processing
    tracker.update("parallel", "running", "Step 2: Parallel analysis")
    tasks = []

    if use_ocr:
        tracker.update("ocr", "running", "eDOCr2 OCR...")
        tasks.append(call_edocr2_ocr(
            file_bytes if is_pdf else image_bytes,
            file.filename,
            extract_dimensions=edocr_extract_dimensions,
            extract_gdt=edocr_extract_gdt,
            extract_text=edocr_extract_text,
            extract_tables=edocr_extract_tables,
            visualize=edocr_visualize,
            language=edocr_language,
            cluster_threshold=edocr_cluster_threshold
        ))

    if use_segmentation:
        tracker.update("edgnet", "running", "EDGNet segmentation...")
        tasks.append(call_edgnet_segment(
            image_bytes,
            image_filename,
            visualize=edgnet_visualize,
            num_classes=edgnet_num_classes,
            save_graph=edgnet_save_graph
        ))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        _process_parallel_results(result, tracker, results, use_ocr, use_segmentation, image_bytes, is_pdf, file_bytes)


async def _run_speed_pipeline(
    result: Dict, tracker: ProgressTracker,
    file_bytes: bytes, image_bytes: bytes, image_filename: str, is_pdf: bool,
    file: UploadFile, use_ocr: bool, use_segmentation: bool,
    yolo_conf_threshold: float, yolo_iou_threshold: float, yolo_imgsz: int, yolo_visualize: bool,
    edocr_extract_dimensions: bool, edocr_extract_gdt: bool, edocr_extract_text: bool,
    edocr_extract_tables: bool, edocr_visualize: bool, edocr_language: str, edocr_cluster_threshold: int,
    edgnet_num_classes: int, edgnet_visualize: bool, edgnet_save_graph: bool
):
    """Run speed pipeline: 3-way parallel (YOLO + OCR + Segmentation)"""
    logger.info("Running SPEED pipeline")
    tracker.update("pipeline", "started", "Speed pipeline started")
    tracker.update("parallel", "running", "3-way parallel processing")

    tasks = [
        call_yolo_detect(
            file_bytes=image_bytes,
            filename=image_filename,
            conf_threshold=yolo_conf_threshold,
            iou_threshold=yolo_iou_threshold,
            imgsz=yolo_imgsz,
            visualize=yolo_visualize,
            model_type="engineering",
            task="detect",
            use_sahi=False,
            slice_height=512,
            slice_width=512,
            overlap_ratio=0.25
        )
    ]

    if use_ocr:
        tasks.append(call_edocr2_ocr(
            file_bytes if is_pdf else image_bytes,
            file.filename,
            extract_dimensions=edocr_extract_dimensions,
            extract_gdt=edocr_extract_gdt,
            extract_text=edocr_extract_text,
            extract_tables=edocr_extract_tables,
            visualize=edocr_visualize,
            language=edocr_language,
            cluster_threshold=edocr_cluster_threshold
        ))

    if use_segmentation:
        tasks.append(call_edgnet_segment(
            image_bytes,
            image_filename,
            visualize=edgnet_visualize,
            num_classes=edgnet_num_classes,
            save_graph=edgnet_save_graph
        ))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # YOLO result
    result["yolo_results"] = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
    if not isinstance(results[0], Exception):
        detections_count = results[0].get("total_detections", 0)
        tracker.update("yolo", "completed", f"YOLO: {detections_count} objects", {"detection_count": detections_count})
    else:
        tracker.update("yolo", "error", f"YOLO failed: {results[0]}")

    # OCR and segmentation results
    idx = 1
    if use_ocr:
        _process_ocr_result(result, tracker, results[idx], image_bytes, is_pdf, file_bytes)
        idx += 1

    if use_segmentation:
        _process_segmentation_result(result, tracker, results[idx], image_bytes, is_pdf, file_bytes)

    tracker.update("parallel", "completed", "3-way parallel completed")


def _process_parallel_results(
    result: Dict, tracker: ProgressTracker, results: list,
    use_ocr: bool, use_segmentation: bool,
    image_bytes: bytes, is_pdf: bool, file_bytes: bytes
):
    """Process parallel task results"""
    idx = 0

    if use_ocr:
        _process_ocr_result(result, tracker, results[idx], image_bytes, is_pdf, file_bytes)
        idx += 1

    if use_segmentation:
        _process_segmentation_result(result, tracker, results[idx], image_bytes, is_pdf, file_bytes)


def _process_ocr_result(result: Dict, tracker: ProgressTracker, ocr_result, image_bytes: bytes, is_pdf: bool, file_bytes: bytes):
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


def _process_segmentation_result(result: Dict, tracker: ProgressTracker, seg_result, image_bytes: bytes, is_pdf: bool, file_bytes: bytes):
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


async def _run_yolo_crop_ocr(result: Dict, tracker: ProgressTracker, file_bytes: bytes, min_confidence: float):
    """Run YOLO crop-based OCR"""
    logger.info("Running YOLO Crop OCR")
    tracker.update("yolo_crop_ocr", "running", "YOLO crop OCR...")

    yolo_detections = result["yolo_results"].get("detections", [])
    if not yolo_detections:
        tracker.update("yolo_crop_ocr", "skipped", "No YOLO detections")
        result["yolo_crop_ocr_results"] = None
        return

    try:
        yolo_crop_ocr_result = await process_yolo_crop_ocr(
            image_bytes=file_bytes,
            yolo_detections=yolo_detections,
            call_edocr2_ocr_func=call_edocr2_ocr,
            crop_bbox_func=crop_bbox,
            is_false_positive_func=is_false_positive,
            dimension_class_ids=[0, 1, 2, 3, 4, 5, 6],
            min_confidence=min_confidence,
            padding=0.1
        )
        result["yolo_crop_ocr_results"] = yolo_crop_ocr_result
        tracker.update("yolo_crop_ocr", "completed",
                       f"YOLO Crop OCR: {yolo_crop_ocr_result['total_texts']} texts",
                       {"dimensions_count": yolo_crop_ocr_result['total_texts']})
    except Exception as e:
        logger.error(f"YOLO Crop OCR failed: {e}")
        tracker.update("yolo_crop_ocr", "error", f"Failed: {e}")
        result["yolo_crop_ocr_results"] = {"error": str(e)}


async def _run_ensemble_merging(
    result: Dict, tracker: ProgressTracker,
    file_bytes: bytes, is_pdf: bool,
    use_ensemble: bool, use_yolo_crop_ocr: bool
):
    """Run ensemble merging of OCR results"""
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


async def _run_tolerance_prediction(
    result: Dict, tracker: ProgressTracker,
    material: str, manufacturing_process: str, correlation_length: float
):
    """Run tolerance prediction"""
    logger.info("Tolerance prediction")
    tracker.update("tolerance", "running", "Skin Model tolerance prediction...")

    ensemble_dimensions = result["ensemble"]["dimensions"]
    material_info = result.get("ocr_results", {}).get("data", {}).get("text", {}).get("material") or "Steel"

    tolerance_result = await call_skinmodel_tolerance(
        ensemble_dimensions,
        {"name": material_info},
        material_type=material,
        manufacturing_process=manufacturing_process,
        correlation_length=correlation_length
    )
    result["tolerance_results"] = tolerance_result
    tracker.update("tolerance", "completed", "Tolerance prediction completed")


def _save_results(
    result: Dict, file_id: str, filename: str, file_bytes: bytes,
    processing_time: float, pipeline_mode: str
) -> tuple:
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
