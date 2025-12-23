# Blueprint AI BOM v2 구현 가이드

> 작성일: 2025-12-19 | 문서 유형: 개발 가이드 | 대상: 개발팀

---

## 목차

1. [사전 준비](#1-사전-준비)
2. [Phase 1: 치수 OCR 통합](#2-phase-1-치수-ocr-통합-2주)
3. [Phase 2: 치수선 기반 관계 추출](#3-phase-2-치수선-기반-관계-추출-1주)
4. [Phase 3: Active Learning 통합](#4-phase-3-active-learning-통합-1주)
5. [Phase 4: VLM 초기 분류](#5-phase-4-vlm-초기-분류-1주)
6. [Phase 5: 영역 분할](#6-phase-5-영역-분할-1주)
7. [Phase 6: P&ID 통합](#7-phase-6-pid-통합-2주)
8. [Phase 7: GD&T 파서](#8-phase-7-gdt-파서-2주)
9. [테스트 전략](#9-테스트-전략)
10. [배포 체크리스트](#10-배포-체크리스트)

---

## 1. 사전 준비

### 1.1 기존 시스템 구조 이해

```
blueprint-ai-bom/
├── backend/
│   ├── api_server.py           # FastAPI 앱 진입점 (포트 5020)
│   ├── routers/
│   │   ├── session_router.py   # 세션 관리 (prefix: /session)
│   │   ├── detection_router.py # 검출 결과 관리 (prefix: /detection) ⭐ 확장 대상
│   │   └── bom_router.py       # BOM 생성 (prefix: /bom)
│   ├── schemas/
│   │   ├── session.py          # SessionStatus enum 포함
│   │   ├── detection.py        # Detection, VerificationStatus 정의 ⭐ 재사용
│   │   └── bom.py
│   ├── services/
│   │   ├── detection_service.py  # YOLO API 호출 (yolo-api:5005)
│   │   ├── session_service.py    # 세션 상태 관리
│   │   └── bom_service.py
│   └── test_drawings/            # 테스트 이미지 및 GT 라벨
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── WorkflowPage.tsx  # 메인 워크플로우 ⭐ 확장 대상
│   │   ├── components/
│   │   └── stores/
│   │       └── sessionStore.ts   # Zustand 스토어
│   └── package.json
└── docker-compose.yml
```

**핵심 패턴 (기존 코드와 일관성 유지):**
```python
# 1. 서비스 주입 패턴 (detection_router.py 참조)
_dimension_service = None
_session_service = None

def set_dimension_service(dimension_service, session_service):
    global _dimension_service, _session_service
    _dimension_service = dimension_service
    _session_service = session_service

# 2. 라우터 prefix 패턴 (api/v1 없이 직접 사용)
router = APIRouter(prefix="/dimension", tags=["dimension"])

# 3. VerificationStatus 재사용 (detection.py에서 import)
from schemas.detection import VerificationStatus
```

### 1.2 개발 환경 설정

```bash
# 1. 저장소 클론 (이미 완료된 경우 스킵)
cd /home/uproot/ax/poc

# 2. 백엔드 의존성
cd blueprint-ai-bom/backend
pip install -r requirements.txt

# 3. 프론트엔드 의존성
cd ../frontend
npm install

# 4. 개발 서버 실행
# 터미널 1: 백엔드 (포트 5020)
cd backend && uvicorn api_server:app --reload --port 5020

# 터미널 2: 프론트엔드 (포트 3000)
cd frontend && npm run dev
```

### 1.3 필요 API 서비스 확인

| 서비스 | 포트 | 상태 확인 |
|--------|------|----------|
| eDOCr2 | 5002 | `curl http://localhost:5002/api/v1/health` |
| YOLO | 5005 | `curl http://localhost:5005/api/v1/health` |
| Line Detector | 5016 | `curl http://localhost:5016/api/v1/health` |
| PaddleOCR | 5006 | `curl http://localhost:5006/api/v1/health` |

### 1.4 테스트 이미지 준비

```bash
# 테스트용 이미지 위치 확인
ls -la /home/uproot/ax/poc/test-images/
# sample2_interm_shaft.jpg  <- Phase 1 테스트용
# sample_pid.png            <- Phase 6 테스트용
```

---

## 2. Phase 1: 치수 OCR 통합 (2주)

### 2.1 개요

**목표:** 기존 심볼 검출에 치수 OCR 기능 추가

**산출물:**
- 분석 옵션 선택 UI
- eDOCr2 연동 서비스
- 치수 검증 UI
- 치수 테이블 출력

### 2.2 Step 1: 데이터 모델 정의 (Day 1)

#### 2.2.1 파일 생성: `backend/schemas/dimension.py`

```python
"""치수 관련 스키마 정의

Note: VerificationStatus는 detection.py에서 이미 정의되어 있으므로 재사용합니다.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

# 기존 detection.py의 VerificationStatus 재사용
from schemas.detection import VerificationStatus, BoundingBox


class DimensionType(str, Enum):
    """치수 유형"""
    LENGTH = "length"
    DIAMETER = "diameter"
    RADIUS = "radius"
    ANGLE = "angle"
    TOLERANCE = "tolerance"
    SURFACE_FINISH = "surface_finish"
    UNKNOWN = "unknown"


class Dimension(BaseModel):
    """치수 데이터 모델

    기존 Detection 스키마와 일관된 패턴을 따릅니다.
    """
    id: str = Field(..., description="고유 ID (예: dim_001)")
    bbox: BoundingBox = Field(..., description="바운딩박스 (기존 BoundingBox 재사용)")
    value: str = Field(..., description="치수 값 (예: Ø50, 100mm)")
    raw_text: str = Field(..., description="OCR 원본 텍스트")
    unit: Optional[str] = Field(None, description="단위 (mm, inch 등)")
    tolerance: Optional[str] = Field(None, description="공차 (H7, ±0.1 등)")
    dimension_type: DimensionType = Field(
        DimensionType.UNKNOWN,
        description="치수 유형"
    )
    confidence: float = Field(..., ge=0, le=1, description="OCR 신뢰도")

    # 기존 detection.py의 VerificationStatus 재사용
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="검증 상태"
    )
    modified_value: Optional[str] = Field(None, description="수정된 치수 값")
    linked_to: Optional[str] = Field(None, description="연결된 객체 ID")

    class Config:
        use_enum_values = True


class DimensionCreate(BaseModel):
    """치수 생성 요청"""
    bbox: List[float]
    value: str
    raw_text: str
    confidence: float
    dimension_type: Optional[DimensionType] = DimensionType.UNKNOWN


class DimensionUpdate(BaseModel):
    """치수 수정 요청"""
    value: Optional[str] = None
    tolerance: Optional[str] = None
    dimension_type: Optional[DimensionType] = None
    status: Optional[VerificationStatus] = None
    linked_to: Optional[str] = None


class DimensionListResponse(BaseModel):
    """치수 목록 응답"""
    dimensions: List[Dimension]
    total: int
    stats: dict  # 상태별 카운트
```

#### 2.2.2 파일 생성: `backend/schemas/analysis_options.py`

```python
"""분석 옵션 스키마"""
from typing import Optional, List
from pydantic import BaseModel, Field


class AnalysisOptions(BaseModel):
    """분석 옵션 설정"""
    enable_symbol_detection: bool = Field(True, description="심볼 검출 활성화")
    enable_dimension_ocr: bool = Field(False, description="치수 OCR 활성화")
    enable_line_detection: bool = Field(False, description="선 검출 활성화")
    enable_text_extraction: bool = Field(False, description="텍스트 블록 추출 활성화")

    # OCR 엔진 선택
    ocr_engine: str = Field("edocr2", description="OCR 엔진 (edocr2, paddleocr, ensemble)")

    # 검출 설정
    confidence_threshold: float = Field(0.5, ge=0, le=1)

    # 프리셋 (선택 시 자동 설정)
    preset: Optional[str] = Field(None, description="프리셋 (mechanical_part, pid, assembly)")


class AnalysisOptionsUpdate(BaseModel):
    """분석 옵션 업데이트"""
    enable_symbol_detection: Optional[bool] = None
    enable_dimension_ocr: Optional[bool] = None
    enable_line_detection: Optional[bool] = None
    enable_text_extraction: Optional[bool] = None
    ocr_engine: Optional[str] = None
    confidence_threshold: Optional[float] = None
    preset: Optional[str] = None


# 프리셋 정의
PRESETS = {
    "mechanical_part": {
        "enable_symbol_detection": False,
        "enable_dimension_ocr": True,
        "enable_line_detection": False,
        "enable_text_extraction": True,
        "ocr_engine": "edocr2",
        "confidence_threshold": 0.5
    },
    "pid": {
        "enable_symbol_detection": True,
        "enable_dimension_ocr": False,
        "enable_line_detection": True,
        "enable_text_extraction": True,
        "ocr_engine": "paddleocr",
        "confidence_threshold": 0.5
    },
    "assembly": {
        "enable_symbol_detection": True,
        "enable_dimension_ocr": True,
        "enable_line_detection": False,
        "enable_text_extraction": True,
        "ocr_engine": "paddleocr",
        "confidence_threshold": 0.5
    }
}
```

#### 2.2.3 스키마 통합: `backend/schemas/__init__.py` 수정

```python
# 기존 import에 추가
from .dimension import (
    Dimension,
    DimensionCreate,
    DimensionUpdate,
    DimensionListResponse,
    DimensionType,
    VerificationStatus
)
from .analysis_options import (
    AnalysisOptions,
    AnalysisOptionsUpdate,
    PRESETS
)
```

### 2.3 Step 2: eDOCr2 서비스 구현 (Day 2-4)

#### 2.3.1 파일 생성: `backend/services/dimension_service.py`

```python
"""치수 OCR 서비스 (eDOCr2 연동)

기존 DetectionService 패턴을 따름:
- httpx를 사용한 외부 API 호출
- 동기 방식 (기존 코드와 일관성 유지)
- 환경변수로 API URL 설정
"""
import os
import uuid
import re
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import httpx
import mimetypes

from schemas.dimension import Dimension, DimensionType
from schemas.detection import VerificationStatus, BoundingBox

logger = logging.getLogger(__name__)

# eDOCr2 API 주소 (Docker 네트워크 내부)
EDOCR2_API_URL = os.getenv("EDOCR2_API_URL", "http://edocr2-api:5002")


class DimensionService:
    """치수 OCR 서비스 (DetectionService 패턴 따름)"""

    def __init__(self, api_url: str = EDOCR2_API_URL):
        self.api_url = api_url
        print(f"✅ DimensionService 초기화 완료 (edocr2-api: {self.api_url})")

    async def health_check(self) -> bool:
        """헬스체크"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"eDOCr2 health check failed: {e}")
            return False

    async def extract_dimensions(
        self,
        image_path: str,
        confidence_threshold: float = 0.5
    ) -> List[Dimension]:
        """
        이미지에서 치수 추출

        Args:
            image_path: 이미지 파일 경로
            confidence_threshold: 최소 신뢰도

        Returns:
            추출된 치수 목록
        """
        try:
            # 이미지 파일 읽기
            with open(image_path, "rb") as f:
                files = {"file": (image_path.split("/")[-1], f, "image/jpeg")}
                data = {"confidence": confidence_threshold}

                response = await self.client.post(
                    f"{self.base_url}/api/v1/process",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                logger.error(f"eDOCr2 API error: {response.text}")
                return []

            result = response.json()
            return self._parse_response(result)

        except Exception as e:
            logger.error(f"Dimension extraction failed: {e}")
            return []

    def _parse_response(self, result: dict) -> List[Dimension]:
        """
        eDOCr2 응답 파싱

        Expected format:
        {
            "detections": [
                {"text": "Ø50", "bbox": [x1, y1, x2, y2], "confidence": 0.95},
                ...
            ]
        }
        """
        dimensions = []
        detections = result.get("detections", [])

        for idx, det in enumerate(detections):
            dim_id = f"dim_{idx:03d}"
            raw_text = det.get("text", "")
            bbox = det.get("bbox", [0, 0, 0, 0])
            confidence = det.get("confidence", 0.0)

            # 치수 유형 추론
            dim_type, parsed_value, tolerance = self._parse_dimension_text(raw_text)

            dimension = Dimension(
                id=dim_id,
                bbox=bbox,
                value=parsed_value,
                raw_text=raw_text,
                unit=self._extract_unit(raw_text),
                tolerance=tolerance,
                dimension_type=dim_type,
                confidence=confidence,
                status=VerificationStatus.PENDING,
                linked_to=None
            )
            dimensions.append(dimension)

        return dimensions

    def _parse_dimension_text(self, text: str) -> tuple:
        """
        치수 텍스트 파싱

        Returns:
            (DimensionType, parsed_value, tolerance)
        """
        text = text.strip()
        tolerance = None
        dim_type = DimensionType.UNKNOWN

        # 직경 패턴: Ø50, ⌀50, φ50
        if re.match(r'^[ØⓁ⌀φ]\s*\d+', text):
            dim_type = DimensionType.DIAMETER

        # 반경 패턴: R50, R 50
        elif re.match(r'^R\s*\d+', text, re.IGNORECASE):
            dim_type = DimensionType.RADIUS

        # 각도 패턴: 45°, 45deg
        elif re.search(r'\d+\s*[°˚]', text) or 'deg' in text.lower():
            dim_type = DimensionType.ANGLE

        # 표면 거칠기: Ra 1.6, Ra1.6
        elif re.match(r'^Ra\s*[\d.]+', text, re.IGNORECASE):
            dim_type = DimensionType.SURFACE_FINISH

        # 일반 길이: 100, 100mm, 50.5
        elif re.match(r'^\d+\.?\d*', text):
            dim_type = DimensionType.LENGTH

        # 공차 추출: H7, h6, ±0.1, +0.05/-0.02
        tolerance_patterns = [
            r'[HhGgFfEe]\d+',  # IT 공차
            r'[±]\s*\d+\.?\d*',  # 대칭 공차
            r'[+\-]\d+\.?\d*\s*/\s*[+\-]?\d+\.?\d*',  # 비대칭 공차
        ]
        for pattern in tolerance_patterns:
            match = re.search(pattern, text)
            if match:
                tolerance = match.group()
                break

        return dim_type, text, tolerance

    def _extract_unit(self, text: str) -> Optional[str]:
        """단위 추출"""
        if 'mm' in text.lower():
            return 'mm'
        elif 'cm' in text.lower():
            return 'cm'
        elif 'in' in text.lower() or '"' in text:
            return 'inch'
        elif '°' in text or 'deg' in text.lower():
            return 'degree'
        return None

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()


# 싱글톤 인스턴스
edocr2_service = EDOCr2Service()
```

#### 2.3.2 서비스 테스트: `backend/tests/test_edocr2_service.py`

```python
"""eDOCr2 서비스 테스트"""
import pytest
from services.edocr2_service import EDOCr2Service, edocr2_service


class TestEDOCr2Service:
    """eDOCr2 서비스 테스트"""

    def test_parse_diameter(self):
        """직경 파싱 테스트"""
        service = EDOCr2Service()
        dim_type, value, tolerance = service._parse_dimension_text("Ø50 H7")

        assert dim_type.value == "diameter"
        assert tolerance == "H7"

    def test_parse_length(self):
        """길이 파싱 테스트"""
        service = EDOCr2Service()
        dim_type, value, tolerance = service._parse_dimension_text("100mm ±0.1")

        assert dim_type.value == "length"
        assert tolerance == "±0.1"

    def test_parse_surface_finish(self):
        """표면 거칠기 파싱 테스트"""
        service = EDOCr2Service()
        dim_type, value, tolerance = service._parse_dimension_text("Ra 1.6")

        assert dim_type.value == "surface_finish"

    def test_extract_unit(self):
        """단위 추출 테스트"""
        service = EDOCr2Service()

        assert service._extract_unit("100mm") == "mm"
        assert service._extract_unit("45°") == "degree"
        assert service._extract_unit("2\"") == "inch"


# pytest 실행: pytest tests/test_edocr2_service.py -v
```

### 2.4 Step 3: 분석 옵션 API (Day 5-6)

#### 2.4.1 파일 생성: `backend/routers/analysis_router.py`

```python
"""분석 옵션 및 실행 API

기존 detection_router.py 패턴을 따름:
- 서비스 주입 패턴 사용
- prefix 패턴: /analysis (api/v1 없이)
- session_service 연동
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from schemas.analysis_options import (
    AnalysisOptions,
    AnalysisOptionsUpdate,
    PRESETS
)
from schemas.dimension import Dimension, DimensionListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis"])

# 서비스 주입을 위한 전역 변수 (detection_router.py 패턴 따름)
_dimension_service = None
_detection_service = None
_session_service = None


def set_analysis_services(dimension_service, detection_service, session_service):
    """서비스 인스턴스 설정"""
    global _dimension_service, _detection_service, _session_service
    _dimension_service = dimension_service
    _detection_service = detection_service
    _session_service = session_service


def get_dimension_service():
    if _dimension_service is None:
        raise HTTPException(status_code=500, detail="Dimension service not initialized")
    return _dimension_service


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


@router.get("/options/{session_id}")
async def get_analysis_options(session_id: str) -> AnalysisOptions:
    """세션의 분석 옵션 조회"""
    if session_id not in session_options:
        # 기본 옵션 반환
        return AnalysisOptions()
    return session_options[session_id]


@router.put("/options/{session_id}")
async def update_analysis_options(
    session_id: str,
    options: AnalysisOptionsUpdate
) -> AnalysisOptions:
    """세션의 분석 옵션 업데이트"""
    current = session_options.get(session_id, AnalysisOptions())

    # 프리셋 적용
    if options.preset and options.preset in PRESETS:
        preset_values = PRESETS[options.preset]
        for key, value in preset_values.items():
            setattr(current, key, value)
        current.preset = options.preset
    else:
        # 개별 옵션 업데이트
        update_data = options.dict(exclude_unset=True, exclude={'preset'})
        for key, value in update_data.items():
            if value is not None:
                setattr(current, key, value)

    session_options[session_id] = current
    return current


@router.post("/options/{session_id}/preset/{preset_name}")
async def apply_preset(session_id: str, preset_name: str) -> AnalysisOptions:
    """프리셋 적용"""
    if preset_name not in PRESETS:
        raise HTTPException(status_code=400, detail=f"Unknown preset: {preset_name}")

    preset_values = PRESETS[preset_name]
    options = AnalysisOptions(**preset_values, preset=preset_name)
    session_options[session_id] = options
    return options


@router.post("/run/{session_id}")
async def run_analysis(
    session_id: str,
    image_path: str
) -> dict:
    """
    분석 실행

    설정된 옵션에 따라 해당 분석 실행
    """
    options = session_options.get(session_id, AnalysisOptions())
    results = {
        "session_id": session_id,
        "options": options.dict(),
        "detections": [],
        "dimensions": [],
        "lines": [],
        "texts": []
    }

    # 심볼 검출
    if options.enable_symbol_detection:
        try:
            detections = await yolo_service.detect(
                image_path,
                confidence=options.confidence_threshold
            )
            results["detections"] = [d.dict() for d in detections]
        except Exception as e:
            logger.error(f"Symbol detection failed: {e}")

    # 치수 OCR
    if options.enable_dimension_ocr:
        try:
            dimensions = await edocr2_service.extract_dimensions(
                image_path,
                confidence_threshold=options.confidence_threshold
            )
            results["dimensions"] = [d.dict() for d in dimensions]
        except Exception as e:
            logger.error(f"Dimension OCR failed: {e}")

    # 선 검출 (Phase 6에서 구현)
    if options.enable_line_detection:
        # TODO: Line Detector 연동
        pass

    # 텍스트 추출 (Phase 4에서 구현)
    if options.enable_text_extraction:
        # TODO: 텍스트 블록 추출
        pass

    return results


@router.get("/presets")
async def list_presets() -> dict:
    """사용 가능한 프리셋 목록"""
    return {
        "presets": [
            {
                "name": name,
                "description": _get_preset_description(name),
                "options": options
            }
            for name, options in PRESETS.items()
        ]
    }


def _get_preset_description(name: str) -> str:
    """프리셋 설명"""
    descriptions = {
        "mechanical_part": "기계 부품도 - 치수, 공차, 표면 거칠기 분석",
        "pid": "P&ID 배관도 - 심볼, 연결선, 태그 분석",
        "assembly": "조립도 - 부품 심볼 + 치수 분석"
    }
    return descriptions.get(name, "")
```

#### 2.4.2 라우터 등록: `backend/api_server.py` 수정

```python
# ===== 기존 import 섹션에 추가 (api_server.py 상단) =====
from routers.analysis_router import router as analysis_router_api, set_analysis_services
from services.dimension_service import DimensionService

# ===== 서비스 인스턴스 생성 섹션에 추가 (약 line 63 부근) =====
dimension_service = DimensionService()

# ===== 라우터에 서비스 주입 섹션에 추가 (약 line 69 부근) =====
set_analysis_services(dimension_service, detection_service, session_service)

# ===== 라우터 등록 섹션에 추가 (약 line 74 부근) =====
app.include_router(analysis_router_api, tags=["Analysis"])
```

**참고: 기존 api_server.py 패턴**
```python
# 기존 코드 (참고용)
session_service = SessionService(UPLOAD_DIR, RESULTS_DIR)
detection_service = DetectionService(model_path=model_path)
bom_service = BOMService(output_dir=RESULTS_DIR)

set_session_service(session_service, UPLOAD_DIR)
set_detection_service(detection_service, session_service)
set_bom_service(bom_service, session_service)

app.include_router(session_router_api, tags=["Session"])
app.include_router(detection_router_api, tags=["Detection"])
app.include_router(bom_router_api, tags=["BOM"])
```

### 2.5 Step 4: 프론트엔드 - 분석 옵션 UI (Day 7-8)

#### 2.5.1 파일 생성: `frontend/src/components/AnalysisOptions.tsx`

```tsx
/**
 * 분석 옵션 선택 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { useWorkflowStore } from '../store/workflowStore';

interface AnalysisOptionsProps {
  sessionId: string;
  onOptionsChange?: (options: AnalysisOptions) => void;
}

interface AnalysisOptions {
  enable_symbol_detection: boolean;
  enable_dimension_ocr: boolean;
  enable_line_detection: boolean;
  enable_text_extraction: boolean;
  ocr_engine: string;
  confidence_threshold: number;
  preset: string | null;
}

const PRESETS = [
  { id: 'mechanical_part', name: '기계 부품도', icon: '⚙️' },
  { id: 'pid', name: 'P&ID 배관도', icon: '🔧' },
  { id: 'assembly', name: '조립도', icon: '🔩' },
  { id: 'custom', name: '커스텀', icon: '⚡' },
];

export const AnalysisOptions: React.FC<AnalysisOptionsProps> = ({
  sessionId,
  onOptionsChange
}) => {
  const [options, setOptions] = useState<AnalysisOptions>({
    enable_symbol_detection: true,
    enable_dimension_ocr: false,
    enable_line_detection: false,
    enable_text_extraction: false,
    ocr_engine: 'edocr2',
    confidence_threshold: 0.5,
    preset: null
  });

  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 옵션 로드 (API prefix: /analysis, not /api/v1/analysis)
  useEffect(() => {
    const loadOptions = async () => {
      try {
        const response = await fetch(`/analysis/options/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          setOptions(data);
          setSelectedPreset(data.preset);
        }
      } catch (error) {
        console.error('Failed to load options:', error);
      }
    };

    if (sessionId) {
      loadOptions();
    }
  }, [sessionId]);

  // 프리셋 적용
  const applyPreset = async (presetId: string) => {
    if (presetId === 'custom') {
      setSelectedPreset('custom');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `/analysis/options/${sessionId}/preset/${presetId}`,
        { method: 'POST' }
      );

      if (response.ok) {
        const data = await response.json();
        setOptions(data);
        setSelectedPreset(presetId);
        onOptionsChange?.(data);
      }
    } catch (error) {
      console.error('Failed to apply preset:', error);
    } finally {
      setLoading(false);
    }
  };

  // 개별 옵션 변경
  const updateOption = async (key: keyof AnalysisOptions, value: any) => {
    const newOptions = { ...options, [key]: value };
    setOptions(newOptions);
    setSelectedPreset('custom');

    try {
      await fetch(`/analysis/options/${sessionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value })
      });
      onOptionsChange?.(newOptions);
    } catch (error) {
      console.error('Failed to update option:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-4">
      <h3 className="text-lg font-semibold mb-3">📊 분석 옵션</h3>

      {/* 프리셋 선택 */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          빠른 선택
        </label>
        <div className="flex gap-2 flex-wrap">
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => applyPreset(preset.id)}
              disabled={loading}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors
                ${selectedPreset === preset.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
                ${loading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              {preset.icon} {preset.name}
            </button>
          ))}
        </div>
      </div>

      {/* 상세 옵션 */}
      <div className="space-y-3">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={options.enable_symbol_detection}
            onChange={(e) => updateOption('enable_symbol_detection', e.target.checked)}
            className="rounded text-blue-600"
          />
          <span className="text-sm">🎯 심볼 검출 (YOLO)</span>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={options.enable_dimension_ocr}
            onChange={(e) => updateOption('enable_dimension_ocr', e.target.checked)}
            className="rounded text-blue-600"
          />
          <span className="text-sm">📏 치수 OCR (eDOCr2)</span>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={options.enable_line_detection}
            onChange={(e) => updateOption('enable_line_detection', e.target.checked)}
            className="rounded text-blue-600"
          />
          <span className="text-sm">📐 선/연결 검출</span>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={options.enable_text_extraction}
            onChange={(e) => updateOption('enable_text_extraction', e.target.checked)}
            className="rounded text-blue-600"
          />
          <span className="text-sm">📝 텍스트 블록 추출</span>
        </label>
      </div>

      {/* 신뢰도 임계값 */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          신뢰도 임계값: {(options.confidence_threshold * 100).toFixed(0)}%
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={options.confidence_threshold * 100}
          onChange={(e) => updateOption('confidence_threshold', parseInt(e.target.value) / 100)}
          className="w-full"
        />
      </div>

      {/* 현재 설정 요약 */}
      <div className="mt-4 p-3 bg-gray-50 rounded text-sm text-gray-600">
        <strong>현재 설정:</strong>{' '}
        {[
          options.enable_symbol_detection && '심볼',
          options.enable_dimension_ocr && '치수',
          options.enable_line_detection && '선',
          options.enable_text_extraction && '텍스트'
        ].filter(Boolean).join(', ') || '없음'}
      </div>
    </div>
  );
};

export default AnalysisOptions;
```

### 2.6 Step 5: 프론트엔드 - 치수 검증 UI (Day 9-11)

#### 2.6.1 파일 생성: `frontend/src/components/DimensionList.tsx`

```tsx
/**
 * 치수 목록 및 검증 컴포넌트
 */
import React, { useState } from 'react';

interface Dimension {
  id: string;
  bbox: number[];
  value: string;
  raw_text: string;
  unit: string | null;
  tolerance: string | null;
  dimension_type: string;
  confidence: number;
  status: 'pending' | 'approved' | 'rejected' | 'modified';
  linked_to: string | null;
}

interface DimensionListProps {
  dimensions: Dimension[];
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onModify: (id: string, newValue: string) => void;
  onHover?: (id: string | null) => void;
}

const STATUS_ICONS = {
  pending: '❓',
  approved: '✅',
  rejected: '❌',
  modified: '✏️'
};

const TYPE_LABELS = {
  length: '길이',
  diameter: '직경',
  radius: '반경',
  angle: '각도',
  tolerance: '공차',
  surface_finish: '표면거칠기',
  unknown: '미분류'
};

export const DimensionList: React.FC<DimensionListProps> = ({
  dimensions,
  onApprove,
  onReject,
  onModify,
  onHover
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const handleStartEdit = (dim: Dimension) => {
    setEditingId(dim.id);
    setEditValue(dim.value);
  };

  const handleSaveEdit = (id: string) => {
    onModify(id, editValue);
    setEditingId(null);
    setEditValue('');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditValue('');
  };

  // 상태별 통계
  const stats = {
    total: dimensions.length,
    pending: dimensions.filter(d => d.status === 'pending').length,
    approved: dimensions.filter(d => d.status === 'approved').length,
    rejected: dimensions.filter(d => d.status === 'rejected').length,
    modified: dimensions.filter(d => d.status === 'modified').length,
  };

  // 신뢰도별 정렬 (낮은 순)
  const sortedDimensions = [...dimensions].sort((a, b) => a.confidence - b.confidence);

  return (
    <div className="bg-white rounded-lg shadow">
      {/* 헤더 */}
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold">📏 치수 목록</h3>
        <div className="flex gap-4 mt-2 text-sm text-gray-600">
          <span>전체: {stats.total}</span>
          <span>✅ {stats.approved}</span>
          <span>❌ {stats.rejected}</span>
          <span>✏️ {stats.modified}</span>
          <span>❓ {stats.pending}</span>
        </div>
      </div>

      {/* 목록 */}
      <div className="divide-y max-h-96 overflow-y-auto">
        {sortedDimensions.map((dim) => (
          <div
            key={dim.id}
            className={`p-3 hover:bg-gray-50 transition-colors
              ${dim.status === 'rejected' ? 'opacity-50' : ''}
            `}
            onMouseEnter={() => onHover?.(dim.id)}
            onMouseLeave={() => onHover?.(null)}
          >
            <div className="flex items-center justify-between">
              {/* 상태 아이콘 */}
              <span className="text-lg mr-2">
                {STATUS_ICONS[dim.status]}
              </span>

              {/* 치수 정보 */}
              <div className="flex-1">
                {editingId === dim.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="border rounded px-2 py-1 text-sm w-24"
                      autoFocus
                    />
                    <button
                      onClick={() => handleSaveEdit(dim.id)}
                      className="text-green-600 hover:text-green-800 text-sm"
                    >
                      저장
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="text-gray-600 hover:text-gray-800 text-sm"
                    >
                      취소
                    </button>
                  </div>
                ) : (
                  <div>
                    <span className="font-medium">{dim.value}</span>
                    {dim.tolerance && (
                      <span className="ml-2 text-blue-600 text-sm">
                        {dim.tolerance}
                      </span>
                    )}
                    <span className="ml-2 text-xs text-gray-500">
                      ({TYPE_LABELS[dim.dimension_type as keyof typeof TYPE_LABELS] || dim.dimension_type})
                    </span>
                  </div>
                )}
              </div>

              {/* 신뢰도 */}
              <div className={`text-sm mr-4 ${
                dim.confidence >= 0.9 ? 'text-green-600' :
                dim.confidence >= 0.7 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {(dim.confidence * 100).toFixed(0)}%
              </div>

              {/* 액션 버튼 */}
              {dim.status === 'pending' && editingId !== dim.id && (
                <div className="flex gap-1">
                  <button
                    onClick={() => onApprove(dim.id)}
                    className="px-2 py-1 text-xs bg-green-100 text-green-700
                             rounded hover:bg-green-200"
                  >
                    승인
                  </button>
                  <button
                    onClick={() => handleStartEdit(dim)}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700
                             rounded hover:bg-blue-200"
                  >
                    수정
                  </button>
                  <button
                    onClick={() => onReject(dim.id)}
                    className="px-2 py-1 text-xs bg-red-100 text-red-700
                             rounded hover:bg-red-200"
                  >
                    거부
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 빈 상태 */}
      {dimensions.length === 0 && (
        <div className="p-8 text-center text-gray-500">
          검출된 치수가 없습니다.
        </div>
      )}
    </div>
  );
};

export default DimensionList;
```

#### 2.6.2 파일 생성: `frontend/src/components/DimensionOverlay.tsx`

```tsx
/**
 * 이미지 위에 치수 바운딩박스 오버레이
 */
import React from 'react';

interface Dimension {
  id: string;
  bbox: number[];
  value: string;
  confidence: number;
  status: string;
}

interface DimensionOverlayProps {
  dimensions: Dimension[];
  imageWidth: number;
  imageHeight: number;
  highlightId: string | null;
  onDimensionClick?: (id: string) => void;
}

export const DimensionOverlay: React.FC<DimensionOverlayProps> = ({
  dimensions,
  imageWidth,
  imageHeight,
  highlightId,
  onDimensionClick
}) => {
  const getColor = (dim: Dimension) => {
    if (dim.id === highlightId) return '#3B82F6'; // blue-500
    if (dim.status === 'approved') return '#10B981'; // green-500
    if (dim.status === 'rejected') return '#EF4444'; // red-500
    if (dim.status === 'modified') return '#F59E0B'; // yellow-500

    // 신뢰도 기반 색상
    if (dim.confidence >= 0.9) return '#10B981';
    if (dim.confidence >= 0.7) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <svg
      className="absolute top-0 left-0 pointer-events-none"
      width={imageWidth}
      height={imageHeight}
      style={{ pointerEvents: 'none' }}
    >
      {dimensions.map((dim) => {
        const [x1, y1, x2, y2] = dim.bbox;
        const width = x2 - x1;
        const height = y2 - y1;
        const color = getColor(dim);
        const isHighlighted = dim.id === highlightId;

        return (
          <g key={dim.id} style={{ pointerEvents: 'auto' }}>
            {/* 바운딩 박스 */}
            <rect
              x={x1}
              y={y1}
              width={width}
              height={height}
              fill={`${color}20`}
              stroke={color}
              strokeWidth={isHighlighted ? 3 : 1.5}
              rx={2}
              onClick={() => onDimensionClick?.(dim.id)}
              style={{ cursor: 'pointer' }}
            />

            {/* 치수 값 라벨 */}
            <text
              x={x1}
              y={y1 - 4}
              fontSize={isHighlighted ? 14 : 11}
              fontWeight={isHighlighted ? 'bold' : 'normal'}
              fill={color}
            >
              {dim.value}
            </text>

            {/* 신뢰도 표시 (하이라이트 시) */}
            {isHighlighted && (
              <text
                x={x2 + 4}
                y={y1 + height / 2}
                fontSize={10}
                fill={color}
              >
                {(dim.confidence * 100).toFixed(0)}%
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

export default DimensionOverlay;
```

### 2.7 Step 6: 치수 테이블 출력 (Day 12-13)

#### 2.7.1 파일 생성: `backend/services/export_service.py`

```python
"""치수 테이블 내보내기 서비스"""
import io
import csv
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

from schemas.dimension import Dimension


class ExportService:
    """내보내기 서비스"""

    def export_dimensions_to_excel(
        self,
        dimensions: List[Dimension],
        session_info: dict = None
    ) -> io.BytesIO:
        """
        치수 목록을 Excel 파일로 내보내기

        Args:
            dimensions: 치수 목록
            session_info: 세션 정보 (선택)

        Returns:
            Excel 파일 BytesIO
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "치수 목록"

        # 스타일 정의
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 헤더 정의
        headers = ["No.", "치수값", "공차", "유형", "단위", "신뢰도", "상태", "연결 대상"]

        # 헤더 작성
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # 데이터 작성
        type_labels = {
            "length": "길이",
            "diameter": "직경",
            "radius": "반경",
            "angle": "각도",
            "tolerance": "공차",
            "surface_finish": "표면거칠기",
            "unknown": "미분류"
        }

        status_labels = {
            "pending": "대기",
            "approved": "승인",
            "rejected": "거부",
            "modified": "수정됨"
        }

        for idx, dim in enumerate(dimensions, 1):
            row = idx + 1
            ws.cell(row=row, column=1, value=idx).border = thin_border
            ws.cell(row=row, column=2, value=dim.value).border = thin_border
            ws.cell(row=row, column=3, value=dim.tolerance or "-").border = thin_border
            ws.cell(row=row, column=4, value=type_labels.get(dim.dimension_type, dim.dimension_type)).border = thin_border
            ws.cell(row=row, column=5, value=dim.unit or "-").border = thin_border
            ws.cell(row=row, column=6, value=f"{dim.confidence * 100:.1f}%").border = thin_border
            ws.cell(row=row, column=7, value=status_labels.get(dim.status, dim.status)).border = thin_border
            ws.cell(row=row, column=8, value=dim.linked_to or "-").border = thin_border

        # 열 너비 조정
        column_widths = [6, 15, 12, 12, 8, 10, 10, 15]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

        # 통계 시트 추가
        ws_stats = wb.create_sheet(title="통계")
        stats = self._calculate_stats(dimensions)

        ws_stats.cell(row=1, column=1, value="항목")
        ws_stats.cell(row=1, column=2, value="값")
        ws_stats.cell(row=2, column=1, value="전체 치수")
        ws_stats.cell(row=2, column=2, value=stats["total"])
        ws_stats.cell(row=3, column=1, value="승인")
        ws_stats.cell(row=3, column=2, value=stats["approved"])
        ws_stats.cell(row=4, column=1, value="거부")
        ws_stats.cell(row=4, column=2, value=stats["rejected"])
        ws_stats.cell(row=5, column=1, value="평균 신뢰도")
        ws_stats.cell(row=5, column=2, value=f"{stats['avg_confidence'] * 100:.1f}%")

        # BytesIO로 저장
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def export_dimensions_to_csv(self, dimensions: List[Dimension]) -> str:
        """치수 목록을 CSV 문자열로 내보내기"""
        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow(["No.", "치수값", "공차", "유형", "단위", "신뢰도", "상태"])

        # 데이터
        for idx, dim in enumerate(dimensions, 1):
            writer.writerow([
                idx,
                dim.value,
                dim.tolerance or "",
                dim.dimension_type,
                dim.unit or "",
                f"{dim.confidence * 100:.1f}%",
                dim.status
            ])

        return output.getvalue()

    def _calculate_stats(self, dimensions: List[Dimension]) -> dict:
        """통계 계산"""
        if not dimensions:
            return {
                "total": 0,
                "approved": 0,
                "rejected": 0,
                "pending": 0,
                "avg_confidence": 0
            }

        return {
            "total": len(dimensions),
            "approved": sum(1 for d in dimensions if d.status == "approved"),
            "rejected": sum(1 for d in dimensions if d.status == "rejected"),
            "pending": sum(1 for d in dimensions if d.status == "pending"),
            "avg_confidence": sum(d.confidence for d in dimensions) / len(dimensions)
        }


# 싱글톤 인스턴스
export_service = ExportService()
```

#### 2.7.2 내보내기 API 추가: `backend/routers/export_router.py`

```python
"""내보내기 API"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

from services.export_service import export_service
from schemas.dimension import Dimension

router = APIRouter(prefix="/export", tags=["Export"])


@router.post("/dimensions/excel/{session_id}")
async def export_dimensions_excel(session_id: str):
    """치수 목록 Excel 다운로드"""
    # TODO: 세션에서 치수 목록 조회
    dimensions = []  # get_dimensions_by_session(session_id)

    excel_file = export_service.export_dimensions_to_excel(
        dimensions,
        session_info={"session_id": session_id}
    )

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=dimensions_{session_id}.xlsx"
        }
    )


@router.post("/dimensions/csv/{session_id}")
async def export_dimensions_csv(session_id: str):
    """치수 목록 CSV 다운로드"""
    dimensions = []  # get_dimensions_by_session(session_id)

    csv_content = export_service.export_dimensions_to_csv(dimensions)

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=dimensions_{session_id}.csv"
        }
    )
```

### 2.8 Step 7: 테스트 및 검증 (Day 14)

#### 2.8.1 통합 테스트 시나리오

```python
"""Phase 1 통합 테스트"""
import pytest
from httpx import AsyncClient
from api_server import app  # main.py → api_server.py


@pytest.mark.asyncio
class TestPhase1Integration:
    """Phase 1 통합 테스트"""

    async def test_full_workflow(self):
        """전체 워크플로우 테스트

        Note: 기존 Blueprint AI BOM은 /api/v1 prefix 없이 직접 라우터를 사용합니다.
        예: /session, /detection, /bom, /analysis
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. 세션 생성 (기존 session_router 패턴)
            response = await client.post("/session/create")
            assert response.status_code == 200
            session_id = response.json()["session_id"]

            # 2. 분석 옵션 설정 (기계 부품도 프리셋)
            response = await client.post(
                f"/analysis/options/{session_id}/preset/mechanical_part"
            )
            assert response.status_code == 200
            options = response.json()
            assert options["enable_dimension_ocr"] == True
            assert options["enable_symbol_detection"] == False

            # 3. 분석 실행
            response = await client.post(
                f"/analysis/run/{session_id}",
                params={"image_path": "/path/to/sample2_interm_shaft.jpg"}
            )
            assert response.status_code == 200
            result = response.json()
            assert "dimensions" in result
            assert len(result["dimensions"]) > 0

            # 4. 치수 승인
            dim_id = result["dimensions"][0]["id"]
            response = await client.put(
                f"/dimension/{session_id}/{dim_id}",
                json={"status": "approved"}
            )
            assert response.status_code == 200

            # 5. Excel 내보내기
            response = await client.post(
                f"/export/dimensions/excel/{session_id}"
            )
            assert response.status_code == 200
            assert "spreadsheetml" in response.headers["content-type"]
```

#### 2.8.2 테스트 실행

```bash
# 백엔드 테스트
cd blueprint-ai-bom/backend
pytest tests/ -v --cov=. --cov-report=html

# 프론트엔드 테스트
cd ../frontend
npm run test
```

---

## 3. Phase 2: 치수선 기반 관계 추출 (1주)

### 3.1 개요

**목표:** 관계 추출 정확도 60% → 85%

**핵심 알고리즘:**
1. 치수선(dimension line) 검출
2. 화살표 방향 분석
3. 대상 객체 추론

### 3.2 Step 1: 치수선 검출 모듈 (Day 1-2)

#### 3.2.1 파일 생성: `backend/services/dimension_line_detector.py`

```python
"""치수선 검출 서비스"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class DimensionLine:
    """치수선 데이터"""
    id: str
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    arrow_direction: str  # 'left', 'right', 'up', 'down', 'both'
    associated_text_bbox: Optional[List[float]] = None
    confidence: float = 0.0


class DimensionLineDetector:
    """
    치수선 검출기

    Hough 변환 + 화살표 검출로 치수선 추출
    """

    def __init__(self):
        self.min_line_length = 30
        self.max_line_gap = 10
        self.arrow_detection_radius = 20

    def detect(self, image_path: str) -> List[DimensionLine]:
        """
        이미지에서 치수선 검출

        Args:
            image_path: 이미지 경로

        Returns:
            검출된 치수선 목록
        """
        # 이미지 로드
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 엣지 검출
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Hough 변환으로 직선 검출
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=50,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )

        if lines is None:
            return []

        dimension_lines = []
        for idx, line in enumerate(lines):
            x1, y1, x2, y2 = line[0]

            # 수평/수직 선만 치수선으로 간주
            if not self._is_axis_aligned(x1, y1, x2, y2):
                continue

            # 화살표 검출
            arrow_dir = self._detect_arrow_direction(img, (x1, y1), (x2, y2))

            if arrow_dir:  # 화살표가 있는 선만 치수선으로 간주
                dim_line = DimensionLine(
                    id=f"dimline_{idx:03d}",
                    start_point=(float(x1), float(y1)),
                    end_point=(float(x2), float(y2)),
                    arrow_direction=arrow_dir,
                    confidence=0.8
                )
                dimension_lines.append(dim_line)

        return dimension_lines

    def _is_axis_aligned(self, x1, y1, x2, y2, tolerance=5) -> bool:
        """수평 또는 수직 선인지 확인"""
        return abs(x1 - x2) < tolerance or abs(y1 - y2) < tolerance

    def _detect_arrow_direction(
        self,
        img: np.ndarray,
        start: Tuple[int, int],
        end: Tuple[int, int]
    ) -> Optional[str]:
        """
        선 끝점에서 화살표 방향 검출

        Returns:
            'left', 'right', 'up', 'down', 'both', None
        """
        h, w = img.shape[:2]
        x1, y1 = start
        x2, y2 = end

        # 끝점 주변 ROI 추출
        def get_roi(x, y):
            r = self.arrow_detection_radius
            x_min = max(0, x - r)
            x_max = min(w, x + r)
            y_min = max(0, y - r)
            y_max = min(h, y + r)
            return img[y_min:y_max, x_min:x_max]

        roi_start = get_roi(x1, y1)
        roi_end = get_roi(x2, y2)

        # 화살표 패턴 검출 (삼각형 형태)
        has_arrow_start = self._has_arrow_pattern(roi_start)
        has_arrow_end = self._has_arrow_pattern(roi_end)

        if has_arrow_start and has_arrow_end:
            return 'both'
        elif has_arrow_start:
            # start 방향으로 화살표
            if abs(x1 - x2) > abs(y1 - y2):
                return 'left' if x1 < x2 else 'right'
            else:
                return 'up' if y1 < y2 else 'down'
        elif has_arrow_end:
            # end 방향으로 화살표
            if abs(x1 - x2) > abs(y1 - y2):
                return 'right' if x1 < x2 else 'left'
            else:
                return 'down' if y1 < y2 else 'up'

        return None

    def _has_arrow_pattern(self, roi: np.ndarray) -> bool:
        """
        ROI에서 화살표 패턴 검출

        삼각형 컨투어 검출로 판단
        """
        if roi.size == 0:
            return False

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # 근사화하여 꼭짓점 수 확인
            epsilon = 0.1 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # 삼각형 (3개 꼭짓점)
            if len(approx) == 3:
                area = cv2.contourArea(contour)
                if 10 < area < 500:  # 적절한 크기
                    return True

        return False


# 싱글톤 인스턴스
dimension_line_detector = DimensionLineDetector()
```

### 3.3 Step 2: 관계 추출 엔진 (Day 3-4)

#### 3.3.1 파일 생성: `backend/services/relation_extractor.py`

```python
"""관계 추출 서비스"""
from typing import List, Optional, Tuple
from dataclasses import dataclass
import math

from schemas.dimension import Dimension
from .dimension_line_detector import DimensionLine, dimension_line_detector


@dataclass
class Relation:
    """관계 데이터"""
    id: str
    source_id: str
    source_type: str  # 'dimension', 'symbol', 'text'
    target_id: str
    target_type: str
    relation_type: str  # 'measures', 'has_dimension', 'connected_via'
    confidence: float
    metadata: dict = None


class RelationExtractor:
    """
    분석 요소 간 관계 추출

    전략:
    1. 치수선이 있는 경우: 치수선 방향으로 대상 추론 (높은 신뢰도)
    2. 치수선이 없는 경우: 근접성 기반 폴백 (낮은 신뢰도)
    """

    def __init__(self):
        self.proximity_threshold = 50  # 픽셀

    def extract_dimension_relations(
        self,
        dimensions: List[Dimension],
        dimension_lines: List[DimensionLine],
        regions: List[dict] = None
    ) -> List[Relation]:
        """
        치수-객체 관계 추출

        Args:
            dimensions: OCR로 추출된 치수 목록
            dimension_lines: 검출된 치수선 목록
            regions: 객체 영역 목록 (있는 경우)

        Returns:
            추출된 관계 목록
        """
        relations = []

        for dim in dimensions:
            # 1. 치수선 기반 관계 추출 시도
            dim_line = self._find_associated_dimension_line(dim, dimension_lines)

            if dim_line:
                # 치수선 방향으로 대상 영역 추론
                target_region = self._trace_dimension_line_target(dim_line, regions)

                if target_region:
                    relation = Relation(
                        id=f"rel_{dim.id}_{target_region['id']}",
                        source_id=target_region['id'],
                        source_type='region',
                        target_id=dim.id,
                        target_type='dimension',
                        relation_type=self._infer_relation_type(dim, dim_line),
                        confidence=0.95,  # 치수선 기반 = 높은 신뢰도
                        metadata={
                            'method': 'dimension_line_trace',
                            'dimension_line_id': dim_line.id
                        }
                    )
                    relations.append(relation)
                    continue

            # 2. 폴백: 근접성 기반 관계 추출
            if regions:
                nearby_regions = self._find_nearby_regions(dim, regions)
                for region in nearby_regions:
                    relation = Relation(
                        id=f"rel_{dim.id}_{region['id']}",
                        source_id=region['id'],
                        source_type='region',
                        target_id=dim.id,
                        target_type='dimension',
                        relation_type='unknown',
                        confidence=0.60,  # 근접성 기반 = 낮은 신뢰도
                        metadata={'method': 'proximity'}
                    )
                    relations.append(relation)

        return relations

    def _find_associated_dimension_line(
        self,
        dim: Dimension,
        dimension_lines: List[DimensionLine]
    ) -> Optional[DimensionLine]:
        """
        치수 텍스트와 연관된 치수선 찾기

        치수 텍스트 bbox 근처의 치수선 검색
        """
        dim_center = self._get_bbox_center(dim.bbox)

        for line in dimension_lines:
            # 치수선의 중간점
            line_mid = (
                (line.start_point[0] + line.end_point[0]) / 2,
                (line.start_point[1] + line.end_point[1]) / 2
            )

            # 거리 계산
            distance = math.sqrt(
                (dim_center[0] - line_mid[0]) ** 2 +
                (dim_center[1] - line_mid[1]) ** 2
            )

            # 치수선 길이의 절반 이내에 있으면 연관
            line_length = math.sqrt(
                (line.end_point[0] - line.start_point[0]) ** 2 +
                (line.end_point[1] - line.start_point[1]) ** 2
            )

            if distance < line_length / 2 + 30:
                return line

        return None

    def _trace_dimension_line_target(
        self,
        dim_line: DimensionLine,
        regions: List[dict]
    ) -> Optional[dict]:
        """
        치수선 방향으로 대상 영역 추론
        """
        if not regions:
            return None

        # 화살표 방향으로 영역 검색
        direction = dim_line.arrow_direction

        # 치수선 끝점 확장
        if direction in ['left', 'right', 'both']:
            # 수평 치수선
            search_y = (dim_line.start_point[1] + dim_line.end_point[1]) / 2

            for region in regions:
                region_center_y = (region['bbox'][1] + region['bbox'][3]) / 2
                if abs(region_center_y - search_y) < 50:
                    # 같은 수평선상에 있는 영역
                    return region

        elif direction in ['up', 'down']:
            # 수직 치수선
            search_x = (dim_line.start_point[0] + dim_line.end_point[0]) / 2

            for region in regions:
                region_center_x = (region['bbox'][0] + region['bbox'][2]) / 2
                if abs(region_center_x - search_x) < 50:
                    return region

        return None

    def _find_nearby_regions(
        self,
        dim: Dimension,
        regions: List[dict]
    ) -> List[dict]:
        """근접 영역 찾기 (폴백)"""
        dim_center = self._get_bbox_center(dim.bbox)
        nearby = []

        for region in regions:
            region_center = self._get_bbox_center(region['bbox'])
            distance = math.sqrt(
                (dim_center[0] - region_center[0]) ** 2 +
                (dim_center[1] - region_center[1]) ** 2
            )

            if distance < self.proximity_threshold:
                nearby.append(region)

        return nearby

    def _infer_relation_type(self, dim: Dimension, dim_line: DimensionLine) -> str:
        """관계 유형 추론"""
        if dim.dimension_type == 'diameter':
            return 'has_diameter'
        elif dim.dimension_type == 'radius':
            return 'has_radius'
        elif dim.dimension_type == 'length':
            if dim_line.arrow_direction in ['left', 'right', 'both']:
                return 'has_width'
            else:
                return 'has_height'
        elif dim.dimension_type == 'angle':
            return 'has_angle'
        else:
            return 'has_dimension'

    def _get_bbox_center(self, bbox: List[float]) -> Tuple[float, float]:
        """bbox 중심점 계산"""
        return (
            (bbox[0] + bbox[2]) / 2,
            (bbox[1] + bbox[3]) / 2
        )


# 싱글톤 인스턴스
relation_extractor = RelationExtractor()
```

### 3.4 Step 3: 관계 API 및 UI (Day 5-7)

#### 3.4.1 관계 스키마: `backend/schemas/relation.py`

```python
"""관계 스키마"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class RelationType(str, Enum):
    HAS_DIAMETER = "has_diameter"
    HAS_RADIUS = "has_radius"
    HAS_WIDTH = "has_width"
    HAS_HEIGHT = "has_height"
    HAS_LENGTH = "has_length"
    HAS_ANGLE = "has_angle"
    HAS_DIMENSION = "has_dimension"
    CONNECTED_VIA = "connected_via"
    HAS_TAG = "has_tag"
    UNKNOWN = "unknown"


class RelationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class RelationSchema(BaseModel):
    """관계 스키마"""
    id: str
    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relation_type: RelationType
    confidence: float = Field(..., ge=0, le=1)
    status: RelationStatus = RelationStatus.PENDING
    metadata: Optional[dict] = None


class RelationUpdate(BaseModel):
    """관계 수정"""
    relation_type: Optional[RelationType] = None
    status: Optional[RelationStatus] = None
    target_id: Optional[str] = None


class RelationCreate(BaseModel):
    """관계 수동 생성"""
    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relation_type: RelationType
```

---

## 4. Phase 3: Active Learning 통합 (1주)

### 4.1 개요

**목표:** 검증 효율 +30%

**핵심 기능:**
1. 신뢰도 기반 우선순위 큐
2. 저신뢰 항목 우선 검증
3. 고신뢰 항목 일괄 승인
4. 검증 결과 로깅

### 4.2 Step 1: 우선순위 큐 로직 (Day 1-2)

#### 4.2.1 파일 생성: `backend/services/active_learning_service.py`

```python
"""Active Learning 서비스"""
from typing import List, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class Priority(str, Enum):
    CRITICAL = "critical"  # 신뢰도 < 0.7
    HIGH = "high"          # 관계 연결 실패
    MEDIUM = "medium"      # 신뢰도 0.7-0.9
    LOW = "low"            # 신뢰도 > 0.9


@dataclass
class VerificationItem:
    """검증 대상 항목"""
    id: str
    item_type: str  # 'dimension', 'symbol', 'relation'
    data: Dict[str, Any]
    confidence: float
    priority: Priority
    has_relation: bool = True


@dataclass
class VerificationLog:
    """검증 결과 로그"""
    item_id: str
    item_type: str
    original_data: Dict[str, Any]
    user_action: str  # 'approved', 'rejected', 'modified'
    modified_data: Dict[str, Any] = None
    timestamp: datetime = None
    session_id: str = None


class ActiveLearningService:
    """
    Active Learning 기반 검증 관리

    - 저신뢰 항목 우선 검증
    - 검증 결과 로깅
    - 모델 개선 데이터 수집
    """

    def __init__(self):
        self.verification_logs: List[VerificationLog] = []
        self.thresholds = {
            'critical': 0.7,
            'auto_approve': 0.9
        }

    def prioritize_items(
        self,
        items: List[Dict[str, Any]],
        item_type: str = 'dimension'
    ) -> Dict[str, List[VerificationItem]]:
        """
        항목들을 우선순위별로 분류

        Args:
            items: 검증 대상 항목들
            item_type: 항목 유형

        Returns:
            우선순위별 분류된 항목 딕셔너리
        """
        prioritized = {
            Priority.CRITICAL: [],
            Priority.HIGH: [],
            Priority.MEDIUM: [],
            Priority.LOW: []
        }

        for item in items:
            confidence = item.get('confidence', 0)
            has_relation = item.get('linked_to') is not None or item.get('has_relation', True)

            # 우선순위 결정
            if confidence < self.thresholds['critical']:
                priority = Priority.CRITICAL
            elif not has_relation:
                priority = Priority.HIGH
            elif confidence < self.thresholds['auto_approve']:
                priority = Priority.MEDIUM
            else:
                priority = Priority.LOW

            verification_item = VerificationItem(
                id=item.get('id'),
                item_type=item_type,
                data=item,
                confidence=confidence,
                priority=priority,
                has_relation=has_relation
            )
            prioritized[priority].append(verification_item)

        return prioritized

    def get_verification_queue(
        self,
        items: List[Dict[str, Any]],
        item_type: str = 'dimension'
    ) -> List[VerificationItem]:
        """
        검증 큐 생성 (우선순위 순)

        Returns:
            우선순위 순으로 정렬된 검증 항목 목록
        """
        prioritized = self.prioritize_items(items, item_type)

        queue = []
        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            # 각 우선순위 내에서 신뢰도 낮은 순 정렬
            sorted_items = sorted(
                prioritized[priority],
                key=lambda x: x.confidence
            )
            queue.extend(sorted_items)

        return queue

    def get_auto_approve_candidates(
        self,
        items: List[Dict[str, Any]]
    ) -> List[str]:
        """
        자동 승인 후보 ID 목록

        신뢰도 > 0.9인 항목들
        """
        return [
            item['id'] for item in items
            if item.get('confidence', 0) >= self.thresholds['auto_approve']
        ]

    def log_verification(
        self,
        item_id: str,
        item_type: str,
        original_data: Dict[str, Any],
        user_action: str,
        modified_data: Dict[str, Any] = None,
        session_id: str = None
    ):
        """
        검증 결과 로깅

        이 데이터는 모델 재학습에 활용
        """
        log = VerificationLog(
            item_id=item_id,
            item_type=item_type,
            original_data=original_data,
            user_action=user_action,
            modified_data=modified_data,
            timestamp=datetime.now(),
            session_id=session_id
        )
        self.verification_logs.append(log)

        # 로그 파일에도 저장
        self._save_log_to_file(log)

    def _save_log_to_file(self, log: VerificationLog):
        """로그 파일 저장"""
        log_entry = {
            'item_id': log.item_id,
            'item_type': log.item_type,
            'original_data': log.original_data,
            'user_action': log.user_action,
            'modified_data': log.modified_data,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None,
            'session_id': log.session_id
        }

        # TODO: 실제 구현에서는 DB 또는 파일에 저장
        logger.info(f"Verification log: {json.dumps(log_entry, default=str)}")

    def get_verification_stats(
        self,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        검증 통계
        """
        prioritized = self.prioritize_items(items)

        return {
            'total': len(items),
            'critical': len(prioritized[Priority.CRITICAL]),
            'high': len(prioritized[Priority.HIGH]),
            'medium': len(prioritized[Priority.MEDIUM]),
            'low': len(prioritized[Priority.LOW]),
            'auto_approve_candidates': len(self.get_auto_approve_candidates(items)),
            'estimated_review_time_minutes': self._estimate_review_time(prioritized)
        }

    def _estimate_review_time(self, prioritized: Dict[Priority, List]) -> float:
        """예상 검토 시간 (분)"""
        # 항목당 예상 시간 (초)
        time_per_item = {
            Priority.CRITICAL: 30,  # 저신뢰 = 꼼꼼히 확인
            Priority.HIGH: 20,
            Priority.MEDIUM: 10,
            Priority.LOW: 2  # 대부분 자동 승인
        }

        total_seconds = sum(
            len(items) * time_per_item[priority]
            for priority, items in prioritized.items()
        )

        return round(total_seconds / 60, 1)


# 싱글톤 인스턴스
active_learning_service = ActiveLearningService()
```

### 4.3 Step 2: Active Learning API (Day 3)

#### 4.3.1 파일 추가: `backend/routers/verification_router.py`

```python
"""검증 API (Active Learning 통합)"""
from fastapi import APIRouter, HTTPException
from typing import List

from services.active_learning_service import (
    active_learning_service,
    Priority
)
from schemas.dimension import Dimension

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.get("/queue/{session_id}")
async def get_verification_queue(session_id: str):
    """
    검증 큐 조회

    우선순위 순으로 정렬된 검증 항목 반환
    """
    # TODO: 세션에서 항목 조회
    items = []  # get_items_by_session(session_id)

    queue = active_learning_service.get_verification_queue(items)

    return {
        "session_id": session_id,
        "queue": [
            {
                "id": item.id,
                "type": item.item_type,
                "priority": item.priority.value,
                "confidence": item.confidence,
                "data": item.data
            }
            for item in queue
        ],
        "stats": active_learning_service.get_verification_stats(items)
    }


@router.get("/auto-approve-candidates/{session_id}")
async def get_auto_approve_candidates(session_id: str):
    """자동 승인 후보 조회"""
    items = []  # get_items_by_session(session_id)
    candidates = active_learning_service.get_auto_approve_candidates(items)

    return {
        "session_id": session_id,
        "candidates": candidates,
        "count": len(candidates)
    }


@router.post("/bulk-approve/{session_id}")
async def bulk_approve(session_id: str, item_ids: List[str]):
    """일괄 승인"""
    # TODO: 실제 승인 처리
    for item_id in item_ids:
        active_learning_service.log_verification(
            item_id=item_id,
            item_type="dimension",
            original_data={},  # 원본 데이터
            user_action="approved",
            session_id=session_id
        )

    return {
        "approved_count": len(item_ids),
        "session_id": session_id
    }


@router.post("/log/{session_id}")
async def log_verification_action(
    session_id: str,
    item_id: str,
    item_type: str,
    action: str,
    original_data: dict,
    modified_data: dict = None
):
    """검증 액션 로깅"""
    active_learning_service.log_verification(
        item_id=item_id,
        item_type=item_type,
        original_data=original_data,
        user_action=action,
        modified_data=modified_data,
        session_id=session_id
    )

    return {"status": "logged"}
```

### 4.4 Step 3: 프론트엔드 검증 큐 UI (Day 4-5)

#### 4.4.1 파일 생성: `frontend/src/components/VerificationQueue.tsx`

```tsx
/**
 * Active Learning 검증 큐 컴포넌트
 */
import React, { useState, useEffect } from 'react';

interface VerificationItem {
  id: string;
  type: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  confidence: number;
  data: any;
}

interface VerificationStats {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  auto_approve_candidates: number;
  estimated_review_time_minutes: number;
}

interface VerificationQueueProps {
  sessionId: string;
  onItemAction: (id: string, action: 'approve' | 'reject' | 'modify', data?: any) => void;
}

const PRIORITY_CONFIG = {
  critical: { label: '🔴 긴급', color: 'bg-red-100 text-red-800', border: 'border-red-300' },
  high: { label: '🟠 높음', color: 'bg-orange-100 text-orange-800', border: 'border-orange-300' },
  medium: { label: '🟡 보통', color: 'bg-yellow-100 text-yellow-800', border: 'border-yellow-300' },
  low: { label: '🟢 낮음', color: 'bg-green-100 text-green-800', border: 'border-green-300' }
};

export const VerificationQueue: React.FC<VerificationQueueProps> = ({
  sessionId,
  onItemAction
}) => {
  const [queue, setQueue] = useState<VerificationItem[]>([]);
  const [stats, setStats] = useState<VerificationStats | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'critical' | 'auto'>('all');
  const [loading, setLoading] = useState(false);

  // 큐 로드
  useEffect(() => {
    const loadQueue = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/verification/queue/${sessionId}`);
        const data = await response.json();
        setQueue(data.queue);
        setStats(data.stats);
      } catch (error) {
        console.error('Failed to load queue:', error);
      } finally {
        setLoading(false);
      }
    };

    loadQueue();
  }, [sessionId]);

  // 일괄 승인
  const handleBulkApprove = async () => {
    const lowPriorityIds = queue
      .filter(item => item.priority === 'low')
      .map(item => item.id);

    if (lowPriorityIds.length === 0) return;

    const confirmed = window.confirm(
      `신뢰도 90% 이상인 ${lowPriorityIds.length}개 항목을 일괄 승인하시겠습니까?`
    );

    if (!confirmed) return;

    try {
      await fetch(`/verification/bulk-approve/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lowPriorityIds)
      });

      // 승인된 항목 제거
      setQueue(prev => prev.filter(item => !lowPriorityIds.includes(item.id)));
    } catch (error) {
      console.error('Bulk approve failed:', error);
    }
  };

  // 필터링된 항목
  const filteredQueue = queue.filter(item => {
    if (activeTab === 'critical') return item.priority === 'critical';
    if (activeTab === 'auto') return item.priority === 'low';
    return true;
  });

  return (
    <div className="bg-white rounded-lg shadow">
      {/* 통계 헤더 */}
      {stats && (
        <div className="p-4 border-b bg-gray-50">
          <div className="flex justify-between items-center">
            <div className="flex gap-4 text-sm">
              <span>전체: <strong>{stats.total}</strong></span>
              <span className="text-red-600">긴급: {stats.critical}</span>
              <span className="text-orange-600">높음: {stats.high}</span>
              <span className="text-yellow-600">보통: {stats.medium}</span>
              <span className="text-green-600">자동승인 후보: {stats.auto_approve_candidates}</span>
            </div>
            <div className="text-sm text-gray-500">
              예상 검토 시간: ~{stats.estimated_review_time_minutes}분
            </div>
          </div>
        </div>
      )}

      {/* 탭 */}
      <div className="flex border-b">
        {[
          { id: 'all', label: '전체' },
          { id: 'critical', label: '🔴 긴급 우선' },
          { id: 'auto', label: '🟢 자동 승인 후보' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === tab.id
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}

        {/* 일괄 승인 버튼 */}
        {activeTab === 'auto' && stats && stats.auto_approve_candidates > 0 && (
          <button
            onClick={handleBulkApprove}
            className="ml-auto mr-4 px-3 py-1 text-sm bg-green-600 text-white
                     rounded hover:bg-green-700"
          >
            {stats.auto_approve_candidates}개 일괄 승인
          </button>
        )}
      </div>

      {/* 항목 목록 */}
      <div className="divide-y max-h-[400px] overflow-y-auto">
        {filteredQueue.map((item, index) => {
          const config = PRIORITY_CONFIG[item.priority];

          return (
            <div
              key={item.id}
              className={`p-3 hover:bg-gray-50 ${config.border} border-l-4`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 text-sm w-6">#{index + 1}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${config.color}`}>
                    {config.label}
                  </span>
                  <span className="font-medium">{item.data.value || item.id}</span>
                  <span className={`text-sm ${
                    item.confidence >= 0.9 ? 'text-green-600' :
                    item.confidence >= 0.7 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="flex gap-1">
                  <button
                    onClick={() => onItemAction(item.id, 'approve')}
                    className="px-2 py-1 text-xs bg-green-100 text-green-700
                             rounded hover:bg-green-200"
                  >
                    승인
                  </button>
                  <button
                    onClick={() => onItemAction(item.id, 'modify')}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700
                             rounded hover:bg-blue-200"
                  >
                    수정
                  </button>
                  <button
                    onClick={() => onItemAction(item.id, 'reject')}
                    className="px-2 py-1 text-xs bg-red-100 text-red-700
                             rounded hover:bg-red-200"
                  >
                    거부
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 빈 상태 */}
      {filteredQueue.length === 0 && !loading && (
        <div className="p-8 text-center text-gray-500">
          {activeTab === 'critical'
            ? '긴급 검증이 필요한 항목이 없습니다.'
            : activeTab === 'auto'
            ? '자동 승인 후보가 없습니다.'
            : '검증할 항목이 없습니다.'}
        </div>
      )}
    </div>
  );
};

export default VerificationQueue;
```

---

## 5. Phase 4: VLM 초기 분류 (1주)

> **참고:** 이 Phase는 온라인 API 사용 가능 시 구현

### 5.1 파일 생성: `backend/services/vlm_classifier.py`

```python
"""VLM 기반 도면 분류 서비스"""
import base64
import httpx
import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class DrawingType(str, Enum):
    MECHANICAL_PART = "mechanical_part"
    PID = "pid"
    ASSEMBLY = "assembly"
    ELECTRICAL = "electrical"
    ARCHITECTURAL = "architectural"
    UNKNOWN = "unknown"


class VLMClassifier:
    """
    Vision Language Model 기반 도면 분류

    GPT-4V 또는 Claude Vision API 사용
    """

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.client = httpx.AsyncClient(timeout=60.0)

        # API 키 (환경변수에서 로드)
        import os
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    async def classify_drawing(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        도면 이미지 분류

        Returns:
            {
                "drawing_type": "mechanical_part",
                "confidence": 0.95,
                "suggested_preset": "mechanical_part",
                "regions": [
                    {"type": "title_block", "bbox": [...], "description": "표제란"},
                    {"type": "main_view", "bbox": [...], "description": "주 투상도"},
                ]
            }
        """
        # 이미지를 base64로 인코딩
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        prompt = self._get_classification_prompt()

        if self.provider == "openai":
            return await self._classify_with_openai(image_data, prompt)
        elif self.provider == "anthropic":
            return await self._classify_with_anthropic(image_data, prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _get_classification_prompt(self) -> str:
        return """이 이미지는 엔지니어링 도면입니다. 다음 정보를 JSON 형식으로 분석해주세요:

1. drawing_type: 도면 유형을 다음 중 하나로 분류
   - mechanical_part: 기계 부품도 (치수, 공차가 주요 정보)
   - pid: P&ID 배관계장도 (심볼, 연결선이 주요 정보)
   - assembly: 조립도 (부품 번호, 분해도)
   - electrical: 전기 회로도
   - architectural: 건축/설비 도면
   - unknown: 분류 불가

2. confidence: 분류 신뢰도 (0-1)

3. suggested_preset: 권장 분석 프리셋 (mechanical_part, pid, assembly)

4. regions: 주요 영역 식별 (좌표는 비율로, 0-1 사이)
   - title_block: 표제란 위치
   - main_view: 메인 도면 영역
   - bom_table: BOM 테이블 (있는 경우)
   - notes: 주석/노트 영역

응답은 반드시 유효한 JSON 형식이어야 합니다."""

    async def _classify_with_openai(
        self,
        image_data: str,
        prompt: str
    ) -> Dict[str, Any]:
        """OpenAI GPT-4V 사용"""
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        }

        response = await self.client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.text}")
            return self._fallback_result()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        import json
        return json.loads(content)

    async def _classify_with_anthropic(
        self,
        image_data: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Anthropic Claude Vision 사용"""
        headers = {
            "x-api-key": self.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }

        response = await self.client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            logger.error(f"Anthropic API error: {response.text}")
            return self._fallback_result()

        result = response.json()
        content = result["content"][0]["text"]

        import json
        # JSON 추출 (마크다운 코드 블록 제거)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content)

    def _fallback_result(self) -> Dict[str, Any]:
        """폴백 결과 (API 실패 시)"""
        return {
            "drawing_type": DrawingType.UNKNOWN.value,
            "confidence": 0.0,
            "suggested_preset": None,
            "regions": [],
            "error": "Classification failed, manual selection required"
        }

    async def close(self):
        await self.client.aclose()


# 싱글톤 인스턴스 (기본: OpenAI)
vlm_classifier = VLMClassifier(provider="openai")
```

---

## 6. Phase 5-7: 추가 구현

> Phase 5-7은 Phase 1-4 완료 후 순차 진행. 상세 구현은 별도 문서로 분리.

### 6.1 Phase 5: 영역 분할 - 핵심 파일

- `backend/services/region_segmenter.py`
- `backend/schemas/region.py`
- `frontend/src/components/RegionEditor.tsx`

### 6.2 Phase 6: P&ID 통합 - 핵심 파일

- `backend/services/line_detector_service.py`
- `backend/services/connectivity_analyzer.py`
- `frontend/src/components/ConnectivityDiagram.tsx`

### 6.3 Phase 7: GD&T 파서 - 핵심 파일

- `backend/services/gdt_parser.py`
- `backend/schemas/gdt.py`
- `frontend/src/components/GDTEditor.tsx`

---

## 9. 테스트 전략

### 9.1 테스트 피라미드

```
              ┌───────┐
              │ E2E   │  Playwright
              │ Tests │
            ┌─┴───────┴─┐
            │Integration│  pytest + httpx
            │   Tests   │
          ┌─┴───────────┴─┐
          │  Unit Tests   │  pytest, vitest
          └───────────────┘
```

### 9.2 테스트 실행 명령어

```bash
# 백엔드 단위 테스트
cd blueprint-ai-bom/backend
pytest tests/unit/ -v

# 백엔드 통합 테스트
pytest tests/integration/ -v

# 프론트엔드 테스트
cd ../frontend
npm run test

# E2E 테스트
npm run test:e2e
```

### 9.3 테스트 커버리지 목표

| 영역 | 목표 커버리지 |
|------|--------------|
| 스키마/모델 | 95% |
| 서비스 레이어 | 80% |
| API 라우터 | 90% |
| 프론트엔드 컴포넌트 | 70% |

---

## 10. 배포 체크리스트

### 10.1 Phase별 배포 체크리스트

#### Phase 1 배포 전

- [ ] eDOCr2 서비스 헬스체크 확인
- [ ] Dimension 스키마 마이그레이션 완료
- [ ] 분석 옵션 API 테스트 통과
- [ ] 치수 검증 UI 크로스브라우저 테스트
- [ ] Excel 내보내기 테스트
- [ ] sample2_interm_shaft.jpg 엔드투엔드 테스트

#### Phase 2-3 배포 전

- [ ] 치수선 검출 정확도 검증
- [ ] 관계 추출 신뢰도 검증
- [ ] Active Learning 큐 로직 테스트
- [ ] 검증 로그 저장 확인

#### Phase 4 배포 전

- [ ] VLM API 키 설정
- [ ] 오프라인 폴백 테스트
- [ ] API 비용 모니터링 설정

### 10.2 환경변수 설정

```bash
# .env.production

# eDOCr2
EDOCR2_BASE_URL=http://edocr2-api:5002

# VLM (Phase 4)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
VLM_PROVIDER=openai  # or anthropic

# Active Learning
VERIFICATION_LOG_PATH=/data/logs/verification
AUTO_APPROVE_THRESHOLD=0.9
CRITICAL_THRESHOLD=0.7
```

---

*작성: Claude Code (Opus 4.5) | 버전: 1.0 | 대상: 개발팀*
