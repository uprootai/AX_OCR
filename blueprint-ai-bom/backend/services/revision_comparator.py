"""리비전 비교 서비스 (Revision Comparison Service)

두 도면 리비전 간 변경점 감지 및 비교 분석
- 이미지 기반 구조적 비교 (SSIM)
- 세션 데이터 기반 상세 비교 (심볼, 치수, 노트)
- VLM 기반 지능형 비교 (선택적)

구현일: 2025-12-27
"""

import os
import base64
import logging
import uuid
import json
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================
# Enums & Data Classes
# ============================================================

class ChangeType(str, Enum):
    """변경 타입"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"
    UNCHANGED = "unchanged"


class ChangeCategory(str, Enum):
    """변경 카테고리"""
    GEOMETRY = "geometry"
    DIMENSION = "dimension"
    TOLERANCE = "tolerance"
    NOTE = "note"
    SYMBOL = "symbol"
    ANNOTATION = "annotation"
    TITLE_BLOCK = "title_block"
    OTHER = "other"


class Severity(str, Enum):
    """변경 중요도"""
    CRITICAL = "critical"  # 치수, 공차 변경
    WARNING = "warning"    # 심볼, 노트 변경
    INFO = "info"          # 기타 변경


@dataclass
class RevisionChange:
    """개별 변경 항목"""
    id: str
    change_type: ChangeType
    category: ChangeCategory
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    bbox_old: Optional[List[float]] = None
    bbox_new: Optional[List[float]] = None
    confidence: float = 0.0
    severity: Severity = Severity.INFO
    item_id: Optional[str] = None  # 관련 심볼/치수 ID


@dataclass
class ComparisonResult:
    """비교 결과"""
    comparison_id: str
    session_id_old: str
    session_id_new: str
    changes: List[RevisionChange] = field(default_factory=list)
    total_changes: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    added_count: int = 0
    removed_count: int = 0
    modified_count: int = 0
    alignment_score: float = 0.0
    similarity_score: float = 0.0
    diff_image_base64: Optional[str] = None
    overlay_image_base64: Optional[str] = None
    provider: str = "opencv"
    processing_time_ms: float = 0.0


# ============================================================
# VLM Comparison Prompt
# ============================================================

COMPARISON_PROMPT = """당신은 기계 도면 리비전 비교 전문가입니다.
두 도면 이미지를 비교하여 변경점을 찾아 JSON 형식으로 반환하세요.

## 비교 대상

### 1. 치수 변경 (DIMENSION) - CRITICAL
- 값 변경: 10mm → 12mm
- 공차 변경: ±0.1 → ±0.05
- 단위 변경: mm → inch

### 2. 심볼 변경 (SYMBOL) - WARNING
- 추가된 심볼
- 삭제된 심볼
- 변경된 심볼 (위치, 크기, 타입)

### 3. 노트 변경 (NOTE) - WARNING
- 재료 사양 변경
- 열처리 조건 변경
- 표면 처리 변경
- 일반 공차 변경

### 4. 형상 변경 (GEOMETRY) - CRITICAL
- 외형 변경
- 홀 추가/삭제
- 피처 수정

### 5. 표제란 변경 (TITLE_BLOCK) - INFO
- 도면 번호 변경
- 리비전 번호 변경
- 작성일 변경

## 응답 형식 (JSON)

```json
{
  "changes": [
    {
      "change_type": "modified",
      "category": "dimension",
      "description": "길이 치수 10mm → 12mm 변경",
      "old_value": "10mm",
      "new_value": "12mm",
      "bbox_old": [0.3, 0.4, 0.35, 0.45],
      "bbox_new": [0.3, 0.4, 0.35, 0.45],
      "severity": "critical"
    }
  ],
  "summary": "3개 치수 변경, 1개 노트 추가",
  "similarity_score": 0.85
}
```

첫 번째 이미지가 이전 리비전, 두 번째 이미지가 새 리비전입니다.
변경점을 상세히 분석해주세요. JSON만 반환하세요."""


class RevisionComparator:
    """리비전 비교 서비스"""

    # OpenAI API
    OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._cv2 = None
        self._skimage = None

    @property
    def cv2(self):
        """OpenCV 지연 로딩"""
        if self._cv2 is None:
            try:
                import cv2
                self._cv2 = cv2
            except ImportError:
                logger.warning("[RevisionComparator] OpenCV not available")
        return self._cv2

    @property
    def skimage(self):
        """scikit-image 지연 로딩"""
        if self._skimage is None:
            try:
                from skimage import metrics
                self._skimage = metrics
            except ImportError:
                logger.warning("[RevisionComparator] scikit-image not available")
        return self._skimage

    async def compare_revisions(
        self,
        session_old: Dict[str, Any],
        session_new: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> ComparisonResult:
        """두 리비전 비교

        Args:
            session_old: 이전 세션 데이터
            session_new: 새 세션 데이터
            config: 비교 설정
                - use_vlm: VLM 사용 여부 (기본: False)
                - compare_dimensions: 치수 비교 (기본: True)
                - compare_symbols: 심볼 비교 (기본: True)
                - compare_notes: 노트 비교 (기본: True)
                - pixel_threshold: 픽셀 차이 임계값 (기본: 10)

        Returns:
            ComparisonResult
        """
        config = config or {}
        use_vlm = config.get("use_vlm", False)

        comparison_id = str(uuid.uuid4())
        session_id_old = session_old.get("session_id", "unknown")
        session_id_new = session_new.get("session_id", "unknown")

        changes: List[RevisionChange] = []
        alignment_score = 0.0
        similarity_score = 0.0
        diff_image_base64 = None
        provider = "data_compare"

        # 1. 이미지 기반 비교 (OpenCV 사용 가능 시)
        image_old = self._get_image_from_session(session_old)
        image_new = self._get_image_from_session(session_new)

        if image_old is not None and image_new is not None:
            try:
                similarity_score, diff_image = self._compare_images_ssim(
                    image_old, image_new
                )
                if diff_image is not None:
                    diff_image_base64 = self._encode_image_base64(diff_image)
                provider = "opencv"
                logger.info(f"[RevisionComparator] 이미지 유사도: {similarity_score:.2%}")
            except Exception as e:
                logger.warning(f"[RevisionComparator] 이미지 비교 실패: {e}")

        # 2. VLM 기반 비교 (선택적)
        if use_vlm and self.openai_api_key:
            try:
                vlm_changes = await self._compare_with_vlm(session_old, session_new)
                changes.extend(vlm_changes)
                provider = "openai_vlm"
                logger.info(f"[RevisionComparator] VLM 변경점: {len(vlm_changes)}개")
            except Exception as e:
                logger.warning(f"[RevisionComparator] VLM 비교 실패: {e}")

        # 3. 데이터 기반 비교 (항상 수행)
        try:
            data_changes = self._compare_session_data(
                session_old, session_new, config
            )
            changes.extend(data_changes)
            logger.info(f"[RevisionComparator] 데이터 변경점: {len(data_changes)}개")
        except Exception as e:
            logger.warning(f"[RevisionComparator] 데이터 비교 실패: {e}")

        # 중복 제거 및 집계
        changes = self._deduplicate_changes(changes)
        by_type = self._count_by_field(changes, "change_type")
        by_category = self._count_by_field(changes, "category")

        return ComparisonResult(
            comparison_id=comparison_id,
            session_id_old=session_id_old,
            session_id_new=session_id_new,
            changes=changes,
            total_changes=len(changes),
            by_type=by_type,
            by_category=by_category,
            added_count=by_type.get("added", 0),
            removed_count=by_type.get("removed", 0),
            modified_count=by_type.get("modified", 0),
            alignment_score=alignment_score,
            similarity_score=similarity_score,
            diff_image_base64=diff_image_base64,
            provider=provider,
        )

    def _get_image_from_session(
        self, session: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """세션에서 이미지 로드"""
        if self.cv2 is None:
            return None

        # base64 이미지
        image_base64 = session.get("image_base64")
        if image_base64:
            try:
                img_data = base64.b64decode(image_base64)
                nparr = np.frombuffer(img_data, np.uint8)
                return self.cv2.imdecode(nparr, self.cv2.IMREAD_COLOR)
            except Exception as e:
                logger.warning(f"[RevisionComparator] base64 이미지 디코드 실패: {e}")

        # 파일 경로
        image_path = session.get("image_path")
        if image_path and Path(image_path).exists():
            try:
                return self.cv2.imread(str(image_path))
            except Exception as e:
                logger.warning(f"[RevisionComparator] 이미지 파일 로드 실패: {e}")

        return None

    def _compare_images_ssim(
        self,
        image_old: np.ndarray,
        image_new: np.ndarray
    ) -> Tuple[float, Optional[np.ndarray]]:
        """SSIM 기반 이미지 비교"""
        if self.cv2 is None:
            return 0.0, None

        # 크기 맞추기
        h1, w1 = image_old.shape[:2]
        h2, w2 = image_new.shape[:2]

        if (h1, w1) != (h2, w2):
            # 더 큰 크기로 맞춤
            target_h = max(h1, h2)
            target_w = max(w1, w2)
            image_old = self.cv2.resize(image_old, (target_w, target_h))
            image_new = self.cv2.resize(image_new, (target_w, target_h))

        # 그레이스케일 변환
        gray_old = self.cv2.cvtColor(image_old, self.cv2.COLOR_BGR2GRAY)
        gray_new = self.cv2.cvtColor(image_new, self.cv2.COLOR_BGR2GRAY)

        # SSIM 계산
        ssim_score = 0.0
        if self.skimage is not None:
            try:
                ssim_score = self.skimage.structural_similarity(
                    gray_old, gray_new, full=False
                )
            except Exception:
                pass

        # 차이 이미지 생성
        diff = self.cv2.absdiff(gray_old, gray_new)
        _, diff_thresh = self.cv2.threshold(diff, 30, 255, self.cv2.THRESH_BINARY)

        # 컬러 차이 이미지 생성 (변경 부분 빨간색)
        diff_colored = self.cv2.cvtColor(gray_new, self.cv2.COLOR_GRAY2BGR)
        diff_colored[diff_thresh > 0] = [0, 0, 255]  # 빨간색

        return ssim_score, diff_colored

    def _encode_image_base64(self, image: np.ndarray) -> str:
        """이미지를 base64로 인코딩"""
        if self.cv2 is None:
            return ""
        _, buffer = self.cv2.imencode('.png', image)
        return base64.b64encode(buffer).decode('utf-8')

    async def _compare_with_vlm(
        self,
        session_old: Dict[str, Any],
        session_new: Dict[str, Any]
    ) -> List[RevisionChange]:
        """VLM을 사용한 지능형 비교"""
        import httpx

        changes: List[RevisionChange] = []

        # 이미지 준비
        image_old_b64 = session_old.get("image_base64")
        image_new_b64 = session_new.get("image_base64")

        # 파일에서 로드
        if not image_old_b64:
            image_path = session_old.get("image_path")
            if image_path and Path(image_path).exists():
                with open(image_path, "rb") as f:
                    image_old_b64 = base64.b64encode(f.read()).decode("utf-8")

        if not image_new_b64:
            image_path = session_new.get("image_path")
            if image_path and Path(image_path).exists():
                with open(image_path, "rb") as f:
                    image_new_b64 = base64.b64encode(f.read()).decode("utf-8")

        if not image_old_b64 or not image_new_b64:
            logger.warning("[RevisionComparator] VLM 비교를 위한 이미지가 없습니다")
            return changes

        # OpenAI API 호출
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
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
                                    {"type": "text", "text": COMPARISON_PROMPT},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_old_b64}"
                                        }
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_new_b64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 2000
                    }
                )
                response.raise_for_status()
                result = response.json()

                # 응답 파싱
                content = result["choices"][0]["message"]["content"]
                changes = self._parse_vlm_response(content)

        except Exception as e:
            logger.error(f"[RevisionComparator] VLM API 호출 실패: {e}")

        return changes

    def _parse_vlm_response(self, content: str) -> List[RevisionChange]:
        """VLM 응답 파싱"""
        changes: List[RevisionChange] = []

        try:
            # JSON 추출
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)

                for item in data.get("changes", []):
                    change = RevisionChange(
                        id=str(uuid.uuid4())[:8],
                        change_type=ChangeType(item.get("change_type", "modified")),
                        category=ChangeCategory(item.get("category", "other")),
                        description=item.get("description", ""),
                        old_value=item.get("old_value"),
                        new_value=item.get("new_value"),
                        bbox_old=item.get("bbox_old"),
                        bbox_new=item.get("bbox_new"),
                        confidence=0.85,  # VLM 기본 신뢰도
                        severity=Severity(item.get("severity", "info")),
                    )
                    changes.append(change)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"[RevisionComparator] VLM 응답 파싱 실패: {e}")

        return changes

    def _compare_session_data(
        self,
        session_old: Dict[str, Any],
        session_new: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[RevisionChange]:
        """세션 데이터 기반 비교"""
        changes: List[RevisionChange] = []

        compare_dimensions = config.get("compare_dimensions", True)
        compare_symbols = config.get("compare_symbols", True)
        compare_notes = config.get("compare_notes", True)

        # 1. 심볼 비교
        if compare_symbols:
            symbol_changes = self._compare_symbols(
                session_old.get("symbols", []),
                session_new.get("symbols", [])
            )
            changes.extend(symbol_changes)

        # 2. 치수 비교
        if compare_dimensions:
            dimension_changes = self._compare_dimensions(
                session_old.get("dimensions", []),
                session_new.get("dimensions", [])
            )
            changes.extend(dimension_changes)

        # 3. 노트 비교
        if compare_notes:
            note_changes = self._compare_notes(
                session_old.get("notes_extraction", {}),
                session_new.get("notes_extraction", {})
            )
            changes.extend(note_changes)

        return changes

    def _compare_symbols(
        self,
        symbols_old: List[Dict[str, Any]],
        symbols_new: List[Dict[str, Any]]
    ) -> List[RevisionChange]:
        """심볼 비교"""
        changes: List[RevisionChange] = []

        # ID 기반 매칭
        old_ids = {s.get("id", str(i)): s for i, s in enumerate(symbols_old)}
        new_ids = {s.get("id", str(i)): s for i, s in enumerate(symbols_new)}

        # 추가된 심볼
        for sym_id, sym in new_ids.items():
            if sym_id not in old_ids:
                changes.append(RevisionChange(
                    id=f"sym_add_{sym_id[:8]}",
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.SYMBOL,
                    description=f"심볼 추가: {sym.get('class_name', 'unknown')}",
                    new_value=sym.get("class_name"),
                    bbox_new=sym.get("bbox"),
                    confidence=sym.get("confidence", 0.8),
                    severity=Severity.WARNING,
                    item_id=sym_id,
                ))

        # 삭제된 심볼
        for sym_id, sym in old_ids.items():
            if sym_id not in new_ids:
                changes.append(RevisionChange(
                    id=f"sym_del_{sym_id[:8]}",
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.SYMBOL,
                    description=f"심볼 삭제: {sym.get('class_name', 'unknown')}",
                    old_value=sym.get("class_name"),
                    bbox_old=sym.get("bbox"),
                    confidence=sym.get("confidence", 0.8),
                    severity=Severity.WARNING,
                    item_id=sym_id,
                ))

        # 수정된 심볼 (클래스 변경)
        for sym_id in set(old_ids.keys()) & set(new_ids.keys()):
            old_sym = old_ids[sym_id]
            new_sym = new_ids[sym_id]

            old_class = old_sym.get("class_name", "")
            new_class = new_sym.get("class_name", "")

            if old_class != new_class:
                changes.append(RevisionChange(
                    id=f"sym_mod_{sym_id[:8]}",
                    change_type=ChangeType.MODIFIED,
                    category=ChangeCategory.SYMBOL,
                    description=f"심볼 변경: {old_class} → {new_class}",
                    old_value=old_class,
                    new_value=new_class,
                    bbox_old=old_sym.get("bbox"),
                    bbox_new=new_sym.get("bbox"),
                    confidence=0.9,
                    severity=Severity.WARNING,
                    item_id=sym_id,
                ))

        return changes

    def _compare_dimensions(
        self,
        dims_old: List[Dict[str, Any]],
        dims_new: List[Dict[str, Any]]
    ) -> List[RevisionChange]:
        """치수 비교"""
        changes: List[RevisionChange] = []

        # 값 기반 매칭 (위치 근접성 고려)
        old_map = {d.get("value", ""): d for d in dims_old if d.get("value")}
        new_map = {d.get("value", ""): d for d in dims_new if d.get("value")}

        # 추가된 치수
        for val, dim in new_map.items():
            if val not in old_map:
                changes.append(RevisionChange(
                    id=f"dim_add_{uuid.uuid4().hex[:8]}",
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.DIMENSION,
                    description=f"치수 추가: {val}",
                    new_value=val,
                    bbox_new=dim.get("bbox"),
                    confidence=dim.get("confidence", 0.8),
                    severity=Severity.CRITICAL,
                ))

        # 삭제된 치수
        for val, dim in old_map.items():
            if val not in new_map:
                changes.append(RevisionChange(
                    id=f"dim_del_{uuid.uuid4().hex[:8]}",
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.DIMENSION,
                    description=f"치수 삭제: {val}",
                    old_value=val,
                    bbox_old=dim.get("bbox"),
                    confidence=dim.get("confidence", 0.8),
                    severity=Severity.CRITICAL,
                ))

        return changes

    def _compare_notes(
        self,
        notes_old: Dict[str, Any],
        notes_new: Dict[str, Any]
    ) -> List[RevisionChange]:
        """노트 비교"""
        changes: List[RevisionChange] = []

        old_list = notes_old.get("notes", [])
        new_list = notes_new.get("notes", [])

        # 텍스트 기반 매칭
        old_texts = {n.get("text", ""): n for n in old_list if n.get("text")}
        new_texts = {n.get("text", ""): n for n in new_list if n.get("text")}

        # 추가된 노트
        for text, note in new_texts.items():
            if text not in old_texts:
                cat = note.get("category", "general")
                changes.append(RevisionChange(
                    id=f"note_add_{uuid.uuid4().hex[:8]}",
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.NOTE,
                    description=f"노트 추가 ({cat}): {text[:50]}...",
                    new_value=text,
                    bbox_new=note.get("bbox"),
                    confidence=note.get("confidence", 0.8),
                    severity=Severity.WARNING,
                ))

        # 삭제된 노트
        for text, note in old_texts.items():
            if text not in new_texts:
                cat = note.get("category", "general")
                changes.append(RevisionChange(
                    id=f"note_del_{uuid.uuid4().hex[:8]}",
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.NOTE,
                    description=f"노트 삭제 ({cat}): {text[:50]}...",
                    old_value=text,
                    bbox_old=note.get("bbox"),
                    confidence=note.get("confidence", 0.8),
                    severity=Severity.WARNING,
                ))

        # 재료, 공차 등 구조화된 데이터 비교
        old_materials = set(notes_old.get("materials", []) or [])
        new_materials = set(notes_new.get("materials", []) or [])

        for mat in new_materials - old_materials:
            if isinstance(mat, dict):
                mat_name = mat.get("name", str(mat))
            else:
                mat_name = str(mat)
            changes.append(RevisionChange(
                id=f"mat_add_{uuid.uuid4().hex[:8]}",
                change_type=ChangeType.ADDED,
                category=ChangeCategory.NOTE,
                description=f"재료 추가: {mat_name}",
                new_value=mat_name,
                confidence=0.9,
                severity=Severity.CRITICAL,
            ))

        for mat in old_materials - new_materials:
            if isinstance(mat, dict):
                mat_name = mat.get("name", str(mat))
            else:
                mat_name = str(mat)
            changes.append(RevisionChange(
                id=f"mat_del_{uuid.uuid4().hex[:8]}",
                change_type=ChangeType.REMOVED,
                category=ChangeCategory.NOTE,
                description=f"재료 삭제: {mat_name}",
                old_value=mat_name,
                confidence=0.9,
                severity=Severity.CRITICAL,
            ))

        return changes

    def _deduplicate_changes(
        self, changes: List[RevisionChange]
    ) -> List[RevisionChange]:
        """중복 변경 제거"""
        seen = set()
        unique = []
        for change in changes:
            key = (change.change_type, change.category, change.description)
            if key not in seen:
                seen.add(key)
                unique.append(change)
        return unique

    def _count_by_field(
        self,
        changes: List[RevisionChange],
        field: str
    ) -> Dict[str, int]:
        """필드별 카운트"""
        counts: Dict[str, int] = {}
        for change in changes:
            val = getattr(change, field, None)
            if val:
                if isinstance(val, Enum):
                    val = val.value
                counts[val] = counts.get(val, 0) + 1
        return counts


# 싱글톤 인스턴스
revision_comparator = RevisionComparator()
