"""노트/주석 추출 서비스 (Phase 4)

도면에서 일반 노트, 재료 사양, 열처리, 표면 처리 등을 추출합니다.
OCR + LLM 조합으로 텍스트를 추출하고 카테고리별로 분류합니다.

지원 프로바이더:
- OpenAI GPT-4o-mini (기본, 비용 효율적)
- OpenAI GPT-4o (고품질)
- Anthropic Claude Vision
- 로컬 VL API + OCR
"""
import os
import re
import json
import logging
import uuid
import base64
import httpx
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class NoteCategory(str, Enum):
    """노트 카테고리"""
    MATERIAL = "material"                   # 재료 사양
    HEAT_TREATMENT = "heat_treatment"       # 열처리
    SURFACE_FINISH = "surface_finish"       # 표면 처리/도금
    TOLERANCE = "tolerance"                 # 일반 공차
    ASSEMBLY = "assembly"                   # 조립 지시
    INSPECTION = "inspection"               # 검사 요구
    WELDING = "welding"                     # 용접 사양
    PAINTING = "painting"                   # 도장 사양
    STANDARD = "standard"                   # 적용 규격
    GENERAL = "general"                     # 일반 노트


@dataclass
class ExtractedNote:
    """추출된 노트"""
    id: str
    category: NoteCategory
    text: str
    confidence: float
    bbox: Optional[List[float]] = None  # [x1, y1, x2, y2] normalized
    source: str = "llm"  # llm, ocr, manual
    verified: bool = False
    parsed_data: Optional[Dict[str, Any]] = None  # 구조화된 데이터


@dataclass
class NotesExtractionResult:
    """노트 추출 결과"""
    notes: List[ExtractedNote] = field(default_factory=list)
    materials: List[Dict[str, Any]] = field(default_factory=list)
    standards: List[str] = field(default_factory=list)
    tolerances: Dict[str, Any] = field(default_factory=dict)
    heat_treatments: List[Dict[str, Any]] = field(default_factory=list)
    surface_finishes: List[Dict[str, Any]] = field(default_factory=list)
    provider: str = "unknown"
    raw_response: Optional[str] = None


# 노트 추출 프롬프트 (한국어 도면 최적화)
NOTES_EXTRACTION_PROMPT = """당신은 기계 도면 분석 전문가입니다. 주어진 도면 이미지에서 노트/주석 영역을 찾아 텍스트를 추출하고 분류하세요.

## 추출 대상

### 노트 카테고리
1. **material**: 재료 사양 - "재질: SUS304", "Material: AISI 1045", "SM45C"
2. **heat_treatment**: 열처리 - "열처리: HRC 58-62", "침탄 경화", "담금질"
3. **surface_finish**: 표면 처리 - "무전해 니켈도금", "아노다이징", "크롬 도금"
4. **tolerance**: 일반 공차 - "일반공차: KS B 0401-m", "ISO 2768-mK"
5. **assembly**: 조립 지시 - "접착제 도포 후 조립", "압입", "용접 후 조립"
6. **inspection**: 검사 요구 - "전수검사", "치수검사", "X-ray 검사"
7. **welding**: 용접 사양 - "TIG 용접", "MIG 용접", "용접 후 응력제거"
8. **painting**: 도장 사양 - "분체도장", "전착도장", "RAL 7035"
9. **standard**: 적용 규격 - "KS B ISO 286-1", "JIS G 3101", "ASTM A36"
10. **general**: 기타 일반 노트

### 구조화된 데이터 추출

#### 재료 (materials)
```json
{
  "name": "SUS304",
  "standard": "KS D 3698",
  "grade": "304",
  "form": "PLATE",
  "thickness": "10mm"
}
```

#### 열처리 (heat_treatments)
```json
{
  "type": "침탄 경화",
  "hardness": "HRC 58-62",
  "depth": "0.8-1.2mm",
  "method": "가스 침탄"
}
```

#### 표면 처리 (surface_finishes)
```json
{
  "type": "무전해 니켈도금",
  "thickness": "10-15μm",
  "standard": "KS D 8301"
}
```

#### 일반 공차 (tolerances)
```json
{
  "standard": "KS B 0401",
  "class": "m",
  "linear": "±0.5",
  "angular": "±0°30'"
}
```

## 응답 형식 (JSON)

```json
{
  "notes": [
    {
      "category": "material",
      "text": "재질: SUS304 (KS D 3698)",
      "confidence": 0.95,
      "bbox": [0.02, 0.85, 0.3, 0.88]
    },
    {
      "category": "tolerance",
      "text": "일반공차: KS B 0401-m",
      "confidence": 0.92,
      "bbox": [0.02, 0.88, 0.25, 0.91]
    }
  ],
  "materials": [
    {
      "name": "SUS304",
      "standard": "KS D 3698",
      "grade": "304"
    }
  ],
  "standards": ["KS D 3698", "KS B 0401"],
  "tolerances": {
    "standard": "KS B 0401",
    "class": "m"
  },
  "heat_treatments": [],
  "surface_finishes": []
}
```

## 주의사항
- 노트 영역은 보통 도면 좌하단 또는 표제란 근처에 있습니다
- 한국어, 영어, 일본어 혼합 표기를 인식하세요
- bbox는 normalized 좌표 [x1, y1, x2, y2] (0-1 범위)
- 확실하지 않은 경우 confidence를 낮게 설정하세요

지금 이 도면을 분석해주세요. JSON만 반환하세요."""


class NotesExtractor:
    """노트/주석 추출 서비스"""

    OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
    ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        default_provider: str = "openai",
        openai_model: Optional[str] = None,
    ):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.default_provider = default_provider
        self.openai_model = openai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = 120.0

        logger.info(f"[NotesExtractor] 초기화 - provider: {default_provider}, model: {self.openai_model}")

    async def extract_notes(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        ocr_texts: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[str] = None
    ) -> NotesExtractionResult:
        """
        노트/주석 추출 실행

        Args:
            image_path: 이미지 파일 경로
            image_base64: Base64 인코딩된 이미지
            ocr_texts: 기존 OCR 결과 (있으면 활용)
            provider: 사용할 프로바이더 (openai, anthropic)

        Returns:
            NotesExtractionResult: 추출 결과
        """
        # 이미지 준비
        if image_path and not image_base64:
            image_base64 = self._encode_image(image_path)

        if not image_base64:
            return self._fallback_result("이미지가 제공되지 않았습니다")

        # 프로바이더 선택
        provider = provider or self.default_provider
        providers_to_try = [provider]

        if provider == "openai":
            providers_to_try.append("anthropic")
        else:
            providers_to_try.append("openai")

        # 순차적으로 시도
        last_error = None
        for p in providers_to_try:
            try:
                if p == "openai" and self.openai_api_key:
                    result = await self._extract_with_openai(image_base64, ocr_texts)
                elif p == "anthropic" and self.anthropic_api_key:
                    result = await self._extract_with_anthropic(image_base64, ocr_texts)
                else:
                    continue

                if result:
                    result.provider = p
                    return result

            except Exception as e:
                last_error = str(e)
                logger.warning(f"[NotesExtractor] {p} 실패: {e}")
                continue

        return self._fallback_result(f"모든 프로바이더 실패: {last_error}")

    async def _extract_with_openai(
        self,
        image_base64: str,
        ocr_texts: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[NotesExtractionResult]:
        """OpenAI GPT-4V로 노트 추출"""
        logger.info(f"[NotesExtractor] OpenAI API 호출 - 모델: {self.openai_model}")

        # OCR 텍스트가 있으면 프롬프트에 추가
        prompt = NOTES_EXTRACTION_PROMPT
        if ocr_texts:
            ocr_hint = "\n\n## 참고: 기존 OCR 결과\n"
            for i, text in enumerate(ocr_texts[:20]):  # 최대 20개
                ocr_hint += f"- {text.get('text', '')}\n"
            prompt += ocr_hint

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.openai_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.1
                }
            )

            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"[NotesExtractor] OpenAI API 오류: {response.status_code} - {error_msg}")
                return None

            data = response.json()
            raw_response = data["choices"][0]["message"]["content"]

            return self._parse_response(raw_response, "openai")

    async def _extract_with_anthropic(
        self,
        image_base64: str,
        ocr_texts: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[NotesExtractionResult]:
        """Anthropic Claude로 노트 추출"""
        logger.info("[NotesExtractor] Anthropic API 호출")

        prompt = NOTES_EXTRACTION_PROMPT
        if ocr_texts:
            ocr_hint = "\n\n## 참고: 기존 OCR 결과\n"
            for i, text in enumerate(ocr_texts[:20]):
                ocr_hint += f"- {text.get('text', '')}\n"
            prompt += ocr_hint

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.anthropic_api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4000,
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
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
            )

            if response.status_code != 200:
                logger.error(f"[NotesExtractor] Anthropic API 오류: {response.status_code}")
                return None

            data = response.json()
            raw_response = data["content"][0]["text"]

            return self._parse_response(raw_response, "anthropic")

    def _parse_response(self, raw_response: str, provider: str) -> NotesExtractionResult:
        """응답 파싱"""
        try:
            # JSON 추출
            json_str = raw_response
            if "```json" in raw_response:
                json_str = raw_response.split("```json")[1].split("```")[0]
            elif "```" in raw_response:
                json_str = raw_response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            # 노트 파싱
            notes = []
            for n in data.get("notes", []):
                try:
                    category = NoteCategory(n.get("category", "general"))
                except ValueError:
                    category = NoteCategory.GENERAL

                notes.append(ExtractedNote(
                    id=f"note_{uuid.uuid4().hex[:8]}",
                    category=category,
                    text=n.get("text", ""),
                    confidence=n.get("confidence", 0.5),
                    bbox=n.get("bbox"),
                    source="llm",
                    verified=False,
                    parsed_data=n.get("parsed_data")
                ))

            # 구조화된 데이터 추출
            materials = data.get("materials", [])
            standards = data.get("standards", [])
            tolerances = data.get("tolerances", {})
            heat_treatments = data.get("heat_treatments", [])
            surface_finishes = data.get("surface_finishes", [])

            return NotesExtractionResult(
                notes=notes,
                materials=materials,
                standards=standards,
                tolerances=tolerances,
                heat_treatments=heat_treatments,
                surface_finishes=surface_finishes,
                provider=provider,
                raw_response=raw_response
            )

        except Exception as e:
            logger.error(f"[NotesExtractor] 응답 파싱 실패: {e}")
            return self._fallback_result(f"응답 파싱 실패: {e}")

    def extract_from_ocr_results(
        self,
        ocr_results: List[Dict[str, Any]]
    ) -> NotesExtractionResult:
        """
        OCR 결과에서 규칙 기반으로 노트 추출 (폴백용)

        Args:
            ocr_results: OCR 결과 목록 [{text, bbox, confidence}, ...]

        Returns:
            NotesExtractionResult
        """
        notes = []
        materials = []
        standards = []
        tolerances = {}
        heat_treatments = []
        surface_finishes = []

        # 재료 패턴
        material_patterns = [
            r'재질\s*[:：]\s*(.+)',
            r'MATERIAL\s*[:：]\s*(.+)',
            r'(SUS\d{3}[A-Z]?)',
            r'(SM\d{2}C)',
            r'(S45C|S50C|SCM\d{3})',
            r'(AISI\s*\d{4})',
            r'(AL\s*\d{4})',
        ]

        # 열처리 패턴
        heat_treatment_patterns = [
            r'열처리\s*[:：]\s*(.+)',
            r'HEAT\s*TREAT[A-Z]*\s*[:：]\s*(.+)',
            r'(HRC\s*\d+[-~]\d+)',
            r'(HV\s*\d+)',
            r'(침탄|담금질|뜨임|어닐링|노멀라이징)',
            r'(CARBURIZING|QUENCHING|TEMPERING|ANNEALING)',
        ]

        # 표면처리 패턴
        surface_patterns = [
            r'표면처리\s*[:：]\s*(.+)',
            r'SURFACE\s*[:：]\s*(.+)',
            r'도금\s*[:：]\s*(.+)',
            r'(무전해\s*니켈도금)',
            r'(아노다이징|ANODIZING)',
            r'(크롬\s*도금|CHROME\s*PLAT)',
            r'(흑색\s*산화|블랙\s*옥사이드)',
        ]

        # 공차 패턴
        tolerance_patterns = [
            r'일반\s*공차\s*[:：]\s*(.+)',
            r'GENERAL\s*TOLERANCE\s*[:：]\s*(.+)',
            r'(KS\s*B\s*0401[-\s]*[a-z])',
            r'(ISO\s*2768[-\s]*[a-zA-Z]+)',
            r'(JIS\s*B\s*0401)',
        ]

        # 규격 패턴
        standard_patterns = [
            r'(KS\s*[A-Z]\s*\d+)',
            r'(JIS\s*[A-Z]\s*\d+)',
            r'(ISO\s*\d+)',
            r'(ASTM\s*[A-Z]\d+)',
            r'(ASME\s*[A-Z0-9.]+)',
        ]

        for ocr in ocr_results:
            text = ocr.get("text", "").strip()
            if not text or len(text) < 3:
                continue

            bbox = ocr.get("bbox")
            confidence = ocr.get("confidence", 0.5)

            # 재료 매칭
            for pattern in material_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    notes.append(ExtractedNote(
                        id=f"note_{uuid.uuid4().hex[:8]}",
                        category=NoteCategory.MATERIAL,
                        text=text,
                        confidence=confidence,
                        bbox=bbox,
                        source="ocr"
                    ))
                    materials.append({"name": match.group(1), "raw_text": text})
                    break

            # 열처리 매칭
            for pattern in heat_treatment_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    notes.append(ExtractedNote(
                        id=f"note_{uuid.uuid4().hex[:8]}",
                        category=NoteCategory.HEAT_TREATMENT,
                        text=text,
                        confidence=confidence,
                        bbox=bbox,
                        source="ocr"
                    ))
                    heat_treatments.append({"type": match.group(1), "raw_text": text})
                    break

            # 표면처리 매칭
            for pattern in surface_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    notes.append(ExtractedNote(
                        id=f"note_{uuid.uuid4().hex[:8]}",
                        category=NoteCategory.SURFACE_FINISH,
                        text=text,
                        confidence=confidence,
                        bbox=bbox,
                        source="ocr"
                    ))
                    surface_finishes.append({"type": match.group(1), "raw_text": text})
                    break

            # 공차 매칭
            for pattern in tolerance_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    notes.append(ExtractedNote(
                        id=f"note_{uuid.uuid4().hex[:8]}",
                        category=NoteCategory.TOLERANCE,
                        text=text,
                        confidence=confidence,
                        bbox=bbox,
                        source="ocr"
                    ))
                    tolerances["standard"] = match.group(1)
                    tolerances["raw_text"] = text
                    break

            # 규격 매칭
            for pattern in standard_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    std = match.group(1).strip()
                    if std not in standards:
                        standards.append(std)
                        notes.append(ExtractedNote(
                            id=f"note_{uuid.uuid4().hex[:8]}",
                            category=NoteCategory.STANDARD,
                            text=text,
                            confidence=confidence,
                            bbox=bbox,
                            source="ocr"
                        ))
                    break

        return NotesExtractionResult(
            notes=notes,
            materials=materials,
            standards=standards,
            tolerances=tolerances,
            heat_treatments=heat_treatments,
            surface_finishes=surface_finishes,
            provider="regex"
        )

    def _encode_image(self, image_path: str) -> str:
        """이미지 파일을 Base64로 인코딩"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _fallback_result(self, reason: str) -> NotesExtractionResult:
        """폴백 결과 생성"""
        logger.warning(f"[NotesExtractor] 폴백: {reason}")
        return NotesExtractionResult(
            notes=[],
            materials=[],
            standards=[],
            tolerances={},
            heat_treatments=[],
            surface_finishes=[],
            provider="fallback"
        )


# 싱글톤 인스턴스
notes_extractor = NotesExtractor()
