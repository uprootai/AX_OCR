"""
VL API Analysis Router
VL 모델 분석 엔드포인트
"""

import io
import json
import time
import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from PIL import Image

from schemas import (
    InfoBlockResponse,
    DimensionExtractionResponse,
    ManufacturingProcessResponse,
    QCChecklistResponse,
    AnalyzeResponse,
)
from services import (
    call_claude_api,
    call_openai_gpt4v_api,
    call_local_vl_api,
    parse_json_from_text,
    get_florence_model,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Analysis"])


@router.get("/info")
async def get_api_info():
    """
    API 메타데이터 - BlueprintFlow Auto Discover용
    """
    return {
        "id": "vl",
        "name": "VL",
        "display_name": "Vision-Language Model",
        "version": "1.0.0",
        "description": "이미지와 텍스트를 함께 이해하는 멀티모달 AI. 도면 분석, 질문-답변, 설명 생성",
        "endpoint": "/api/v1/analyze",
        "method": "POST",
        "requires_image": True,

        # 입력 정의
        "inputs": [
            {"name": "file", "type": "Image", "required": True, "description": "분석할 이미지 (도면, 사진 등)"},
            {"name": "prompt", "type": "Text", "required": False, "description": "질문 또는 분석 요청 (선택사항)"}
        ],

        # 출력 정의
        "outputs": [
            {"name": "mode", "type": "String", "description": "분석 모드 (vqa/captioning)"},
            {"name": "answer", "type": "String", "description": "질문에 대한 답변"},
            {"name": "caption", "type": "String", "description": "이미지 설명"},
            {"name": "confidence", "type": "Float", "description": "답변 신뢰도"}
        ],

        # 파라미터 정의
        "parameters": [
            {
                "name": "model",
                "type": "select",
                "options": ["claude-3-5-sonnet-20241022", "gpt-4o", "blip-base"],
                "default": "claude-3-5-sonnet-20241022",
                "description": "VL 모델 선택"
            },
            {
                "name": "temperature",
                "type": "float",
                "default": 0.0,
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
                "description": "생성 다양성 (0=결정적, 1=창의적)"
            }
        ],

        # BlueprintFlow 메타데이터
        "blueprintflow": {
            "category": "ai",
            "color": "#6366f1",
            "icon": "Sparkles"
        },

        # 입출력 매핑 (BlueprintFlow 노드 연결용)
        "input_mappings": {
            "file": "image",
            "prompt": "question"
        },

        # 출력 필드 매핑
        "output_mappings": {
            "mode": "mode",
            "answer": "answer",
            "caption": "caption",
            "confidence": "confidence"
        }
    }


@router.post("/extract_info_block", response_model=InfoBlockResponse)
async def extract_info_block(
    file: UploadFile = File(...),
    query_fields: str = Form(default='["name", "part number", "material", "scale", "weight"]'),
    model: str = Form(default="claude-3-5-sonnet-20241022"),
    temperature: float = Form(default=0.0, description="Generation temperature (0-1, 0=deterministic, 1=creative)")
):
    """
    Information Block에서 특정 정보 추출

    논문 섹션 4.1 구현
    """
    start_time = time.time()

    try:
        # 파일 읽기
        image_bytes = await file.read()

        # query_fields 파싱
        fields = json.loads(query_fields)

        # 프롬프트 생성
        prompt = f"""Based on the image, return only a python dictionary extracting this information: {fields}.

The image contains an engineering drawing information block (title block). Extract the requested fields exactly as they appear.

Return ONLY a valid JSON dictionary with the field names as keys and extracted values as values. If a field is not found, use null as the value.

Example format:
{{
    "name": "Intermediate Shaft",
    "part number": "A12-311197-9",
    "material": "STS304",
    "scale": "1:2",
    "weight": "5.2kg"
}}"""

        # 모델 선택 및 호출
        if model.startswith("claude"):
            response_text = await call_claude_api(image_bytes, prompt, model, temperature=temperature)
        elif model.startswith("gpt"):
            response_text = await call_openai_gpt4v_api(image_bytes, prompt, model, temperature=temperature)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

        # JSON 파싱
        extracted_data = parse_json_from_text(response_text)

        processing_time = time.time() - start_time

        logger.info(f"Extracted info block: {extracted_data}")

        return InfoBlockResponse(
            status="success",
            data=extracted_data,
            processing_time=processing_time,
            model_used=model
        )

    except Exception as e:
        logger.error(f"Info block extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract_dimensions", response_model=DimensionExtractionResponse)
async def extract_dimensions(
    file: UploadFile = File(...),
    model: str = Form(default="claude-3-5-sonnet-20241022"),
    temperature: float = Form(default=0.0, description="Generation temperature (0-1)")
):
    """
    VL 모델로 치수 추출 (eDOCr 대체)

    논문 섹션 4.4 구현
    """
    start_time = time.time()

    try:
        # 파일 읽기
        image_bytes = await file.read()

        # 프롬프트 생성 (논문에서 제시한 System Role + Query)
        prompt = """You are a specialized OCR system capable of reading mechanical drawings. You read:
- Measurements: usually scattered and oriented text in the image with arrows in the surroundings. If tolerances are present, read them as "nominal +upper -lower", e.g., "10 +0.1 -0.0"
- Angles: usually oriented text with arrows in the surroundings

Based on the image, return only a python list of strings extracting dimensions.

Examples:
["φ476", "φ370", "φ9.204 +0.1 -0.2", "φ1313±2", "(177)", "7±0.5", "5mm", "1.5", "5"]

Return ONLY a valid JSON list of dimension strings. Do not include any other text or explanation."""

        # 모델 선택 및 호출
        if model.startswith("claude"):
            response_text = await call_claude_api(image_bytes, prompt, model, temperature=temperature)
        elif model.startswith("gpt"):
            response_text = await call_openai_gpt4v_api(image_bytes, prompt, model, temperature=temperature)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

        # JSON 파싱
        dimensions = parse_json_from_text(response_text)

        if not isinstance(dimensions, list):
            raise ValueError("Response is not a list")

        processing_time = time.time() - start_time

        logger.info(f"Extracted {len(dimensions)} dimensions")

        return DimensionExtractionResponse(
            status="success",
            data=dimensions,
            processing_time=processing_time,
            model_used=model
        )

    except Exception as e:
        logger.error(f"Dimension extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/infer_manufacturing_process", response_model=ManufacturingProcessResponse)
async def infer_manufacturing_process(
    info_block: UploadFile = File(...),
    part_views: UploadFile = File(...),
    model: str = Form(default="gpt-4o"),
    temperature: float = Form(default=0.0, description="Generation temperature (0-1)")
):
    """
    제조 공정 추론

    논문 섹션 4.2 구현
    """
    start_time = time.time()

    try:
        # 파일 읽기
        info_block_bytes = await info_block.read()
        part_views_bytes = await part_views.read()

        # 프롬프트 생성 (논문에서 제시한 Query)
        prompt = """You are getting the information block of the drawing in the first image and the views of the part in the second image.

I need you to return a python dictionary with the manufacturing processes (keys) and short description (values) that are best for this part.

Consider:
- Part geometry (cylindrical, flat surfaces, holes, etc.)
- Material specifications
- Tolerances and surface finish requirements
- GD&T specifications

Return ONLY a valid JSON dictionary. Example format:
{
    "Turning": "Used for creating the cylindrical shape of the part, including the outer diameters and chamfers",
    "Drilling/Boring": "To achieve the internal diameter and the countersink specified",
    "Milling": "For creating the flat surfaces if needed",
    "Reaming": "To ensure the internal diameter precision",
    "Grinding": "To achieve the surface finish required on precise diameters",
    "Deburring": "To break all sharp edges and remove burrs as specified"
}"""

        # 두 이미지를 하나로 합치기 (side-by-side)
        img1 = Image.open(io.BytesIO(info_block_bytes))
        img2 = Image.open(io.BytesIO(part_views_bytes))

        # 새 이미지 생성 (가로로 나란히)
        total_width = img1.width + img2.width
        max_height = max(img1.height, img2.height)
        combined_img = Image.new('RGB', (total_width, max_height), (255, 255, 255))
        combined_img.paste(img1, (0, 0))
        combined_img.paste(img2, (img1.width, 0))

        # bytes로 변환
        img_byte_arr = io.BytesIO()
        combined_img.save(img_byte_arr, format='PNG')
        combined_bytes = img_byte_arr.getvalue()

        # 모델 호출
        if model.startswith("claude"):
            response_text = await call_claude_api(combined_bytes, prompt, model)
        elif model.startswith("gpt"):
            response_text = await call_openai_gpt4v_api(combined_bytes, prompt, model)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

        # JSON 파싱
        processes = parse_json_from_text(response_text)

        if not isinstance(processes, dict):
            raise ValueError("Response is not a dictionary")

        processing_time = time.time() - start_time

        logger.info(f"Inferred {len(processes)} manufacturing processes")

        return ManufacturingProcessResponse(
            status="success",
            data=processes,
            processing_time=processing_time,
            model_used=model
        )

    except Exception as e:
        logger.error(f"Manufacturing process inference failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate_qc_checklist", response_model=QCChecklistResponse)
async def generate_qc_checklist(
    file: UploadFile = File(...),
    model: str = Form(default="gpt-4o"),
    temperature: float = Form(default=0.0, description="Generation temperature (0-1)")
):
    """
    품질 관리 체크리스트 자동 생성

    논문 섹션 4.3 구현
    """
    start_time = time.time()

    try:
        # 파일 읽기
        image_bytes = await file.read()

        # 프롬프트 생성 (논문에서 제시한 Query)
        prompt = """I need you to provide a Python list containing only the measurements—numerical values and tolerances—that need to be checked in the quality control process.

Focus on:
- Critical dimensions that affect part fit and assembly
- Dimensions with tight tolerances
- Dimensions with GD&T specifications
- Surface finish requirements

Return ONLY a valid JSON list of measurement strings. Example:
["Ø21.5 ± 0.1", "Ø38 H12", "Ra 1.6", "Flatness 0.05"]

Do not include reference dimensions or non-critical measurements."""

        # 모델 호출
        if model.startswith("claude"):
            response_text = await call_claude_api(image_bytes, prompt, model)
        elif model.startswith("gpt"):
            response_text = await call_openai_gpt4v_api(image_bytes, prompt, model)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

        # JSON 파싱
        checklist = parse_json_from_text(response_text)

        if not isinstance(checklist, list):
            raise ValueError("Response is not a list")

        processing_time = time.time() - start_time

        logger.info(f"Generated QC checklist with {len(checklist)} items")

        return QCChecklistResponse(
            status="success",
            data=checklist,
            processing_time=processing_time,
            model_used=model
        )

    except Exception as e:
        logger.error(f"QC checklist generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None, description="질문 또는 분석 요청 (선택사항)"),
    model: str = Form(default="claude-3-5-sonnet-20241022"),
    temperature: float = Form(default=0.0, ge=0.0, le=1.0)
):
    """
    범용 VQA (Visual Question Answering) 엔드포인트

    - prompt가 있으면: 질문-답변 모드 (VQA)
    - prompt가 없으면: 일반 이미지 캡셔닝 모드

    Examples:
        - "이 도면의 모든 치수를 추출해주세요"
        - "용접 기호를 찾아주세요"
        - "이 부품의 재질은 무엇인가요?"
    """
    start_time = time.time()
    _florence_model = get_florence_model()

    try:
        # 파일 읽기
        image_bytes = await file.read()

        # 프롬프트가 있으면 VQA 모드, 없으면 캡셔닝 모드
        if prompt and prompt.strip():
            # VQA (Visual Question Answering) 모드
            system_prompt = f"""You are an expert in analyzing engineering drawings and mechanical parts.

User Question: {prompt}

Please answer the question based on the image. Be specific and accurate. If you cannot find the requested information, clearly state that."""

            # VL 모델 호출
            if model.startswith("claude"):
                response_text = await call_claude_api(image_bytes, system_prompt, model, temperature=temperature)
            elif model.startswith("gpt"):
                response_text = await call_openai_gpt4v_api(image_bytes, system_prompt, model, temperature=temperature)
            elif model.startswith("blip") or model.startswith("florence"):
                response_text = await call_local_vl_api(image_bytes, prompt, "vqa")
            else:
                # 지원되지 않는 모델인 경우 로컬 모델 폴백
                if _florence_model is not None:
                    logger.warning(f"Unsupported model {model}, falling back to BLIP")
                    response_text = await call_local_vl_api(image_bytes, prompt, "vqa")
                    model = "blip-base"
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

            processing_time = time.time() - start_time

            logger.info(f"VQA completed: Q='{prompt}' A='{response_text[:100]}...'")

            return AnalyzeResponse(
                status="success",
                mode="vqa",
                answer=response_text,
                question=prompt,
                confidence=0.95,  # VL 모델의 기본 신뢰도
                processing_time=processing_time,
                model_used=model
            )

        else:
            # 일반 이미지 캡셔닝 모드
            caption_prompt = """Describe this engineering drawing or mechanical part in detail. Include:
- Type of drawing (assembly, detail, section view, etc.)
- Main components visible
- Key features (dimensions, symbols, annotations)
- Overall purpose or function

Provide a concise but informative description."""

            # VL 모델 호출
            if model.startswith("claude"):
                caption_text = await call_claude_api(image_bytes, caption_prompt, model, temperature=temperature)
            elif model.startswith("gpt"):
                caption_text = await call_openai_gpt4v_api(image_bytes, caption_prompt, model, temperature=temperature)
            elif model.startswith("blip") or model.startswith("florence"):
                caption_text = await call_local_vl_api(image_bytes, "", "caption")
            else:
                # 지원되지 않는 모델인 경우 로컬 모델 폴백
                if _florence_model is not None:
                    logger.warning(f"Unsupported model {model}, falling back to BLIP")
                    caption_text = await call_local_vl_api(image_bytes, "", "caption")
                    model = "blip-base"
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

            processing_time = time.time() - start_time

            logger.info(f"Captioning completed: '{caption_text[:100]}...'")

            return AnalyzeResponse(
                status="success",
                mode="captioning",
                caption=caption_text,
                confidence=0.90,
                processing_time=processing_time,
                model_used=model
            )

    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
