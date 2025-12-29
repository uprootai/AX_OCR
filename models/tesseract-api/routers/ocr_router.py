"""
Tesseract Router - OCR Endpoints
"""
import io
import time
import logging

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from schemas import OCRResult, OCRResponse
from services import TESSERACT_AVAILABLE, pytesseract, Image, get_tesseract_version

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ocr"])


@router.get("/info")
async def get_info():
    """API info (BlueprintFlow metadata)"""
    return {
        "name": "Tesseract OCR",
        "type": "tesseract",
        "category": "ocr",
        "description": "Google Tesseract based OCR engine - document text recognition",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "lang",
                "type": "select",
                "default": "eng",
                "options": ["eng", "kor", "jpn", "chi_sim", "chi_tra", "eng+kor"],
                "description": "Recognition language"
            },
            {
                "name": "psm",
                "type": "select",
                "default": "3",
                "options": ["0", "1", "3", "4", "6", "7", "11", "12", "13"],
                "description": "Page Segmentation Mode (3: auto, 6: single block, 11: sparse text)"
            },
            {
                "name": "oem",
                "type": "select",
                "default": "3",
                "options": ["0", "1", "2", "3"],
                "description": "OCR Engine Mode (0: Legacy, 1: LSTM, 3: default)"
            },
            {
                "name": "output_type",
                "type": "select",
                "default": "data",
                "options": ["string", "data", "dict"],
                "description": "Output format (string: text only, data: with positions)"
            }
        ],
        "inputs": [
            {"name": "image", "type": "Image", "description": "Input image"}
        ],
        "outputs": [
            {"name": "texts", "type": "OCRResult[]", "description": "Recognition results"},
            {"name": "full_text", "type": "string", "description": "Full text"}
        ],
        "ensemble_weight": 0.15
    }


@router.post("/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(...),
    lang: str = Form(default="eng"),
    psm: str = Form(default="3"),
    oem: str = Form(default="3"),
    output_type: str = Form(default="data")
):
    """
    Perform Tesseract OCR

    Args:
        file: Image file
        lang: Language code (eng, kor, jpn, chi_sim, eng+kor)
        psm: Page Segmentation Mode
        oem: OCR Engine Mode
        output_type: Output format (string, data, dict)
    """
    start_time = time.time()

    if not TESSERACT_AVAILABLE:
        return OCRResponse(
            success=False,
            texts=[],
            full_text="",
            language=lang,
            processing_time_ms=0,
            error="Tesseract is not installed"
        )

    try:
        # Load image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Tesseract config
        custom_config = f"--psm {psm} --oem {oem}"

        texts = []
        full_text = ""

        if output_type == "string":
            full_text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
            texts = [OCRResult(text=full_text.strip(), confidence=0.9)]

        elif output_type == "data":
            data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)

            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i]) if data['conf'][i] != '-1' else 0

                if text and conf > 0:
                    bbox = [
                        data['left'][i],
                        data['top'][i],
                        data['left'][i] + data['width'][i],
                        data['top'][i] + data['height'][i]
                    ]
                    texts.append(OCRResult(
                        text=text,
                        confidence=conf / 100.0,
                        bbox=bbox,
                        level=data['level'][i]
                    ))

            full_text = " ".join([t.text for t in texts])

        else:  # dict
            data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)
            full_text = pytesseract.image_to_string(image, lang=lang, config=custom_config)

            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:
                    texts.append(OCRResult(
                        text=text,
                        confidence=float(data['conf'][i]) / 100.0 if data['conf'][i] != '-1' else 0,
                        bbox=[data['left'][i], data['top'][i],
                              data['left'][i] + data['width'][i],
                              data['top'][i] + data['height'][i]],
                        level=data['level'][i]
                    ))

        processing_time = (time.time() - start_time) * 1000

        logger.info(f"Tesseract OCR complete: {len(texts)} texts, {processing_time:.1f}ms")

        return OCRResponse(
            success=True,
            texts=texts,
            full_text=full_text.strip(),
            language=lang,
            processing_time_ms=processing_time,
            tesseract_version=get_tesseract_version()
        )

    except Exception as e:
        logger.error(f"Tesseract OCR error: {e}")
        return OCRResponse(
            success=False,
            texts=[],
            full_text="",
            language=lang,
            processing_time_ms=(time.time() - start_time) * 1000,
            error=str(e)
        )


@router.post("/ocr/boxes")
async def get_bounding_boxes(
    file: UploadFile = File(...),
    lang: str = Form(default="eng")
):
    """Extract text bounding boxes only (YOLO-like format)"""
    if not TESSERACT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tesseract not available")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        if image.mode != "RGB":
            image = image.convert("RGB")

        # Extract bounding boxes
        boxes = pytesseract.image_to_boxes(image, lang=lang, output_type=pytesseract.Output.DICT)

        results = []
        h, w = image.size[1], image.size[0]

        for i in range(len(boxes['char'])):
            char = boxes['char'][i]
            # Tesseract boxes are based on bottom-left, so transform
            x1, y1, x2, y2 = boxes['left'][i], h - boxes['top'][i], boxes['right'][i], h - boxes['bottom'][i]
            results.append({
                "char": char,
                "bbox": [x1, min(y1, y2), x2, max(y1, y2)]
            })

        return {
            "success": True,
            "boxes": results,
            "image_size": {"width": w, "height": h}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
