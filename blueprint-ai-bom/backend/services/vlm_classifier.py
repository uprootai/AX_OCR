"""VLM 기반 도면 분류기 (Phase 4)

Vision-Language Model을 활용한 도면 타입 분류
- 로컬 VL API (우선)
- OpenAI GPT-4V (폴백)
- Anthropic Claude Vision (폴백)

v10.4: Dashboard API Key 설정 연동
"""
import os
import base64
import json
import logging
import httpx
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# API Key 서비스 (Dashboard 설정 연동)
_api_key_service = None

def get_api_key_service():
    """API Key 서비스 싱글톤"""
    global _api_key_service
    if _api_key_service is None:
        try:
            from services.api_key_service import APIKeyService
            _api_key_service = APIKeyService()
        except ImportError:
            logger.warning("[VLMClassifier] APIKeyService를 불러올 수 없습니다. 환경변수를 사용합니다.")
            _api_key_service = None
    return _api_key_service


class DrawingType(str, Enum):
    """도면 타입 분류"""
    MECHANICAL_PART = "mechanical_part"     # 기계 부품도
    PID = "pid"                             # P&ID 배관계장도
    ASSEMBLY = "assembly"                   # 조립도
    ELECTRICAL = "electrical"               # 전기 회로도
    ARCHITECTURAL = "architectural"         # 건축 도면
    UNKNOWN = "unknown"                     # 분류 불가


class RegionType(str, Enum):
    """도면 영역 타입"""
    TITLE_BLOCK = "title_block"             # 표제란
    MAIN_VIEW = "main_view"                 # 메인 뷰
    BOM_TABLE = "bom_table"                 # BOM 테이블
    NOTES = "notes"                         # 주석 영역
    DETAIL_VIEW = "detail_view"             # 상세도
    SECTION_VIEW = "section_view"           # 단면도
    DIMENSION_AREA = "dimension_area"       # 치수 영역


@dataclass
class DetectedRegion:
    """검출된 영역"""
    region_type: RegionType
    bbox: List[float]  # [x1, y1, x2, y2] normalized
    confidence: float
    description: Optional[str] = None


@dataclass
class ClassificationResult:
    """분류 결과"""
    drawing_type: DrawingType
    confidence: float
    suggested_preset: str
    regions: List[DetectedRegion] = field(default_factory=list)
    analysis_notes: str = ""
    provider: str = "unknown"
    raw_response: Optional[str] = None


# 분류 프롬프트 (한국어 도면 최적화)
CLASSIFICATION_PROMPT = """당신은 기계 도면 분석 전문가입니다. 주어진 도면 이미지를 분석하고 다음 정보를 JSON 형식으로 반환하세요.

## 분류 기준

### 도면 타입 (drawing_type)
1. **mechanical_part**: 기계 부품도 - 단일 부품의 상세 치수, 공차, 표면처리 정보가 있는 도면
2. **pid**: P&ID (배관계장도) - 파이프, 밸브, 계기류 심볼이 있는 배관 시스템 도면
3. **assembly**: 조립도 - 여러 부품이 조립된 상태를 보여주는 도면
4. **electrical**: 전기 회로도 - 전기 배선, 회로 심볼이 있는 도면
5. **architectural**: 건축 도면 - 평면도, 입면도, 단면도 등 건축 관련 도면
6. **unknown**: 위 카테고리에 해당하지 않는 경우

### 추천 프리셋 (suggested_preset)
- mechanical_part → "dimension_extraction" (치수 추출 최적화)
- pid → "pid_analysis" (P&ID 심볼 및 연결 분석)
- assembly → "assembly_analysis" (조립 관계 분석)
- electrical → "electrical_analysis" (전기 회로 분석)
- architectural → "architectural_analysis" (건축 요소 분석)
- unknown → "general" (일반 분석)

### 영역 검출 (regions)
다음 영역들을 찾아서 bbox를 normalized 좌표 [x1, y1, x2, y2] (0-1 범위)로 반환:
- title_block: 표제란 (보통 우하단)
- main_view: 메인 도면 영역
- bom_table: BOM 테이블 (있는 경우)
- notes: 주석/노트 영역
- detail_view: 상세도 영역 (있는 경우)
- dimension_area: 치수가 집중된 영역

## 응답 형식 (JSON)

```json
{
  "drawing_type": "mechanical_part",
  "confidence": 0.95,
  "suggested_preset": "dimension_extraction",
  "regions": [
    {
      "region_type": "title_block",
      "bbox": [0.7, 0.85, 1.0, 1.0],
      "confidence": 0.9,
      "description": "표제란 - 도면번호, 품명 포함"
    },
    {
      "region_type": "main_view",
      "bbox": [0.05, 0.1, 0.85, 0.8],
      "confidence": 0.95,
      "description": "정면도 - 주요 치수 포함"
    }
  ],
  "analysis_notes": "기계 부품 도면입니다. GD&T 기호와 다수의 치수 표기가 있습니다. 표면 거칠기 기호도 발견됩니다."
}
```

지금 이 도면을 분석해주세요. JSON만 반환하세요."""


class VLMClassifier:
    """VLM 기반 도면 분류기"""

    # 외부 API 엔드포인트 (환경변수로 오버라이드 가능)
    OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
    ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")

    # 지원하는 OpenAI 모델 (Vision 지원)
    OPENAI_MODELS = {
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "description": "가장 저렴한 Vision 모델 - 테스트용 추천",
            "input_cost": 0.15,   # per 1M tokens
            "output_cost": 0.60,  # per 1M tokens
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "description": "고성능 Vision 모델 - 프로덕션용",
            "input_cost": 2.50,
            "output_cost": 10.00,
        },
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "description": "이전 세대 Vision 모델",
            "input_cost": 10.00,
            "output_cost": 30.00,
        },
    }

    def __init__(
        self,
        local_vl_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        default_provider: str = "local",
        openai_model: Optional[str] = None,
    ):
        # Docker 환경에서는 vl-api 컨테이너 이름 사용
        self.local_vl_url = local_vl_url or os.getenv("VL_API_URL", "http://vl-api:5004")

        # API Key 서비스에서 키 가져오기 (우선) → 환경변수 (폴백)
        self._api_key_service = get_api_key_service()

        # OpenAI API 키
        self.openai_api_key = openai_api_key or self._get_key_from_service("openai") or os.getenv("OPENAI_API_KEY")

        # Anthropic API 키
        self.anthropic_api_key = anthropic_api_key or self._get_key_from_service("anthropic") or os.getenv("ANTHROPIC_API_KEY")

        self.default_provider = default_provider

        # OpenAI 모델 (Dashboard 설정 → 환경변수 → 기본값)
        self.openai_model = openai_model or self._get_model_from_service("openai") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Anthropic 모델 (Dashboard 설정 → 기본값)
        self.anthropic_model = self._get_model_from_service("anthropic") or "claude-3-5-sonnet-20241022"

        self.timeout = 120.0

        logger.info(f"[VLMClassifier] 초기화 - provider: {default_provider}, openai_model: {self.openai_model}, anthropic_model: {self.anthropic_model}")

    def _get_key_from_service(self, provider: str) -> Optional[str]:
        """API Key 서비스에서 키 가져오기"""
        if self._api_key_service:
            try:
                return self._api_key_service.get_api_key(provider)
            except Exception as e:
                logger.debug(f"[VLMClassifier] API Key 서비스에서 {provider} 키를 가져올 수 없음: {e}")
        return None

    def _get_model_from_service(self, provider: str) -> Optional[str]:
        """API Key 서비스에서 선택된 모델 가져오기"""
        if self._api_key_service:
            try:
                settings = self._api_key_service.get_api_key_settings(provider)
                return settings.get("selected_model")
            except Exception as e:
                logger.debug(f"[VLMClassifier] API Key 서비스에서 {provider} 모델을 가져올 수 없음: {e}")
        return None

    def refresh_credentials(self):
        """API Key 서비스에서 최신 키/모델로 갱신 (Dashboard 변경 반영)"""
        self._api_key_service = get_api_key_service()

        new_openai_key = self._get_key_from_service("openai") or os.getenv("OPENAI_API_KEY")
        new_anthropic_key = self._get_key_from_service("anthropic") or os.getenv("ANTHROPIC_API_KEY")
        new_openai_model = self._get_model_from_service("openai") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        new_anthropic_model = self._get_model_from_service("anthropic") or "claude-3-5-sonnet-20241022"

        if new_openai_key != self.openai_api_key or new_openai_model != self.openai_model:
            logger.info(f"[VLMClassifier] OpenAI 설정 갱신: 모델 {self.openai_model} → {new_openai_model}")
            self.openai_api_key = new_openai_key
            self.openai_model = new_openai_model

        if new_anthropic_key != self.anthropic_api_key or new_anthropic_model != self.anthropic_model:
            logger.info(f"[VLMClassifier] Anthropic 설정 갱신: 모델 {self.anthropic_model} → {new_anthropic_model}")
            self.anthropic_api_key = new_anthropic_key
            self.anthropic_model = new_anthropic_model

    async def classify_drawing(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        provider: Optional[str] = None
    ) -> ClassificationResult:
        """
        도면 분류 실행

        Args:
            image_path: 이미지 파일 경로
            image_base64: Base64 인코딩된 이미지
            provider: 사용할 프로바이더 (local, openai, anthropic)

        Returns:
            ClassificationResult: 분류 결과
        """
        # Dashboard 설정 변경 반영
        self.refresh_credentials()

        # 이미지 준비
        if image_path and not image_base64:
            image_base64 = self._encode_image(image_path)

        if not image_base64:
            return self._fallback_result("이미지가 제공되지 않았습니다")

        # 프로바이더 선택
        provider = provider or self.default_provider
        providers_to_try = [provider]

        # 폴백 순서 설정
        if provider == "local":
            providers_to_try.extend(["openai", "anthropic"])
        elif provider == "openai":
            providers_to_try.extend(["anthropic", "local"])
        else:
            providers_to_try.extend(["openai", "local"])

        # 순차적으로 시도
        last_error = None
        for p in providers_to_try:
            try:
                if p == "local":
                    result = await self._classify_with_local(image_base64)
                elif p == "openai" and self.openai_api_key:
                    result = await self._classify_with_openai(image_base64)
                elif p == "anthropic" and self.anthropic_api_key:
                    result = await self._classify_with_anthropic(image_base64)
                else:
                    continue

                if result:
                    result.provider = p
                    return result

            except Exception as e:
                last_error = str(e)
                logger.warning(f"[VLMClassifier] {p} 실패: {e}")
                continue

        return self._fallback_result(f"모든 프로바이더 실패: {last_error}")

    async def _classify_with_local(self, image_base64: str) -> Optional[ClassificationResult]:
        """로컬 VL API 사용"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 헬스체크
            try:
                health = await client.get(f"{self.local_vl_url}/api/v1/health")
                if health.status_code != 200:
                    logger.warning(f"[VLMClassifier] Local VL API health check failed: {health.status_code}")
                    return None
            except Exception as e:
                logger.warning(f"[VLMClassifier] Local VL API health check error: {e}")
                return None

            # Base64를 바이너리로 디코딩
            try:
                image_bytes = base64.b64decode(image_base64)
            except Exception as e:
                logger.error(f"[VLMClassifier] Failed to decode base64 image: {e}")
                return None

            # 분류 요청 (multipart/form-data)
            # BLIP 모델은 512 토큰 제한이 있으므로 간단한 프롬프트 사용
            files = {
                "file": ("image.png", image_bytes, "image/png")
            }
            data = {
                "prompt": "What type of engineering drawing is this? Is it a mechanical part drawing, P&ID, assembly drawing, electrical schematic, or architectural drawing?",
                "model": "blip-base",
                "temperature": 0.1
            }

            response = await client.post(
                f"{self.local_vl_url}/api/v1/analyze",
                files=files,
                data=data
            )

            if response.status_code != 200:
                logger.error(f"[VLMClassifier] Local VL API error: {response.status_code} - {response.text}")
                return None

            result = response.json()
            # VL API는 VQA 모드에서 'answer', 캡셔닝 모드에서 'caption' 반환
            raw_response = result.get("answer") or result.get("caption") or result.get("response") or ""

            if not raw_response:
                logger.warning(f"[VLMClassifier] VL API returned empty response: {result}")
                return None

            # BLIP 모델은 단순 캡션만 반환하므로 기본 분류 시도
            return self._parse_blip_response(raw_response, "local")

    async def _classify_with_openai(self, image_base64: str) -> Optional[ClassificationResult]:
        """OpenAI GPT-4V 사용 (gpt-4o-mini, gpt-4o, gpt-4-turbo 지원)"""
        logger.info(f"[VLMClassifier] OpenAI API 호출 - 모델: {self.openai_model}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.openai_model,  # 환경변수 또는 기본값 (gpt-4o-mini)
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": CLASSIFICATION_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.1
                }
            )

            if response.status_code != 200:
                return None

            data = response.json()
            raw_response = data["choices"][0]["message"]["content"]

            return self._parse_response(raw_response, "openai")

    async def _classify_with_anthropic(self, image_base64: str) -> Optional[ClassificationResult]:
        """Anthropic Claude Vision 사용"""
        logger.info(f"[VLMClassifier] Anthropic API 호출 - 모델: {self.anthropic_model}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.anthropic_api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": self.anthropic_model,  # Dashboard 설정 또는 기본값
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": image_base64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": CLASSIFICATION_PROMPT
                                }
                            ]
                        }
                    ]
                }
            )

            if response.status_code != 200:
                return None

            data = response.json()
            raw_response = data["content"][0]["text"]

            return self._parse_response(raw_response, "anthropic")

    def _parse_response(self, raw_response: str, provider: str) -> ClassificationResult:
        """응답 파싱"""
        try:
            # JSON 추출 (코드 블록 내부 또는 전체)
            json_str = raw_response
            if "```json" in raw_response:
                json_str = raw_response.split("```json")[1].split("```")[0]
            elif "```" in raw_response:
                json_str = raw_response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            # 영역 파싱
            regions = []
            for r in data.get("regions", []):
                try:
                    regions.append(DetectedRegion(
                        region_type=RegionType(r.get("region_type", "main_view")),
                        bbox=r.get("bbox", [0, 0, 1, 1]),
                        confidence=r.get("confidence", 0.5),
                        description=r.get("description")
                    ))
                except ValueError:
                    continue

            # 결과 생성
            return ClassificationResult(
                drawing_type=DrawingType(data.get("drawing_type", "unknown")),
                confidence=data.get("confidence", 0.5),
                suggested_preset=data.get("suggested_preset", "general"),
                regions=regions,
                analysis_notes=data.get("analysis_notes", ""),
                provider=provider,
                raw_response=raw_response
            )

        except Exception as e:
            logger.error(f"[VLMClassifier] 응답 파싱 실패: {e}")
            return self._fallback_result(f"응답 파싱 실패: {e}")

    def _parse_blip_response(self, caption: str, provider: str) -> ClassificationResult:
        """BLIP 모델의 간단한 캡션 응답을 분류 결과로 변환"""
        if not caption:
            return self._fallback_result("VL API 응답이 비어있습니다")

        caption_lower = caption.lower()

        # 키워드 기반 분류
        drawing_type = DrawingType.UNKNOWN
        confidence = 0.6
        suggested_preset = "general"

        # 기계 부품도 키워드
        mechanical_keywords = [
            "mechanical", "part", "component", "machine", "shaft",
            "bearing", "gear", "dimension", "tolerance", "drawing",
            "engineering", "technical", "blueprint", "specification",
            "기계", "부품", "치수", "도면", "설계"
        ]

        # P&ID 키워드
        pid_keywords = [
            "pipe", "piping", "valve", "instrument", "p&id", "pid",
            "flow", "process", "diagram", "tank", "pump", "배관", "밸브"
        ]

        # 조립도 키워드
        assembly_keywords = [
            "assembly", "assembled", "exploded", "parts list",
            "조립", "분해도", "부품목록"
        ]

        # 전기 회로도 키워드
        electrical_keywords = [
            "electrical", "circuit", "wiring", "schematic",
            "전기", "회로", "배선"
        ]

        # 건축 키워드
        architectural_keywords = [
            "architectural", "floor plan", "building", "construction",
            "건축", "평면도", "입면도"
        ]

        # 매칭 점수 계산
        scores = {
            DrawingType.MECHANICAL_PART: sum(1 for kw in mechanical_keywords if kw in caption_lower),
            DrawingType.PID: sum(1 for kw in pid_keywords if kw in caption_lower),
            DrawingType.ASSEMBLY: sum(1 for kw in assembly_keywords if kw in caption_lower),
            DrawingType.ELECTRICAL: sum(1 for kw in electrical_keywords if kw in caption_lower),
            DrawingType.ARCHITECTURAL: sum(1 for kw in architectural_keywords if kw in caption_lower),
        }

        # 가장 높은 점수의 타입 선택
        max_score = max(scores.values())
        if max_score > 0:
            for dt, score in scores.items():
                if score == max_score:
                    drawing_type = dt
                    confidence = min(0.5 + score * 0.1, 0.85)  # 점수에 따라 신뢰도 조정
                    break

        # 프리셋 매핑
        preset_map = {
            DrawingType.MECHANICAL_PART: "dimension_extraction",
            DrawingType.PID: "pid_analysis",
            DrawingType.ASSEMBLY: "assembly_analysis",
            DrawingType.ELECTRICAL: "electrical_analysis",
            DrawingType.ARCHITECTURAL: "architectural_analysis",
            DrawingType.UNKNOWN: "general"
        }
        suggested_preset = preset_map.get(drawing_type, "general")

        return ClassificationResult(
            drawing_type=drawing_type,
            confidence=confidence,
            suggested_preset=suggested_preset,
            regions=[],
            analysis_notes=f"BLIP 캡션 기반 분류: {caption[:100]}...",
            provider=provider,
            raw_response=caption
        )

    def _encode_image(self, image_path: str) -> str:
        """이미지 파일을 Base64로 인코딩"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _fallback_result(self, reason: str) -> ClassificationResult:
        """폴백 결과 생성"""
        return ClassificationResult(
            drawing_type=DrawingType.UNKNOWN,
            confidence=0.0,
            suggested_preset="general",
            regions=[],
            analysis_notes=f"자동 분류 실패: {reason}. 수동 분류가 필요합니다.",
            provider="fallback"
        )


# 싱글톤 인스턴스
vlm_classifier = VLMClassifier()


# 프리셋별 파이프라인 설정
PRESET_PIPELINES = {
    "dimension_extraction": {
        "name": "치수 추출 파이프라인",
        "description": "기계 부품도의 치수 및 공차 추출에 최적화",
        "nodes": ["yolo", "edocr2", "skinmodel"],
        "yolo_confidence": 0.25,
        "ocr_engine": "edocr2",
        "enable_tolerance_analysis": True
    },
    "pid_analysis": {
        "name": "P&ID 분석 파이프라인",
        "description": "배관계장도의 심볼 및 연결 분석",
        "nodes": ["yolo", "line_detector", "pid_analyzer"],
        "yolo_model_type": "pid_class_aware",
        "yolo_confidence": 0.15,
        "enable_connectivity": True,
        "enable_bom": True
    },
    "assembly_analysis": {
        "name": "조립도 분석 파이프라인",
        "description": "조립도의 부품 식별 및 관계 분석",
        "nodes": ["yolo", "edocr2", "vl"],
        "yolo_confidence": 0.30,
        "enable_part_matching": True
    },
    "electrical_analysis": {
        "name": "전기 회로 분석 파이프라인",
        "description": "전기 회로도의 심볼 및 연결 분석",
        "nodes": ["yolo", "ocr_ensemble"],
        "yolo_confidence": 0.20,
        "enable_circuit_analysis": True
    },
    "architectural_analysis": {
        "name": "건축 도면 분석 파이프라인",
        "description": "건축 도면의 요소 추출",
        "nodes": ["edgnet", "ocr_ensemble"],
        "enable_floor_plan_analysis": True
    },
    "general": {
        "name": "일반 분석 파이프라인",
        "description": "범용 도면 분석",
        "nodes": ["yolo", "ocr_ensemble"],
        "yolo_confidence": 0.25
    }
}


def get_preset_config(preset_name: str) -> Dict[str, Any]:
    """프리셋 설정 조회"""
    return PRESET_PIPELINES.get(preset_name, PRESET_PIPELINES["general"])
