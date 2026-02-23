"""Region Segmenter Service (Phase 5 + DocLayout-YOLO 통합)

도면 영역 분할 서비스
- DocLayout-YOLO 기반 ML 검출 (신규, 40ms/이미지)
- 휴리스틱 기반 영역 검출 (표제란, BOM 테이블, 메인 뷰 등)
- VLM 연동 옵션 (Phase 4 VLMClassifier 활용)
- 수동 영역 추가/수정 지원
- 영역별 처리 전략 적용

통합 일자: 2025-12-31
리팩토링: 2026-02-23 (배럴 re-export 패턴으로 모듈 분리)
DocLayout-YOLO 테스트: rnd/experiments/doclayout_yolo/REPORT.md

모듈 구조:
- _region_constants.py: 공유 상수 및 RegionDetectionResult 데이터클래스
- region_analysis.py: 엣지 검출, 마스크 생성, 개별 영역 검출 함수
- region_merging.py: 영역 병합, 중복 제거, IoU 계산, DocLayout/VLM 검출
- region_segmenter.py (이 파일): RegionSegmenter 클래스 + 오케스트레이션 + re-export
"""

import uuid
import time
import logging
from typing import Optional, List, Dict

from PIL import Image

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

# 배럴 re-export: 기존 import 경로 유지
from services._region_constants import (  # noqa: F401
    RegionDetectionResult,
    TITLE_BLOCK_X_RATIO,
    TITLE_BLOCK_Y_RATIO,
    BOM_TABLE_X_RATIO,
    BOM_TABLE_Y_END_RATIO,
    LEGEND_X_END_RATIO,
    LEGEND_Y_END_RATIO,
    NOTE_X_END_RATIO,
    NOTE_Y_RATIO,
    BRIGHTNESS_THRESHOLD,
    LINE_DIFF_THRESHOLD,
    MIN_TABLE_LINES,
    VARIANCE_THRESHOLD,
    USE_DOCLAYOUT,
    DOCLAYOUT_FALLBACK_TO_HEURISTIC,
)

# 분석 함수 re-export
from services.region_analysis import (  # noqa: F401
    detect_regions_heuristic,
    detect_title_block,
    detect_bom_table,
    detect_main_view,
    detect_legend,
    detect_notes,
    get_area,
)

# 병합 함수 re-export
from services.region_merging import (  # noqa: F401
    detect_regions_doclayout,
    map_doclayout_to_region_type,
    needs_vlm_fallback,
    detect_regions_vlm,
    merge_regions,
    merge_overlapping_regions,
    calculate_iou,
)

logger = logging.getLogger(__name__)


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
        detection_source = "heuristic"  # 검출 소스 추적

        # 1. DocLayout-YOLO 기반 영역 검출 (우선 시도)
        if USE_DOCLAYOUT:
            try:
                doclayout_regions = detect_regions_doclayout(image_path, image_width, image_height)
                if doclayout_regions:
                    detected_regions.extend(doclayout_regions)
                    detection_source = "doclayout"
                    logger.info(f"[RegionSegmenter] DocLayout-YOLO: {len(doclayout_regions)}개 영역 검출")
            except Exception as e:
                logger.warning(f"[RegionSegmenter] DocLayout-YOLO 검출 실패: {e}")

        # 2. 휴리스틱 폴백 (DocLayout 결과 없거나 비활성화된 경우)
        if not detected_regions or (not USE_DOCLAYOUT and DOCLAYOUT_FALLBACK_TO_HEURISTIC):
            heuristic_regions = detect_regions_heuristic(
                image, image_width, image_height, config,
                self.title_block_hints, self.bom_table_hints
            )
            if not detected_regions:
                detected_regions.extend(heuristic_regions)
                detection_source = "heuristic"
            else:
                # DocLayout + 휴리스틱 병합
                detected_regions = merge_regions(detected_regions, heuristic_regions)
                detection_source = "hybrid"

        # 3. VLM 기반 영역 검출 (옵션 - 저신뢰도 영역 검증)
        if use_vlm:
            try:
                # VLM 폴백 필요 여부 확인
                if needs_vlm_fallback(detected_regions):
                    vlm_regions = await detect_regions_vlm(image_path)
                    # VLM 결과 병합 (높은 신뢰도 우선)
                    detected_regions = merge_regions(detected_regions, vlm_regions)
                    detection_source = f"{detection_source}+vlm"
                    logger.info(f"[RegionSegmenter] VLM 폴백 적용: {len(vlm_regions)}개 영역")
            except Exception as e:
                logger.warning(f"[RegionSegmenter] VLM 영역 검출 실패: {e}")

        # 3. 겹치는 영역 처리
        if config.merge_overlapping:
            detected_regions = merge_overlapping_regions(
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
        return RegionProcessingResult(
            region_id=region.id,
            region_type=region.region_type,
            processing_strategy=ProcessingStrategy.SYMBOL_MATCH,
            success=True,
            symbol_matches=[],
        )


# 싱글톤 인스턴스
region_segmenter = RegionSegmenter()
