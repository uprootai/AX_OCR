"""Layout Analyzer 테스트

DocLayout-YOLO 통합 테스트
- 모델 초기화
- 이미지 추론
- RegionSegmenter 통합

실행: pytest tests/test_layout_analyzer.py -v
"""

import pytest
import os
from pathlib import Path

# 테스트 이미지 경로
TEST_IMAGES_DIR = Path(__file__).parent.parent.parent.parent / "test_drawings"
SAMPLE_IMAGES_DIR = Path(__file__).parent.parent.parent.parent.parent / "web-ui/public/samples"


class TestLayoutAnalyzer:
    """LayoutAnalyzer 단위 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from services.layout_analyzer import LayoutAnalyzer, get_layout_analyzer
        assert LayoutAnalyzer is not None
        assert get_layout_analyzer is not None

    def test_singleton(self):
        """싱글톤 패턴 테스트"""
        from services.layout_analyzer import get_layout_analyzer

        analyzer1 = get_layout_analyzer()
        analyzer2 = get_layout_analyzer()
        assert analyzer1 is analyzer2

    def test_is_available(self):
        """모델 사용 가능 여부 테스트"""
        from services.layout_analyzer import get_layout_analyzer

        analyzer = get_layout_analyzer()
        # doclayout-yolo가 설치되어 있으면 True
        # 설치 여부에 따라 테스트 결과가 달라질 수 있음
        assert isinstance(analyzer.is_available, bool)

    @pytest.mark.skipif(
        not os.environ.get("TEST_WITH_GPU", "").lower() == "true",
        reason="GPU 테스트는 TEST_WITH_GPU=true 환경변수 필요"
    )
    def test_detect_sample_image(self):
        """샘플 이미지 검출 테스트"""
        from services.layout_analyzer import get_layout_analyzer

        analyzer = get_layout_analyzer()
        if not analyzer.is_available:
            pytest.skip("DocLayout-YOLO 사용 불가")

        # 테스트 이미지 찾기
        sample_image = None
        for img_dir in [TEST_IMAGES_DIR, SAMPLE_IMAGES_DIR]:
            if img_dir.exists():
                for ext in ["*.jpg", "*.png"]:
                    images = list(img_dir.glob(ext))
                    if images:
                        sample_image = images[0]
                        break
            if sample_image:
                break

        if not sample_image:
            pytest.skip("테스트 이미지 없음")

        # 검출 실행
        detections = analyzer.detect(str(sample_image))

        # 결과 검증
        assert isinstance(detections, list)
        # 검출 결과가 있으면 속성 확인
        if detections:
            det = detections[0]
            assert hasattr(det, "class_name")
            assert hasattr(det, "region_type")
            assert hasattr(det, "bbox")
            assert hasattr(det, "confidence")
            assert 0 <= det.confidence <= 1

    def test_needs_vlm_fallback_empty(self):
        """VLM 폴백 테스트 - 빈 결과"""
        from services.layout_analyzer import get_layout_analyzer

        analyzer = get_layout_analyzer()
        assert analyzer.needs_vlm_fallback([]) is True

    def test_get_stats_empty(self):
        """통계 테스트 - 빈 결과"""
        from services.layout_analyzer import get_layout_analyzer

        analyzer = get_layout_analyzer()
        stats = analyzer.get_stats([])

        assert stats["total"] == 0
        assert stats["by_class"] == {}
        assert stats["by_region"] == {}


class TestRegionSegmenterIntegration:
    """RegionSegmenter + DocLayout-YOLO 통합 테스트"""

    def test_doclayout_config(self):
        """DocLayout 설정 환경변수 테스트"""
        from services.region_segmenter import USE_DOCLAYOUT, DOCLAYOUT_FALLBACK_TO_HEURISTIC

        # 기본값 확인
        assert isinstance(USE_DOCLAYOUT, bool)
        assert isinstance(DOCLAYOUT_FALLBACK_TO_HEURISTIC, bool)

    def test_region_segmenter_init(self):
        """RegionSegmenter 초기화 테스트"""
        from services.region_segmenter import RegionSegmenter, region_segmenter

        assert region_segmenter is not None
        assert isinstance(region_segmenter, RegionSegmenter)

    def test_doclayout_to_region_type_mapping(self):
        """DocLayout → RegionType 매핑 테스트"""
        from services.region_segmenter import RegionSegmenter
        from schemas.region import RegionType

        segmenter = RegionSegmenter()

        # 매핑 테스트
        assert segmenter._map_doclayout_to_region_type("TITLE_BLOCK") == RegionType.TITLE_BLOCK
        assert segmenter._map_doclayout_to_region_type("BOM_TABLE") == RegionType.BOM_TABLE
        assert segmenter._map_doclayout_to_region_type("MAIN_VIEW") == RegionType.MAIN_VIEW
        assert segmenter._map_doclayout_to_region_type("NOTES") == RegionType.NOTES
        assert segmenter._map_doclayout_to_region_type("UNKNOWN_TYPE") == RegionType.UNKNOWN

    def test_needs_vlm_fallback(self):
        """VLM 폴백 필요 여부 테스트"""
        from services.region_segmenter import RegionSegmenter, RegionDetectionResult
        from schemas.region import RegionType

        segmenter = RegionSegmenter()

        # 빈 결과 → VLM 필요
        assert segmenter._needs_vlm_fallback([]) is True

        # 낮은 신뢰도 → VLM 필요
        low_conf_regions = [
            RegionDetectionResult(
                region_type=RegionType.MAIN_VIEW,
                bbox=(0, 0, 100, 100),
                confidence=0.3,
                source="doclayout"
            )
        ]
        assert segmenter._needs_vlm_fallback(low_conf_regions) is True

        # 높은 신뢰도 + MAIN_VIEW → VLM 불필요
        high_conf_regions = [
            RegionDetectionResult(
                region_type=RegionType.MAIN_VIEW,
                bbox=(0, 0, 100, 100),
                confidence=0.9,
                source="doclayout"
            )
        ]
        assert segmenter._needs_vlm_fallback(high_conf_regions) is False

        # MAIN_VIEW 없음 → VLM 필요
        no_main_view = [
            RegionDetectionResult(
                region_type=RegionType.TITLE_BLOCK,
                bbox=(0, 0, 100, 100),
                confidence=0.9,
                source="doclayout"
            )
        ]
        assert segmenter._needs_vlm_fallback(no_main_view) is True


class TestDocLayoutClassMapping:
    """DocLayout 클래스 매핑 테스트"""

    def test_doclayout_to_region_map(self):
        """클래스 매핑 상수 테스트"""
        from services.layout_analyzer import DOCLAYOUT_TO_REGION_MAP

        # 필수 매핑 확인
        assert "title" in DOCLAYOUT_TO_REGION_MAP
        assert "table" in DOCLAYOUT_TO_REGION_MAP
        assert "figure" in DOCLAYOUT_TO_REGION_MAP

        # 매핑 값 확인
        assert DOCLAYOUT_TO_REGION_MAP["title"] == "TITLE_BLOCK"
        assert DOCLAYOUT_TO_REGION_MAP["table"] == "BOM_TABLE"
        assert DOCLAYOUT_TO_REGION_MAP["figure"] == "MAIN_VIEW"
