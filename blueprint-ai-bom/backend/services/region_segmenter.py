"""Region Segmenter Service (Phase 5)

도면 영역 분할 서비스
- 휴리스틱 기반 영역 검출 (표제란, BOM 테이블, 메인 뷰 등)
- VLM 연동 옵션 (Phase 4 VLMClassifier 활용)
- 수동 영역 추가/수정 지원
- 영역별 처리 전략 적용
"""

import os
import uuid
import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# 영역 분할 설정 (환경변수로 커스터마이징 가능)
TITLE_BLOCK_X_RATIO = float(os.environ.get("REGION_TITLE_BLOCK_X", "0.6"))
TITLE_BLOCK_Y_RATIO = float(os.environ.get("REGION_TITLE_BLOCK_Y", "0.8"))
BOM_TABLE_X_RATIO = float(os.environ.get("REGION_BOM_TABLE_X", "0.65"))
BOM_TABLE_Y_END_RATIO = float(os.environ.get("REGION_BOM_TABLE_Y_END", "0.35"))
LEGEND_X_END_RATIO = float(os.environ.get("REGION_LEGEND_X_END", "0.2"))
LEGEND_Y_END_RATIO = float(os.environ.get("REGION_LEGEND_Y_END", "0.3"))
NOTE_X_END_RATIO = float(os.environ.get("REGION_NOTE_X_END", "0.4"))
NOTE_Y_RATIO = float(os.environ.get("REGION_NOTE_Y", "0.75"))
BRIGHTNESS_THRESHOLD = int(os.environ.get("REGION_BRIGHTNESS_THRESHOLD", "10"))
LINE_DIFF_THRESHOLD = int(os.environ.get("REGION_LINE_DIFF_THRESHOLD", "30"))
MIN_TABLE_LINES = int(os.environ.get("REGION_MIN_TABLE_LINES", "3"))
VARIANCE_THRESHOLD = int(os.environ.get("REGION_VARIANCE_THRESHOLD", "2000"))

from schemas.detection import BoundingBox, VerificationStatus
from schemas.region import (
    RegionType,
    ProcessingStrategy,
    REGION_STRATEGY_MAP,
    Region,
    RegionSegmentationConfig,
    RegionSegmentationResult,
    RegionUpdate,
    ManualRegion,
    RegionProcessingResult,
    TitleBlockData,
    ParsedTable,
    TableCell,
)


@dataclass
class RegionDetectionResult:
    """내부 영역 검출 결과"""
    region_type: RegionType
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels
    confidence: float
    source: str = "heuristic"  # heuristic, vlm, manual


class RegionSegmenter:
    """영역 분할 서비스"""

    def __init__(self):
        # 세션별 영역 데이터 저장
        self.session_regions: Dict[str, List[Region]] = {}

        # 표제란 위치 휴리스틱 (정규화 좌표)
        self.title_block_hints = {
            "bottom_right": (0.6, 0.8, 1.0, 1.0),     # 우하단 (가장 흔함)
            "bottom_full": (0.0, 0.85, 1.0, 1.0),    # 하단 전체
            "right_side": (0.75, 0.0, 1.0, 1.0),     # 우측 전체
        }

        # BOM 테이블 위치 휴리스틱
        self.bom_table_hints = {
            "top_right": (0.6, 0.0, 1.0, 0.25),
            "right_side": (0.75, 0.0, 1.0, 0.5),
        }

    async def segment(
        self,
        session_id: str,
        image_path: str,
        config: Optional[RegionSegmentationConfig] = None,
        use_vlm: bool = False
    ) -> RegionSegmentationResult:
        """
        도면 영역 분할 실행

        Args:
            session_id: 세션 ID
            image_path: 이미지 파일 경로
            config: 분할 설정
            use_vlm: VLM 사용 여부 (Phase 4 연동)

        Returns:
            RegionSegmentationResult: 분할 결과
        """
        start_time = time.time()
        config = config or RegionSegmentationConfig()

        # 이미지 로드
        try:
            image = Image.open(image_path)
            image_width, image_height = image.size
        except Exception as e:
            raise ValueError(f"이미지 로드 실패: {e}")

        # 영역 검출
        detected_regions: List[RegionDetectionResult] = []

        # 1. 휴리스틱 기반 영역 검출
        heuristic_regions = self._detect_regions_heuristic(
            image, image_width, image_height, config
        )
        detected_regions.extend(heuristic_regions)

        # 2. VLM 기반 영역 검출 (옵션)
        if use_vlm:
            try:
                vlm_regions = await self._detect_regions_vlm(image_path)
                # VLM 결과 병합 (높은 신뢰도 우선)
                detected_regions = self._merge_regions(detected_regions, vlm_regions)
            except Exception as e:
                logger.warning(f"[RegionSegmenter] VLM 영역 검출 실패: {e}")

        # 3. 겹치는 영역 처리
        if config.merge_overlapping:
            detected_regions = self._merge_overlapping_regions(
                detected_regions, config.overlap_threshold
            )

        # 4. Region 객체로 변환
        regions = []
        region_stats: Dict[str, int] = {}

        for det in detected_regions:
            if det.confidence < config.confidence_threshold:
                continue

            # 처리 전략 자동 할당
            strategy = ProcessingStrategy.SKIP
            if config.auto_assign_strategy:
                strategy = REGION_STRATEGY_MAP.get(
                    det.region_type, ProcessingStrategy.SKIP
                )

            # 정규화 좌표 계산
            bbox_normalized = [
                det.bbox[0] / image_width,
                det.bbox[1] / image_height,
                det.bbox[2] / image_width,
                det.bbox[3] / image_height,
            ]

            region = Region(
                id=str(uuid.uuid4()),
                region_type=det.region_type,
                bbox=BoundingBox(
                    x1=det.bbox[0],
                    y1=det.bbox[1],
                    x2=det.bbox[2],
                    y2=det.bbox[3]
                ),
                confidence=det.confidence,
                bbox_normalized=bbox_normalized,
                processing_strategy=strategy,
                verification_status=VerificationStatus.PENDING,
            )
            regions.append(region)

            # 통계 업데이트
            type_name = det.region_type.value
            region_stats[type_name] = region_stats.get(type_name, 0) + 1

        # 세션에 저장
        self.session_regions[session_id] = regions

        processing_time_ms = (time.time() - start_time) * 1000

        return RegionSegmentationResult(
            session_id=session_id,
            regions=regions,
            image_width=image_width,
            image_height=image_height,
            total_regions=len(regions),
            processing_time_ms=processing_time_ms,
            region_stats=region_stats,
        )

    def _detect_regions_heuristic(
        self,
        image: Image.Image,
        width: int,
        height: int,
        config: RegionSegmentationConfig
    ) -> List[RegionDetectionResult]:
        """휴리스틱 기반 영역 검출"""
        regions = []
        min_area = config.min_region_area * width * height

        # 1. 표제란 검출 (우하단)
        if config.detect_title_block:
            title_block = self._detect_title_block(image, width, height)
            if title_block and self._get_area(title_block.bbox) >= min_area:
                regions.append(title_block)

        # 2. BOM 테이블 검출
        if config.detect_bom_table:
            bom_table = self._detect_bom_table(image, width, height)
            if bom_table and self._get_area(bom_table.bbox) >= min_area:
                regions.append(bom_table)

        # 3. 메인 뷰 (나머지 영역)
        main_view = self._detect_main_view(
            width, height, regions
        )
        if main_view and self._get_area(main_view.bbox) >= min_area:
            regions.append(main_view)

        # 4. 범례 검출 (P&ID 도면용)
        if config.detect_legend:
            legend = self._detect_legend(image, width, height)
            if legend and self._get_area(legend.bbox) >= min_area:
                regions.append(legend)

        # 5. 노트/주석 영역 검출
        if config.detect_notes:
            notes = self._detect_notes(image, width, height)
            for note in notes:
                if self._get_area(note.bbox) >= min_area:
                    regions.append(note)

        return regions

    def _detect_title_block(
        self,
        image: Image.Image,
        width: int,
        height: int
    ) -> Optional[RegionDetectionResult]:
        """표제란 검출 (우하단 영역 분석)"""
        # 일반적인 표제란 위치: 우하단 30% x 20% 영역
        # 또는 하단 전체 15% 영역

        # 방법 1: 고정 비율 기반 (환경변수로 커스터마이징 가능)
        x1 = int(width * TITLE_BLOCK_X_RATIO)
        y1 = int(height * TITLE_BLOCK_Y_RATIO)
        x2 = width
        y2 = height

        # 이미지 분석으로 실제 경계 찾기 (간단한 엣지 검출)
        try:
            # PIL을 numpy로 변환
            img_array = np.array(image.convert('L'))

            # 우하단 영역 분석
            region = img_array[y1:y2, x1:x2]

            # 수평/수직 라인 검출로 표제란 경계 확인
            # 간단한 휴리스틱: 평균 밝기가 주변과 다르면 표제란으로 판단
            avg_brightness = np.mean(region)
            main_brightness = np.mean(img_array[:y1, :x1])

            if abs(avg_brightness - main_brightness) > BRIGHTNESS_THRESHOLD:  # 밝기 차이가 있으면
                return RegionDetectionResult(
                    region_type=RegionType.TITLE_BLOCK,
                    bbox=(x1, y1, x2, y2),
                    confidence=0.8,
                    source="heuristic"
                )
        except Exception:
            pass

        # 기본 영역 반환
        return RegionDetectionResult(
            region_type=RegionType.TITLE_BLOCK,
            bbox=(x1, y1, x2, y2),
            confidence=0.6,
            source="heuristic"
        )

    def _detect_bom_table(
        self,
        image: Image.Image,
        width: int,
        height: int
    ) -> Optional[RegionDetectionResult]:
        """BOM 테이블 검출 (우상단 또는 우측)"""
        # BOM 테이블은 보통 우상단 또는 표제란 위에 위치 (환경변수로 커스터마이징 가능)
        x1 = int(width * BOM_TABLE_X_RATIO)
        y1 = 0
        x2 = width
        y2 = int(height * BOM_TABLE_Y_END_RATIO)

        try:
            img_array = np.array(image.convert('L'))
            region = img_array[y1:y2, x1:x2]

            # 테이블 패턴 감지: 수평선이 여러 개 있는지 확인
            # 간단한 휴리스틱: 수평 그래디언트 분석
            if len(region) > 0:
                row_means = np.mean(region, axis=1)
                # 급격한 변화 횟수 계산 (테이블 라인)
                diff = np.abs(np.diff(row_means))
                line_count = np.sum(diff > LINE_DIFF_THRESHOLD)

                if line_count >= MIN_TABLE_LINES:  # 최소 라인 수
                    return RegionDetectionResult(
                        region_type=RegionType.BOM_TABLE,
                        bbox=(x1, y1, x2, y2),
                        confidence=0.7,
                        source="heuristic"
                    )
        except Exception:
            pass

        return None

    def _detect_main_view(
        self,
        width: int,
        height: int,
        existing_regions: List[RegionDetectionResult]
    ) -> RegionDetectionResult:
        """메인 뷰 영역 계산 (다른 영역 제외)"""
        # 기본: 전체 이미지에서 표제란 영역 제외
        x1, y1 = 0, 0
        x2, y2 = width, height

        for region in existing_regions:
            if region.region_type == RegionType.TITLE_BLOCK:
                # 표제란이 우하단이면 메인 뷰는 그 위쪽
                if region.bbox[1] > height * 0.5:
                    y2 = min(y2, region.bbox[1])
                # 표제란이 우측이면 메인 뷰는 그 왼쪽
                if region.bbox[0] > width * 0.5:
                    x2 = min(x2, region.bbox[0])

            elif region.region_type == RegionType.BOM_TABLE:
                # BOM 테이블이 우상단이면 그 아래쪽도 제외
                if region.bbox[1] < height * 0.5 and region.bbox[0] > width * 0.5:
                    pass  # 메인 뷰에 영향 없음 (우상단은 이미 작음)

        return RegionDetectionResult(
            region_type=RegionType.MAIN_VIEW,
            bbox=(x1, y1, x2, y2),
            confidence=0.9,
            source="heuristic"
        )

    def _detect_legend(
        self,
        image: Image.Image,
        width: int,
        height: int
    ) -> Optional[RegionDetectionResult]:
        """범례 검출 (P&ID 도면용)"""
        # 범례는 보통 좌상단 또는 우하단에 위치
        # 표제란과 구분하기 어려우므로 낮은 신뢰도로 반환

        # 좌상단 영역 확인 (환경변수로 커스터마이징 가능)
        x1 = 0
        y1 = 0
        x2 = int(width * LEGEND_X_END_RATIO)
        y2 = int(height * LEGEND_Y_END_RATIO)

        try:
            img_array = np.array(image.convert('L'))
            region = img_array[y1:y2, x1:x2]

            # 범례 패턴: 작은 심볼들이 반복되는 패턴
            if len(region) > 0:
                # 분산이 높으면 다양한 심볼이 있을 가능성
                variance = np.var(region)
                if variance > VARIANCE_THRESHOLD:  # 높은 분산
                    return RegionDetectionResult(
                        region_type=RegionType.LEGEND,
                        bbox=(x1, y1, x2, y2),
                        confidence=0.5,
                        source="heuristic"
                    )
        except Exception:
            pass

        return None

    def _detect_notes(
        self,
        image: Image.Image,
        width: int,
        height: int
    ) -> List[RegionDetectionResult]:
        """노트/주석 영역 검출"""
        notes = []

        # 일반적인 노트 위치: 좌하단 (환경변수로 커스터마이징 가능)
        x1 = 0
        y1 = int(height * NOTE_Y_RATIO)
        x2 = int(width * NOTE_X_END_RATIO)
        y2 = int(height * 0.95)

        try:
            img_array = np.array(image.convert('L'))
            region = img_array[y1:y2, x1:x2]

            if len(region) > 0:
                # 텍스트가 많은 영역: 중간 밝기 분산
                mean_val = np.mean(region)
                if 100 < mean_val < 200:  # 텍스트가 있으면 중간 밝기
                    notes.append(RegionDetectionResult(
                        region_type=RegionType.NOTES,
                        bbox=(x1, y1, x2, y2),
                        confidence=0.5,
                        source="heuristic"
                    ))
        except Exception:
            pass

        return notes

    async def _detect_regions_vlm(
        self,
        image_path: str
    ) -> List[RegionDetectionResult]:
        """VLM 기반 영역 검출 (Phase 4 VLMClassifier 활용)"""
        try:
            from services.vlm_classifier import vlm_classifier

            result = await vlm_classifier.classify_drawing(image_path=image_path)

            vlm_regions = []
            for region in result.regions:
                # 정규화 좌표를 픽셀 좌표로 변환
                # VLM은 정규화 좌표 반환, 여기서는 임시로 저장
                vlm_regions.append(RegionDetectionResult(
                    region_type=RegionType(region.region_type.value),
                    bbox=tuple(region.bbox),  # 정규화 좌표 그대로
                    confidence=region.confidence,
                    source="vlm"
                ))

            return vlm_regions

        except Exception as e:
            logger.error(f"[RegionSegmenter] VLM 연동 실패: {e}")
            return []

    def _merge_regions(
        self,
        heuristic_regions: List[RegionDetectionResult],
        vlm_regions: List[RegionDetectionResult]
    ) -> List[RegionDetectionResult]:
        """휴리스틱과 VLM 결과 병합"""
        merged = list(heuristic_regions)

        for vlm_region in vlm_regions:
            # 같은 타입의 영역이 있는지 확인
            found = False
            for i, h_region in enumerate(merged):
                if h_region.region_type == vlm_region.region_type:
                    # VLM 신뢰도가 더 높으면 교체
                    if vlm_region.confidence > h_region.confidence:
                        merged[i] = vlm_region
                    found = True
                    break

            if not found:
                merged.append(vlm_region)

        return merged

    def _merge_overlapping_regions(
        self,
        regions: List[RegionDetectionResult],
        overlap_threshold: float
    ) -> List[RegionDetectionResult]:
        """겹치는 영역 병합"""
        if len(regions) <= 1:
            return regions

        merged = []
        used = set()

        for i, r1 in enumerate(regions):
            if i in used:
                continue

            best_region = r1
            for j, r2 in enumerate(regions):
                if i == j or j in used:
                    continue

                iou = self._calculate_iou(r1.bbox, r2.bbox)
                if iou > overlap_threshold:
                    # 신뢰도가 높은 쪽 선택
                    if r2.confidence > best_region.confidence:
                        best_region = r2
                    used.add(j)

            merged.append(best_region)
            used.add(i)

        return merged

    def _calculate_iou(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float]
    ) -> float:
        """IoU 계산"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def _get_area(
        self,
        bbox: Tuple[float, float, float, float]
    ) -> float:
        """영역 면적 계산"""
        return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

    # =========== 영역 관리 ===========

    def get_regions(self, session_id: str) -> List[Region]:
        """세션의 영역 목록 조회"""
        return self.session_regions.get(session_id, [])

    def get_region(self, session_id: str, region_id: str) -> Optional[Region]:
        """특정 영역 조회"""
        regions = self.session_regions.get(session_id, [])
        for region in regions:
            if region.id == region_id:
                return region
        return None

    def update_region(
        self,
        session_id: str,
        update: RegionUpdate
    ) -> Optional[Region]:
        """영역 업데이트"""
        regions = self.session_regions.get(session_id, [])

        for i, region in enumerate(regions):
            if region.id == update.region_id:
                # 업데이트 적용
                if update.region_type is not None:
                    region.region_type = update.region_type
                if update.bbox is not None:
                    region.bbox = update.bbox
                if update.processing_strategy is not None:
                    region.processing_strategy = update.processing_strategy
                if update.verification_status is not None:
                    region.verification_status = update.verification_status
                if update.label is not None:
                    region.label = update.label

                self.session_regions[session_id][i] = region
                return region

        return None

    def add_region(
        self,
        session_id: str,
        manual_region: ManualRegion,
        image_width: int,
        image_height: int
    ) -> Region:
        """수동 영역 추가"""
        # 처리 전략 결정
        strategy = manual_region.processing_strategy
        if strategy is None:
            strategy = REGION_STRATEGY_MAP.get(
                manual_region.region_type, ProcessingStrategy.SKIP
            )

        # 정규화 좌표 계산
        bbox_normalized = [
            manual_region.bbox.x1 / image_width,
            manual_region.bbox.y1 / image_height,
            manual_region.bbox.x2 / image_width,
            manual_region.bbox.y2 / image_height,
        ]

        region = Region(
            id=str(uuid.uuid4()),
            region_type=manual_region.region_type,
            bbox=manual_region.bbox,
            confidence=1.0,  # 수동 추가는 신뢰도 100%
            bbox_normalized=bbox_normalized,
            processing_strategy=strategy,
            verification_status=VerificationStatus.APPROVED,  # 수동 추가는 자동 승인
            label=manual_region.label,
        )

        if session_id not in self.session_regions:
            self.session_regions[session_id] = []

        self.session_regions[session_id].append(region)
        return region

    def delete_region(self, session_id: str, region_id: str) -> bool:
        """영역 삭제"""
        regions = self.session_regions.get(session_id, [])

        for i, region in enumerate(regions):
            if region.id == region_id:
                del self.session_regions[session_id][i]
                return True

        return False

    # =========== 영역 처리 ===========

    async def process_region(
        self,
        session_id: str,
        region_id: str,
        image_path: str
    ) -> Optional[RegionProcessingResult]:
        """
        단일 영역 처리

        영역 타입과 전략에 따라 적절한 처리 수행
        - YOLO_OCR: YOLO 검출 + OCR
        - OCR_ONLY: OCR만 적용
        - TABLE_PARSE: 테이블 파싱
        - METADATA_EXTRACT: 메타데이터 추출
        - SYMBOL_MATCH: 심볼 매칭
        """
        region = self.get_region(session_id, region_id)
        if not region:
            return None

        start_time = time.time()

        try:
            # 전략별 처리
            strategy = region.processing_strategy

            if strategy == ProcessingStrategy.YOLO_OCR:
                result = await self._process_yolo_ocr(region, image_path)
            elif strategy == ProcessingStrategy.OCR_ONLY:
                result = await self._process_ocr_only(region, image_path)
            elif strategy == ProcessingStrategy.TABLE_PARSE:
                result = await self._process_table_parse(region, image_path)
            elif strategy == ProcessingStrategy.METADATA_EXTRACT:
                result = await self._process_metadata_extract(region, image_path)
            elif strategy == ProcessingStrategy.SYMBOL_MATCH:
                result = await self._process_symbol_match(region, image_path)
            else:
                result = RegionProcessingResult(
                    region_id=region_id,
                    region_type=region.region_type,
                    processing_strategy=strategy,
                    success=True,
                    processing_time_ms=0
                )

            result.processing_time_ms = (time.time() - start_time) * 1000

            # 영역에 처리 결과 저장
            region.processed = True
            region.processing_result = {
                "success": result.success,
                "strategy": strategy.value,
                "ocr_text": result.ocr_text,
                "table_data": [dict(row) for row in (result.table_data or [])],
                "metadata": result.metadata,
            }
            self.update_region(session_id, RegionUpdate(
                region_id=region_id,
                verification_status=VerificationStatus.APPROVED if result.success else VerificationStatus.PENDING
            ))

            return result

        except Exception as e:
            return RegionProcessingResult(
                region_id=region_id,
                region_type=region.region_type,
                processing_strategy=region.processing_strategy,
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def _process_yolo_ocr(
        self,
        region: Region,
        image_path: str
    ) -> RegionProcessingResult:
        """YOLO + OCR 처리 (미구현 - Phase 6에서 구현 예정)"""
        logger.info(f"[RegionSegmenter] YOLO_OCR 처리 요청 (region: {region.id}) - 현재 스텁 반환")
        # 영역별 YOLO/OCR 처리는 현재 메인 파이프라인에서 수행
        # 이 메서드는 향후 영역 단위 세부 처리 시 구현 예정
        return RegionProcessingResult(
            region_id=region.id,
            region_type=region.region_type,
            processing_strategy=ProcessingStrategy.YOLO_OCR,
            success=True,
            detections=[],
            ocr_text="",
        )

    async def _process_ocr_only(
        self,
        region: Region,
        image_path: str
    ) -> RegionProcessingResult:
        """OCR 전용 처리 (미구현 - Phase 6에서 구현 예정)"""
        logger.info(f"[RegionSegmenter] OCR_ONLY 처리 요청 (region: {region.id}) - 현재 스텁 반환")
        # 영역별 OCR 처리는 현재 메인 파이프라인에서 수행
        return RegionProcessingResult(
            region_id=region.id,
            region_type=region.region_type,
            processing_strategy=ProcessingStrategy.OCR_ONLY,
            success=True,
            ocr_text="",
        )

    async def _process_table_parse(
        self,
        region: Region,
        image_path: str
    ) -> RegionProcessingResult:
        """테이블 파싱 처리 (미구현 - Phase 6에서 구현 예정)"""
        logger.info(f"[RegionSegmenter] TABLE_PARSE 처리 요청 (region: {region.id}) - 현재 스텁 반환")
        # BOM 테이블 파싱은 별도 테이블 OCR 모델 연동 필요
        return RegionProcessingResult(
            region_id=region.id,
            region_type=region.region_type,
            processing_strategy=ProcessingStrategy.TABLE_PARSE,
            success=True,
            table_data=[],
        )

    async def _process_metadata_extract(
        self,
        region: Region,
        image_path: str
    ) -> RegionProcessingResult:
        """메타데이터 추출 처리 (표제란) - 미구현: Phase 6에서 구현 예정"""
        logger.info(f"[RegionSegmenter] METADATA_EXTRACT 처리 요청 (region: {region.id}) - 현재 스텁 반환")
        # 표제란 OCR + 필드 파싱은 레이아웃 분석 모델 연동 필요
        metadata = {
            "drawing_number": None,
            "title": None,
            "revision": None,
            "date": None,
            "scale": None,
        }

        return RegionProcessingResult(
            region_id=region.id,
            region_type=region.region_type,
            processing_strategy=ProcessingStrategy.METADATA_EXTRACT,
            success=True,
            metadata=metadata,
        )

    async def _process_symbol_match(
        self,
        region: Region,
        image_path: str
    ) -> RegionProcessingResult:
        """심볼 매칭 처리 (범례) - 미구현: Phase 6에서 구현 예정"""
        logger.info(f"[RegionSegmenter] SYMBOL_MATCH 처리 요청 (region: {region.id}) - 현재 스텁 반환")
        # 범례 심볼 검출 및 클래스 매핑은 별도 모델 필요
        return RegionProcessingResult(
            region_id=region.id,
            region_type=region.region_type,
            processing_strategy=ProcessingStrategy.SYMBOL_MATCH,
            success=True,
            symbol_matches=[],
        )


# 싱글톤 인스턴스
region_segmenter = RegionSegmenter()
