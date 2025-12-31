"""
Download Router - /api/v1/download/* endpoints
File download endpoints for results and quotes

Refactored from api_server.py (2025-12-31)
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from constants import RESULTS_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["download"])


@router.get("/download/{file_id}/{file_type}")
async def download_result_file(file_id: str, file_type: str):
    """
    Download result file

    Args:
        file_id: File ID
        file_type: File type (original, yolo_visualization, result_json)
    """
    try:
        project_dir = RESULTS_DIR / file_id

        if not project_dir.exists():
            raise HTTPException(status_code=404, detail=f"Project {file_id} not found")

        # Determine file path based on type
        if file_type == "yolo_visualization":
            file_path = project_dir / "yolo_visualization.jpg"
            media_type = "image/jpeg"
            filename = f"{file_id}_yolo_visualization.jpg"
        elif file_type == "result_json":
            file_path = project_dir / "result.json"
            media_type = "application/json"
            filename = f"{file_id}_result.json"
        elif file_type == "original":
            # Find original file (unknown extension)
            original_files = list(project_dir.glob("original.*"))
            if not original_files:
                raise HTTPException(status_code=404, detail="Original file not found")
            file_path = original_files[0]
            media_type = "application/octet-stream"
            filename = f"{file_id}_original{file_path.suffix}"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid file_type: {file_type}")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {file_type} not found")

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download_quote/{quote_number}")
async def download_quote(quote_number: str):
    """Download quote PDF"""
    try:
        pdf_path = RESULTS_DIR / f"{quote_number}.pdf"

        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"Quote {quote_number} not found")

        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=f"quote_{quote_number}.pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))
