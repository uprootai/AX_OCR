"""
Quote Router - /api/v1/quote and /api/v1/process_with_vl endpoints
Quote generation and VL-based processing

Refactored from api_server.py (2025-12-31)
"""

import os
import time
import json
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

from models import QuoteResponse
from utils import pdf_to_image
from services import (
    call_edocr2_ocr, call_edgnet_segment,
    call_skinmodel_tolerance, calculate_quote
)
from cost_estimator import get_cost_estimator
from pdf_generator import get_pdf_generator
from constants import RESULTS_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["quote"])

# Configuration
VL_API_URL = os.getenv("VL_API_URL", "http://vl-api:5004")


@router.post("/quote", response_model=QuoteResponse)
async def generate_quote(
    file: UploadFile = File(..., description="Drawing file"),
    material_cost_per_kg: float = Form(5.0),
    machining_rate_per_hour: float = Form(50.0),
    tolerance_premium_factor: float = Form(1.2),
    skin_material: str = Form(default='steel'),
    skin_manufacturing_process: str = Form(default='machining'),
    skin_correlation_length: float = Form(default=10.0)
):
    """
    Generate quote (full pipeline + cost calculation)

    - **file**: Drawing file
    - **material_cost_per_kg**: Material cost (USD/kg)
    - **machining_rate_per_hour**: Machining rate (USD/hour)
    - **tolerance_premium_factor**: Tolerance precision cost factor
    """
    start_time = time.time()
    file_bytes = await file.read()

    try:
        logger.info("Running full pipeline for quote generation")

        ocr_task = call_edocr2_ocr(file_bytes, file.filename)
        segment_task = call_edgnet_segment(file_bytes, file.filename, visualize=False)

        ocr_result, segment_result = await asyncio.gather(ocr_task, segment_task, return_exceptions=True)

        if isinstance(ocr_result, Exception):
            raise ocr_result

        # Tolerance prediction
        ocr_data = ocr_result.get("data", ocr_result)
        dimensions = ocr_data.get("dimensions", [])
        material = ocr_data.get("text", {}).get("material") or "Steel"

        tolerance_result = await call_skinmodel_tolerance(
            dimensions,
            {"name": material},
            material_type=skin_material,
            manufacturing_process=skin_manufacturing_process,
            correlation_length=skin_correlation_length
        )

        # Calculate quote
        quote_data = calculate_quote(
            ocr_result,
            tolerance_result,
            material_cost_per_kg,
            machining_rate_per_hour,
            tolerance_premium_factor
        )

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "data": {
                "quote": quote_data,
                "ocr_summary": {
                    "dimensions_count": len(dimensions),
                    "drawing_number": ocr_data.get("text", {}).get("drawing_number"),
                    "material": material
                },
                "tolerance_summary": tolerance_result.get("data", {}).get("manufacturability", {})
            },
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"Error in quote generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process_with_vl")
async def process_with_vl(
    file: UploadFile = File(...),
    model: str = Form(default="claude-3-5-sonnet-20241022"),
    quantity: int = Form(default=1),
    customer_name: str = Form(default="N/A")
):
    """
    VL model based integrated processing (replaces eDOCr)

    - Information Block extraction
    - Dimension extraction (VL model)
    - Manufacturing process inference
    - Cost estimation
    - QC Checklist generation
    - Quote PDF generation
    """
    start_time = time.time()

    try:
        file_bytes = await file.read()
        filename = file.filename or "unknown.pdf"

        logger.info(f"Starting VL-based processing for {filename}")

        # Convert PDF to image if needed
        if filename.lower().endswith('.pdf'):
            image_bytes = pdf_to_image(file_bytes, dpi=200)
        else:
            image_bytes = file_bytes

        # 1. Information Block extraction
        logger.info("Step 1: Extracting information block...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            files_info = {"file": (filename, image_bytes, "image/png")}
            data_info = {
                "query_fields": json.dumps(["name", "part number", "material", "scale", "weight"]),
                "model": model
            }

            response_info = await client.post(
                f"{VL_API_URL}/api/v1/extract_info_block",
                files=files_info,
                data=data_info
            )

            if response_info.status_code != 200:
                raise HTTPException(
                    status_code=response_info.status_code,
                    detail=f"Info extraction failed: {response_info.text}"
                )

            info_block_data = response_info.json()["data"]

        # 2. Dimension extraction (VL model)
        logger.info("Step 2: Extracting dimensions with VL model...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            files_dim = {"file": (filename, image_bytes, "image/png")}
            data_dim = {"model": model}

            response_dim = await client.post(
                f"{VL_API_URL}/api/v1/extract_dimensions",
                files=files_dim,
                data=data_dim
            )

            if response_dim.status_code != 200:
                raise HTTPException(
                    status_code=response_dim.status_code,
                    detail=f"Dimension extraction failed: {response_dim.text}"
                )

            dimensions_data = response_dim.json()["data"]

        # 3. Manufacturing process inference
        logger.info("Step 3: Inferring manufacturing processes...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            files_proc = {
                "info_block": (filename, image_bytes, "image/png"),
                "part_views": (filename, image_bytes, "image/png")
            }
            data_proc = {"model": "gpt-4o"}

            response_proc = await client.post(
                f"{VL_API_URL}/api/v1/infer_manufacturing_process",
                files=files_proc,
                data=data_proc
            )

            if response_proc.status_code != 200:
                logger.warning(f"Process inference failed: {response_proc.text}")
                manufacturing_processes = {"Machining": "General machining processes"}
            else:
                manufacturing_processes = response_proc.json()["data"]

        # 4. QC Checklist generation
        logger.info("Step 4: Generating QC checklist...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            files_qc = {"file": (filename, image_bytes, "image/png")}
            data_qc = {"model": "gpt-4o"}

            response_qc = await client.post(
                f"{VL_API_URL}/api/v1/generate_qc_checklist",
                files=files_qc,
                data=data_qc
            )

            if response_qc.status_code != 200:
                logger.warning(f"QC checklist generation failed: {response_qc.text}")
                qc_checklist = []
            else:
                qc_checklist = response_qc.json()["data"]

        # 5. Cost estimation
        logger.info("Step 5: Estimating cost...")
        cost_estimator = get_cost_estimator()
        material = info_block_data.get("material", "Mild Steel")

        cost_breakdown = cost_estimator.estimate_cost(
            manufacturing_processes=manufacturing_processes,
            material=material,
            dimensions=dimensions_data,
            gdt_count=0,
            tolerance_count=len([d for d in dimensions_data if '±' in d or '+' in d or '-' in d]),
            quantity=quantity
        )

        # 6. Quote PDF generation
        logger.info("Step 6: Generating quote PDF...")
        pdf_generator = get_pdf_generator()

        quote_number = f"Q-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        quote_data = {
            "quote_number": quote_number,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "customer_name": customer_name,
            "part_info": {
                "name": info_block_data.get("name", "N/A"),
                "part_number": info_block_data.get("part number", "N/A"),
                "material": material,
                "quantity": quantity
            },
            "cost_breakdown": cost_breakdown,
            "qc_checklist": qc_checklist,
            "manufacturing_processes": manufacturing_processes
        }

        pdf_bytes = pdf_generator.generate_quote_pdf(quote_data)

        # Save PDF
        pdf_path = RESULTS_DIR / f"{quote_number}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)

        processing_time = time.time() - start_time
        logger.info(f"VL-based processing completed in {processing_time:.2f}s")

        return JSONResponse({
            "status": "success",
            "data": {
                "quote_number": quote_number,
                "info_block": info_block_data,
                "dimensions": dimensions_data,
                "dimensions_count": len(dimensions_data),
                "manufacturing_processes": manufacturing_processes,
                "cost_breakdown": cost_breakdown,
                "qc_checklist": qc_checklist,
                "pdf_path": str(pdf_path)
            },
            "processing_time": round(processing_time, 2),
            "model_used": model
        })

    except Exception as e:
        logger.error(f"VL-based processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
