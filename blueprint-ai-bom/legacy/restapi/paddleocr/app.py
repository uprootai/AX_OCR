#!/usr/bin/env python3
"""
PaddleOCR API Service - Optimized for CAD symbols
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import base64
from typing import List, Dict, Any
import io
from PIL import Image

app = FastAPI(title="PaddleOCR API", version="2.0.0")

# Global OCR reader
ocr_reader = None

def init_paddleocr():
    """Initialize PaddleOCR with optimized settings for CAD symbols"""
    global ocr_reader
    try:
        from paddleocr import PaddleOCR
        ocr_reader = PaddleOCR(lang='en')
        print("✅ PaddleOCR initialized successfully")
        return True
    except Exception as e:
        print(f"❌ PaddleOCR initialization failed: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize OCR on startup"""
    success = init_paddleocr()
    if not success:
        print("⚠️ PaddleOCR not available, service will return errors")

@app.get("/")
def root():
    return {"service": "PaddleOCR API", "status": "running", "available": ocr_reader is not None}

@app.get("/health")
def health_check():
    return {
        "status": "healthy" if ocr_reader is not None else "degraded",
        "ocr_engine": "PaddleOCR",
        "optimizations": ["angle_classification", "low_thresholds", "cad_tuned"]
    }

@app.post("/ocr")
async def perform_ocr(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.3
):
    """
    Perform OCR on uploaded image with CAD optimization
    """
    if ocr_reader is None:
        raise HTTPException(status_code=503, detail="PaddleOCR not available")

    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        # Perform OCR
        results = ocr_reader.ocr(img)

        # Process results
        ocr_results = []
        full_texts = []

        if results and len(results) > 0:
            # PaddleOCR 3.x returns OCRResult object
            page_result = results[0]

            # Check if it's the new OCRResult format
            if hasattr(page_result, '__getitem__') and 'rec_texts' in page_result:
                # New PaddleOCR 3.x format
                texts = page_result.get('rec_texts', [])
                scores = page_result.get('rec_scores', [])
                boxes = page_result.get('dt_polys', [])

                for i, (text, score) in enumerate(zip(texts, scores)):
                    if score >= confidence_threshold and text.strip():
                        bbox = boxes[i] if i < len(boxes) else [[0,0], [0,0], [0,0], [0,0]]

                        # Extract coordinates
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]

                        ocr_results.append({
                            "text": text.strip(),
                            "confidence": float(score),
                            "bbox": {
                                "x1": int(min(x_coords)) if x_coords else 0,
                                "y1": int(min(y_coords)) if y_coords else 0,
                                "x2": int(max(x_coords)) if x_coords else 0,
                                "y2": int(max(y_coords)) if y_coords else 0
                            }
                        })
                        full_texts.append(text.strip())
            else:
                # Fallback to old format
                for line in page_result if isinstance(page_result, list) else []:
                    if len(line) >= 2:
                        bbox, (text, confidence) = line[0], line[1]

                        if confidence >= confidence_threshold and text.strip():
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]

                            ocr_results.append({
                                "text": text.strip(),
                                "confidence": float(confidence),
                                "bbox": {
                                    "x1": int(min(x_coords)),
                                    "y1": int(min(y_coords)),
                                    "x2": int(max(x_coords)),
                                    "y2": int(max(y_coords))
                                }
                            })
                            full_texts.append(text.strip())

        return JSONResponse({
            "success": True,
            "texts": ocr_results,
            "full_text": " ".join(full_texts),
            "total_detections": len(ocr_results),
            "engine": "PaddleOCR"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

@app.post("/ocr/base64")
async def perform_ocr_base64(data: dict):
    """
    Perform OCR on base64 encoded image
    """
    if ocr_reader is None:
        raise HTTPException(status_code=503, detail="PaddleOCR not available")

    try:
        # Extract parameters
        image_base64 = data.get('image_base64')
        confidence_threshold = data.get('confidence_threshold', 0.3)

        if not image_base64:
            raise HTTPException(status_code=400, detail="image_base64 required")

        # Decode base64
        img_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        # Perform OCR
        results = ocr_reader.ocr(img)

        # Process results (same as above)
        ocr_results = []
        full_texts = []

        if results and len(results) > 0:
            # PaddleOCR 3.x returns OCRResult object
            page_result = results[0]

            # Check if it's the new OCRResult format
            if hasattr(page_result, '__getitem__') and 'rec_texts' in page_result:
                # New PaddleOCR 3.x format
                texts = page_result.get('rec_texts', [])
                scores = page_result.get('rec_scores', [])
                boxes = page_result.get('dt_polys', [])

                for i, (text, score) in enumerate(zip(texts, scores)):
                    if score >= confidence_threshold and text.strip():
                        bbox = boxes[i] if i < len(boxes) else [[0,0], [0,0], [0,0], [0,0]]

                        # Extract coordinates
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]

                        ocr_results.append({
                            "text": text.strip(),
                            "confidence": float(score),
                            "bbox": {
                                "x1": int(min(x_coords)) if x_coords else 0,
                                "y1": int(min(y_coords)) if y_coords else 0,
                                "x2": int(max(x_coords)) if x_coords else 0,
                                "y2": int(max(y_coords)) if y_coords else 0
                            }
                        })
                        full_texts.append(text.strip())
            else:
                # Fallback to old format
                for line in page_result if isinstance(page_result, list) else []:
                    if len(line) >= 2:
                        bbox, (text, confidence) = line[0], line[1]

                        if confidence >= confidence_threshold and text.strip():
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]

                            ocr_results.append({
                                "text": text.strip(),
                                "confidence": float(confidence),
                                "bbox": {
                                    "x1": int(min(x_coords)),
                                    "y1": int(min(y_coords)),
                                    "x2": int(max(x_coords)),
                                    "y2": int(max(y_coords))
                                }
                            })
                            full_texts.append(text.strip())

        return JSONResponse({
            "success": True,
            "texts": ocr_results,
            "full_text": " ".join(full_texts),
            "total_detections": len(ocr_results),
            "engine": "PaddleOCR"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)