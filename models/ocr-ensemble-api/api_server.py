"""
OCR Ensemble API Server
PPT 슬라이드 11 [HOW-2] 멀티 엔진 앙상블 가중 투표 시스템

eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%

각 OCR 엔진의 결과를 가중치 기반으로 병합하여 최종 결과 도출
"""
import os
import io
import logging
import time
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ENSEMBLE_API_PORT = int(os.getenv("ENSEMBLE_API_PORT", "5011"))

# OCR 엔진 URL 설정
EDOCR2_URL = os.getenv("EDOCR2_URL", "http://edocr2-v2-api:5002")
PADDLEOCR_URL = os.getenv("PADDLEOCR_URL", "http://paddleocr-api:5006")
TESSERACT_URL = os.getenv("TESSERACT_URL", "http://tesseract-api:5008")
TROCR_URL = os.getenv("TROCR_URL", "http://trocr-api:5009")

# 기본 가중치 (PPT 기준)
DEFAULT_WEIGHTS = {
    "edocr2": 0.40,
    "paddleocr": 0.35,
    "tesseract": 0.15,
    "trocr": 0.10
}

app = FastAPI(
    title="OCR Ensemble API",
    description="멀티 엔진 앙상블 OCR - 4개 OCR 엔진 가중 투표 시스템",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# Schemas
# =====================

class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: Optional[List[int]] = None
    source: str  # 어떤 OCR 엔진에서 왔는지


class EnsembleResult(BaseModel):
    text: str
    confidence: float
    bbox: Optional[List[int]] = None
    votes: Dict[str, float]  # 각 엔진별 투표 가중치
    sources: List[str]  # 이 결과를 반환한 엔진들


class EnsembleResponse(BaseModel):
    success: bool
    results: List[EnsembleResult]
    full_text: str
    engine_results: Dict[str, List[OCRResult]]  # 각 엔진별 원본 결과
    engine_status: Dict[str, str]  # 각 엔진 상태
    weights_used: Dict[str, float]
    processing_time_ms: float
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    engines: Dict[str, str]
    timestamp: str


# =====================
# OCR Engine Clients
# =====================

async def call_edocr2(client: httpx.AsyncClient, image_bytes: bytes) -> List[OCRResult]:
    """eDOCr2 OCR 호출"""
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"language": "eng", "visualize": "false"}

        response = await client.post(
            f"{EDOCR2_URL}/api/v2/ocr",
            files=files,
            data=data,
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            texts = result.get("texts") or result.get("text_results") or []
            return [
                OCRResult(
                    text=t.get("text", ""),
                    confidence=t.get("confidence", 0.8),
                    bbox=t.get("bbox"),
                    source="edocr2"
                )
                for t in texts if t.get("text")
            ]
    except Exception as e:
        logger.warning(f"eDOCr2 호출 실패: {e}")
    return []


async def call_paddleocr(client: httpx.AsyncClient, image_bytes: bytes) -> List[OCRResult]:
    """PaddleOCR 호출"""
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"lang": "en", "visualize": "false"}

        response = await client.post(
            f"{PADDLEOCR_URL}/api/v1/ocr",
            files=files,
            data=data,
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            texts = result.get("texts") or result.get("results") or []
            return [
                OCRResult(
                    text=t.get("text", ""),
                    confidence=t.get("confidence", 0.8),
                    bbox=t.get("bbox"),
                    source="paddleocr"
                )
                for t in texts if t.get("text")
            ]
    except Exception as e:
        logger.warning(f"PaddleOCR 호출 실패: {e}")
    return []


async def call_tesseract(client: httpx.AsyncClient, image_bytes: bytes) -> List[OCRResult]:
    """Tesseract OCR 호출"""
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"lang": "eng", "output_type": "data"}

        response = await client.post(
            f"{TESSERACT_URL}/api/v1/ocr",
            files=files,
            data=data,
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            texts = result.get("texts", [])
            return [
                OCRResult(
                    text=t.get("text", ""),
                    confidence=t.get("confidence", 0.7),
                    bbox=t.get("bbox"),
                    source="tesseract"
                )
                for t in texts if t.get("text")
            ]
    except Exception as e:
        logger.warning(f"Tesseract 호출 실패: {e}")
    return []


async def call_trocr(client: httpx.AsyncClient, image_bytes: bytes) -> List[OCRResult]:
    """TrOCR 호출"""
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}

        response = await client.post(
            f"{TROCR_URL}/api/v1/ocr",
            files=files,
            timeout=60.0  # TrOCR은 더 느림
        )

        if response.status_code == 200:
            result = response.json()
            texts = result.get("texts", [])
            return [
                OCRResult(
                    text=t.get("text", ""),
                    confidence=t.get("confidence", 0.85),
                    bbox=t.get("bbox"),
                    source="trocr"
                )
                for t in texts if t.get("text")
            ]
    except Exception as e:
        logger.warning(f"TrOCR 호출 실패: {e}")
    return []


async def check_engine_health(client: httpx.AsyncClient, url: str, name: str) -> str:
    """OCR 엔진 헬스체크"""
    try:
        # eDOCr2는 /api/v1/health 사용, 나머지는 /health
        health_path = "/api/v1/health" if "edocr2" in name.lower() or "edocr2" in url else "/health"
        response = await client.get(f"{url}{health_path}", timeout=5.0)
        if response.status_code == 200:
            return "healthy"
        return f"unhealthy ({response.status_code})"
    except Exception as e:
        return f"unreachable ({str(e)[:30]})"


# =====================
# Ensemble Logic
# =====================

def normalize_text(text: str) -> str:
    """텍스트 정규화 (비교용)"""
    import re
    # 소문자 변환, 공백 정규화, 특수문자 유지 (치수에 중요)
    text = text.strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text


def calculate_text_similarity(text1: str, text2: str) -> float:
    """두 텍스트의 유사도 계산"""
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)

    if t1 == t2:
        return 1.0

    # Jaccard 유사도 (문자 단위)
    set1 = set(t1)
    set2 = set(t2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union


def merge_results(
    engine_results: Dict[str, List[OCRResult]],
    weights: Dict[str, float],
    similarity_threshold: float = 0.7
) -> List[EnsembleResult]:
    """
    가중 투표 기반 결과 병합

    1. 모든 결과를 모음
    2. 유사한 텍스트끼리 그룹화
    3. 각 그룹에서 가중치 기반 투표로 최종 텍스트 선택
    4. 신뢰도 계산
    """
    # 모든 결과 수집
    all_results = []
    for engine, results in engine_results.items():
        for r in results:
            all_results.append({
                "text": r.text,
                "confidence": r.confidence,
                "bbox": r.bbox,
                "source": engine,
                "weight": weights.get(engine, 0.1)
            })

    if not all_results:
        return []

    # 유사 텍스트 그룹화
    groups = []
    used = set()

    for i, result in enumerate(all_results):
        if i in used:
            continue

        group = [result]
        used.add(i)

        for j, other in enumerate(all_results):
            if j in used:
                continue

            similarity = calculate_text_similarity(result["text"], other["text"])
            if similarity >= similarity_threshold:
                group.append(other)
                used.add(j)

        groups.append(group)

    # 각 그룹에서 최종 결과 선택
    ensemble_results = []

    for group in groups:
        # 가중 투표
        text_votes = defaultdict(float)
        text_sources = defaultdict(list)

        for item in group:
            normalized = normalize_text(item["text"])
            vote = item["weight"] * item["confidence"]
            text_votes[normalized] += vote
            text_sources[normalized].append(item["source"])

        # 가장 높은 투표를 받은 텍스트 선택
        if not text_votes:
            continue

        best_text = max(text_votes.keys(), key=lambda t: text_votes[t])

        # 원본 텍스트 찾기 (대소문자 유지)
        original_text = best_text
        for item in group:
            if normalize_text(item["text"]) == best_text:
                original_text = item["text"]
                break

        # 신뢰도 계산 (가중 평균)
        total_weight = sum(item["weight"] for item in group)
        if total_weight > 0:
            weighted_confidence = sum(
                item["confidence"] * item["weight"]
                for item in group
            ) / total_weight
        else:
            weighted_confidence = 0.5

        # 동의율 보너스 (여러 엔진이 동의할수록 신뢰도 증가)
        unique_sources = set(text_sources[best_text])
        agreement_bonus = min(len(unique_sources) * 0.05, 0.2)  # 최대 0.2 보너스

        final_confidence = min(weighted_confidence + agreement_bonus, 1.0)

        # Bbox 선택 (가장 신뢰도 높은 것)
        best_bbox = None
        for item in group:
            if item["bbox"] and normalize_text(item["text"]) == best_text:
                best_bbox = item["bbox"]
                break

        # 투표 정보
        votes = {}
        for item in group:
            engine = item["source"]
            votes[engine] = votes.get(engine, 0) + item["weight"] * item["confidence"]

        ensemble_results.append(EnsembleResult(
            text=original_text,
            confidence=final_confidence,
            bbox=best_bbox,
            votes=votes,
            sources=list(unique_sources)
        ))

    # 신뢰도 순으로 정렬
    ensemble_results.sort(key=lambda x: x.confidence, reverse=True)

    return ensemble_results


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    async with httpx.AsyncClient() as client:
        engines = {
            "edocr2": await check_engine_health(client, EDOCR2_URL, "eDOCr2"),
            "paddleocr": await check_engine_health(client, PADDLEOCR_URL, "PaddleOCR"),
            "tesseract": await check_engine_health(client, TESSERACT_URL, "Tesseract"),
            "trocr": await check_engine_health(client, TROCR_URL, "TrOCR")
        }

    healthy_count = sum(1 for s in engines.values() if s == "healthy")
    status = "healthy" if healthy_count >= 2 else "degraded" if healthy_count >= 1 else "unhealthy"

    return HealthResponse(
        status=status,
        service="OCR Ensemble API",
        version="1.0.0",
        engines=engines,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "name": "OCR Ensemble",
        "type": "ocr_ensemble",
        "category": "ocr",
        "description": "4개 OCR 엔진 가중 투표 앙상블 (eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%)",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "edocr2_weight",
                "type": "number",
                "default": 0.40,
                "min": 0,
                "max": 1,
                "step": 0.05,
                "description": "eDOCr2 가중치"
            },
            {
                "name": "paddleocr_weight",
                "type": "number",
                "default": 0.35,
                "min": 0,
                "max": 1,
                "step": 0.05,
                "description": "PaddleOCR 가중치"
            },
            {
                "name": "tesseract_weight",
                "type": "number",
                "default": 0.15,
                "min": 0,
                "max": 1,
                "step": 0.05,
                "description": "Tesseract 가중치"
            },
            {
                "name": "trocr_weight",
                "type": "number",
                "default": 0.10,
                "min": 0,
                "max": 1,
                "step": 0.05,
                "description": "TrOCR 가중치"
            },
            {
                "name": "similarity_threshold",
                "type": "number",
                "default": 0.7,
                "min": 0.5,
                "max": 1,
                "step": 0.05,
                "description": "텍스트 유사도 임계값 (그룹화 기준)"
            },
            {
                "name": "engines",
                "type": "string",
                "default": "all",
                "description": "사용할 엔진 (콤마 구분: edocr2,paddleocr,tesseract,trocr)"
            }
        ],
        "inputs": [
            {"name": "image", "type": "Image", "description": "입력 이미지"}
        ],
        "outputs": [
            {"name": "results", "type": "EnsembleResult[]", "description": "앙상블 결과"},
            {"name": "full_text", "type": "string", "description": "전체 텍스트"}
        ],
        "default_weights": DEFAULT_WEIGHTS
    }


@app.post("/api/v1/ocr", response_model=EnsembleResponse)
async def ensemble_ocr(
    file: UploadFile = File(...),
    edocr2_weight: float = Form(default=0.40),
    paddleocr_weight: float = Form(default=0.35),
    tesseract_weight: float = Form(default=0.15),
    trocr_weight: float = Form(default=0.10),
    similarity_threshold: float = Form(default=0.7),
    engines: str = Form(default="all")
):
    """
    앙상블 OCR 수행

    Args:
        file: 이미지 파일
        edocr2_weight: eDOCr2 가중치 (기본 0.40)
        paddleocr_weight: PaddleOCR 가중치 (기본 0.35)
        tesseract_weight: Tesseract 가중치 (기본 0.15)
        trocr_weight: TrOCR 가중치 (기본 0.10)
        similarity_threshold: 텍스트 유사도 임계값
        engines: 사용할 엔진 (콤마 구분 또는 'all')
    """
    start_time = time.time()

    # 가중치 설정
    weights = {
        "edocr2": edocr2_weight,
        "paddleocr": paddleocr_weight,
        "tesseract": tesseract_weight,
        "trocr": trocr_weight
    }

    # 사용할 엔진 결정
    if engines.lower() == "all":
        active_engines = list(weights.keys())
    else:
        active_engines = [e.strip().lower() for e in engines.split(",")]

    # 이미지 로드
    image_bytes = await file.read()

    # 병렬로 모든 OCR 엔진 호출
    engine_results = {}
    engine_status = {}

    async with httpx.AsyncClient() as client:
        tasks = []

        if "edocr2" in active_engines:
            tasks.append(("edocr2", call_edocr2(client, image_bytes)))
        if "paddleocr" in active_engines:
            tasks.append(("paddleocr", call_paddleocr(client, image_bytes)))
        if "tesseract" in active_engines:
            tasks.append(("tesseract", call_tesseract(client, image_bytes)))
        if "trocr" in active_engines:
            tasks.append(("trocr", call_trocr(client, image_bytes)))

        # 병렬 실행
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        for i, (engine_name, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, Exception):
                engine_results[engine_name] = []
                engine_status[engine_name] = f"error: {str(result)[:50]}"
            else:
                engine_results[engine_name] = result
                engine_status[engine_name] = f"ok ({len(result)} texts)"

    # 앙상블 결과 병합
    ensemble_results = merge_results(engine_results, weights, similarity_threshold)

    # 전체 텍스트 구성
    full_text = " ".join([r.text for r in ensemble_results])

    processing_time = (time.time() - start_time) * 1000

    logger.info(
        f"앙상블 OCR 완료: {len(ensemble_results)}개 결과, "
        f"엔진 상태: {engine_status}, {processing_time:.1f}ms"
    )

    return EnsembleResponse(
        success=True,
        results=ensemble_results,
        full_text=full_text,
        engine_results={
            k: [OCRResult(**r.dict()) for r in v]
            for k, v in engine_results.items()
        },
        engine_status=engine_status,
        weights_used=weights,
        processing_time_ms=processing_time
    )


@app.post("/api/v1/ocr/compare")
async def compare_engines(
    file: UploadFile = File(...)
):
    """
    모든 OCR 엔진 결과 비교 (앙상블 없이)
    디버깅 및 성능 비교용
    """
    start_time = time.time()
    image_bytes = await file.read()

    results = {}

    async with httpx.AsyncClient() as client:
        # 순차 실행 (타이밍 측정용)
        for engine_name, call_func in [
            ("edocr2", call_edocr2),
            ("paddleocr", call_paddleocr),
            ("tesseract", call_tesseract),
            ("trocr", call_trocr)
        ]:
            engine_start = time.time()
            try:
                texts = await call_func(client, image_bytes)
                results[engine_name] = {
                    "texts": [t.dict() for t in texts],
                    "count": len(texts),
                    "time_ms": (time.time() - engine_start) * 1000,
                    "status": "ok"
                }
            except Exception as e:
                results[engine_name] = {
                    "texts": [],
                    "count": 0,
                    "time_ms": (time.time() - engine_start) * 1000,
                    "status": f"error: {str(e)}"
                }

    total_time = (time.time() - start_time) * 1000

    return {
        "engines": results,
        "total_time_ms": total_time
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting OCR Ensemble API on port {ENSEMBLE_API_PORT}")
    logger.info(f"Default weights: {DEFAULT_WEIGHTS}")
    logger.info(f"Engine URLs:")
    logger.info(f"  - eDOCr2: {EDOCR2_URL}")
    logger.info(f"  - PaddleOCR: {PADDLEOCR_URL}")
    logger.info(f"  - Tesseract: {TESSERACT_URL}")
    logger.info(f"  - TrOCR: {TROCR_URL}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ENSEMBLE_API_PORT,
        log_level="info"
    )
