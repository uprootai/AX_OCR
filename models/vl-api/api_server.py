"""
Vision Language Model API Server
Multimodal LLM 기반 도면 분석 마이크로서비스

포트: 5004
기능: Information Block 추출, 치수 추출, 제조 공정 추론, QC Checklist 생성
"""

import os
import sys
import json
import time
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import io

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from PIL import Image
import httpx
import torch
from transformers import AutoProcessor, AutoModelForCausalLM, Blip2Processor, Blip2ForConditionalGeneration

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Vision Language Model API",
    description="Multimodal LLM Service for Engineering Drawing Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

UPLOAD_DIR = Path("/tmp/vl-api/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# API 키 상태 (startup 시 검증됨)
_api_keys_validated = False
_available_models = []

# Florence-2 로컬 모델 (API 키 없을 때 폴백)
_florence_model = None
_florence_processor = None
_florence_device = None
FLORENCE_MODEL_ID = "microsoft/Florence-2-base"


# =====================
# Pydantic Models
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    available_models: List[str]


class InfoBlockRequest(BaseModel):
    query_fields: List[str] = Field(
        default=["name", "part number", "material", "scale", "weight"],
        description="추출할 정보 필드 목록"
    )
    model: str = Field(default="claude-3-5-sonnet-20241022", description="사용할 VL 모델")


class InfoBlockResponse(BaseModel):
    status: str
    data: Dict[str, str]
    processing_time: float
    model_used: str


class DimensionExtractionRequest(BaseModel):
    model: str = Field(default="claude-3-5-sonnet-20241022", description="사용할 VL 모델")


class DimensionExtractionResponse(BaseModel):
    status: str
    data: List[str]
    processing_time: float
    model_used: str


class ManufacturingProcessRequest(BaseModel):
    model: str = Field(default="gpt-4o", description="사용할 VL 모델")


class ManufacturingProcessResponse(BaseModel):
    status: str
    data: Dict[str, str]
    processing_time: float
    model_used: str


class QCChecklistRequest(BaseModel):
    model: str = Field(default="gpt-4o", description="사용할 VL 모델")


class QCChecklistResponse(BaseModel):
    status: str
    data: List[str]
    processing_time: float
    model_used: str


class AnalyzeRequest(BaseModel):
    """범용 VQA (Visual Question Answering) 요청"""
    model: str = Field(default="claude-3-5-sonnet-20241022", description="사용할 VL 모델")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="생성 temperature")


class AnalyzeResponse(BaseModel):
    """범용 VQA 응답"""
    status: str
    mode: str = Field(description="분석 모드: 'vqa' (질문-답변) 또는 'captioning' (일반 설명)")
    answer: Optional[str] = Field(None, description="질문에 대한 답변 (VQA 모드)")
    caption: Optional[str] = Field(None, description="이미지 설명 (캡셔닝 모드)")
    question: Optional[str] = Field(None, description="사용자 질문 (VQA 모드)")
    confidence: float = Field(default=1.0, description="답변 신뢰도")
    processing_time: float
    model_used: str


# =====================
# Helper Functions
# =====================

def encode_image_to_base64(image_bytes: bytes) -> str:
    """이미지를 base64로 인코딩"""
    return base64.b64encode(image_bytes).decode('utf-8')


async def call_claude_api(
    image_bytes: bytes,
    prompt: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 4096,
    temperature: float = 0.0
) -> str:
    """
    Claude API 호출

    Args:
        image_bytes: 이미지 바이트 데이터
        prompt: 프롬프트
        model: 모델명
        max_tokens: 최대 토큰 수
        temperature: 생성 다양성 (0-1, 0=결정적, 1=창의적)

    Returns:
        모델 응답 텍스트
    """
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    try:
        # 이미지를 base64로 인코딩
        base64_image = encode_image_to_base64(image_bytes)

        # 이미지 형식 감지
        img = Image.open(io.BytesIO(image_bytes))
        image_format = img.format.lower() if img.format else "png"
        if image_format == "jpg":
            image_format = "jpeg"

        # Claude API 요청
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": f"image/{image_format}",
                                        "data": base64_image
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
            )

            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Claude API error: {response.text}"
                )

            result = response.json()
            text = result["content"][0]["text"]

            logger.info(f"Claude API response: {len(text)} characters")
            return text

    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")


async def call_openai_gpt4v_api(
    image_bytes: bytes,
    prompt: str,
    model: str = "gpt-4o",
    max_tokens: int = 4096,
    temperature: float = 0.0
) -> str:
    """
    OpenAI GPT-4V API 호출

    Args:
        image_bytes: 이미지 바이트 데이터
        prompt: 프롬프트
        model: 모델명
        max_tokens: 최대 토큰 수
        temperature: 생성 다양성 (0-1, 0=결정적, 1=창의적)

    Returns:
        모델 응답 텍스트
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    try:
        # 이미지를 base64로 인코딩
        base64_image = encode_image_to_base64(image_bytes)

        # 이미지 형식 감지
        img = Image.open(io.BytesIO(image_bytes))
        image_format = img.format.lower() if img.format else "png"
        if image_format == "jpg":
            image_format = "jpeg"

        # OpenAI API 요청
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{image_format};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )

            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI API error: {response.text}"
                )

            result = response.json()
            text = result["choices"][0]["message"]["content"]

            logger.info(f"OpenAI API response: {len(text)} characters")
            return text

    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")


async def call_local_vl_api(
    image_bytes: bytes,
    prompt: str = "",
    mode: str = "caption"
) -> str:
    """
    로컬 VL 모델 호출 (BLIP)

    Args:
        image_bytes: 이미지 바이트 데이터
        prompt: 프롬프트 (선택사항, BLIP는 conditional generation 지원)
        mode: 'caption' (기본) 또는 'vqa'

    Returns:
        모델 응답 텍스트
    """
    global _florence_model, _florence_processor, _florence_device

    if _florence_model is None:
        raise HTTPException(status_code=500, detail="Local VL model not loaded")

    try:
        # 이미지 로드
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # BLIP은 conditional captioning 지원
        if prompt and prompt.strip():
            # 프롬프트가 있으면 conditional generation
            inputs = _florence_processor(
                images=img,
                text=prompt,
                return_tensors="pt"
            ).to(_florence_device)
        else:
            # 프롬프트 없으면 unconditional captioning
            inputs = _florence_processor(
                images=img,
                return_tensors="pt"
            ).to(_florence_device)

        # 추론
        with torch.no_grad():
            generated_ids = _florence_model.generate(
                **inputs,
                max_new_tokens=100,
                num_beams=3
            )

        # 디코딩
        generated_text = _florence_processor.decode(
            generated_ids[0], skip_special_tokens=True
        )

        return generated_text.strip()

    except Exception as e:
        logger.error(f"Local VL inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Local VL error: {str(e)}")


def parse_json_from_text(text: str) -> Union[Dict, List]:
    """
    텍스트에서 JSON 추출 및 파싱

    모델이 ```json ... ``` 형태로 감싼 경우 처리
    """
    try:
        # 코드 블록 제거
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # JSON 파싱
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed, attempting to extract: {e}")
        # 단순히 중괄호 또는 대괄호로 시작하는 부분 찾기
        import re
        json_pattern = r'(\{.*\}|\[.*\])'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass

        # 실패 시 원본 텍스트 반환
        logger.error(f"Could not parse JSON from text: {text[:200]}")
        raise ValueError(f"Failed to parse JSON: {text[:200]}")


# =====================
# Startup/Shutdown Events
# =====================

@app.on_event("startup")
async def startup_event():
    """Validate API keys and load Florence-2 on startup"""
    global _api_keys_validated, _available_models, _florence_model, _florence_processor, _florence_device

    logger.info("🚀 Starting VL API...")
    logger.info("🔑 Validating API keys...")

    missing_keys = []
    available_models = []

    # Check Anthropic API key
    if ANTHROPIC_API_KEY:
        logger.info("  ✅ ANTHROPIC_API_KEY is set")
        available_models.extend([
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307"
        ])
    else:
        logger.warning("  ⚠️  ANTHROPIC_API_KEY is NOT set")
        missing_keys.append("ANTHROPIC_API_KEY")

    # Check OpenAI API key
    if OPENAI_API_KEY:
        logger.info("  ✅ OPENAI_API_KEY is set")
        available_models.extend([
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4"
        ])
    else:
        logger.warning("  ⚠️  OPENAI_API_KEY is NOT set")
        missing_keys.append("OPENAI_API_KEY")

    # Load local VL model as fallback (always available)
    logger.info("🔄 Loading local VL model...")
    try:
        _florence_device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"  Using device: {_florence_device}")

        # Try BLIP-2 (smaller model with better compatibility)
        BLIP_MODEL_ID = "Salesforce/blip-image-captioning-base"
        from transformers import BlipProcessor, BlipForConditionalGeneration

        _florence_processor = BlipProcessor.from_pretrained(BLIP_MODEL_ID)
        _florence_model = BlipForConditionalGeneration.from_pretrained(
            BLIP_MODEL_ID,
            torch_dtype=torch.float16 if _florence_device == "cuda" else torch.float32
        ).to(_florence_device)

        _florence_model.eval()
        available_models.append("blip-base")
        logger.info("  ✅ BLIP model loaded successfully")
    except Exception as e:
        logger.error(f"  ❌ Failed to load local model: {e}")
        logger.warning("  Local model will not be available")

    # Update global state
    _available_models = available_models
    _api_keys_validated = True

    # Log summary
    if missing_keys and not _florence_model:
        logger.error("❌ No API keys and Florence-2 failed to load! VL API will not work.")
        logger.error("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variables")
    elif missing_keys:
        logger.warning(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
        logger.info(f"✅ Florence-2 available as fallback")
    else:
        logger.info(f"✅ All API keys validated. Available models: {len(available_models)}")

    logger.info(f"✅ VL API ready. Available models: {available_models}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down VL API...")


# =====================
# API Endpoints
# =====================

@app.get("/api/v1/info")
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
            {
                "name": "image",
                "type": "file",
                "description": "분석할 도면 이미지",
                "required": True
            },
            {
                "name": "prompt",
                "type": "string",
                "description": "질문 또는 분석 요청 (선택사항). 예: '이 도면의 치수를 추출해주세요'",
                "required": False
            }
        ],

        # 출력 정의
        "outputs": [
            {
                "name": "mode",
                "type": "string",
                "description": "분석 모드 ('vqa' 또는 'captioning')"
            },
            {
                "name": "answer",
                "type": "string",
                "description": "질문에 대한 답변 (VQA 모드)"
            },
            {
                "name": "caption",
                "type": "string",
                "description": "이미지 설명 (캡셔닝 모드)"
            },
            {
                "name": "confidence",
                "type": "number",
                "description": "답변 신뢰도 (0-1)"
            }
        ],

        # 파라미터 정의
        "parameters": [
            {
                "name": "model",
                "type": "select",
                "options": ["blip-base", "claude-3-5-sonnet-20241022", "gpt-4o", "gpt-4-turbo"],
                "default": "blip-base",
                "description": "사용할 VL 모델 (blip-base는 로컬 모델)"
            },
            {
                "name": "temperature",
                "type": "number",
                "default": 0.0,
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
                "description": "생성 temperature (0=결정적, 1=창의적)"
            }
        ],

        # 입력 필드 매핑
        "input_mappings": {
            "prompt": "inputs.text"  # TextInput의 text → VL API의 prompt
        },

        # BlueprintFlow UI 설정
        "blueprintflow": {
            "icon": "👁️",
            "color": "#ec4899",
            "category": "api"
        },

        # 출력 필드 매핑
        "output_mappings": {
            "mode": "mode",
            "answer": "answer",
            "caption": "caption",
            "confidence": "confidence"
        }
    }


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint / 헬스체크

    Returns the current health status and available VL models.
    """
    global _available_models

    # Use cached available models from startup
    available_models = _available_models if _api_keys_validated else []

    # Fallback: check if keys exist (for backward compatibility)
    if not available_models:
        if ANTHROPIC_API_KEY:
            available_models.extend([
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ])
        if OPENAI_API_KEY:
            available_models.extend([
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4-vision-preview"
            ])

    return HealthResponse(
        status="healthy",
        service="vl-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        available_models=available_models
    )


@app.post("/api/v1/extract_info_block", response_model=InfoBlockResponse)
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


@app.post("/api/v1/extract_dimensions", response_model=DimensionExtractionResponse)
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


@app.post("/api/v1/infer_manufacturing_process", response_model=ManufacturingProcessResponse)
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
{{
    "Turning": "Used for creating the cylindrical shape of the part, including the outer diameters and chamfers",
    "Drilling/Boring": "To achieve the internal diameter and the countersink specified",
    "Milling": "For creating the flat surfaces if needed",
    "Reaming": "To ensure the internal diameter precision",
    "Grinding": "To achieve the surface finish required on precise diameters",
    "Deburring": "To break all sharp edges and remove burrs as specified"
}}"""

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


@app.post("/api/v1/generate_qc_checklist", response_model=QCChecklistResponse)
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


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
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


# =====================
# Main
# =====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=5004,
        reload=True,
        log_level="info"
    )
