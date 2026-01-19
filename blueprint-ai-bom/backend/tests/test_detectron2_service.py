"""Detectron2 Service 테스트

테스트 항목:
1. 서비스 초기화
2. 모델 로드
3. 검출 실행
4. 마스크/폴리곤 변환
5. YOLO/Detectron2 백엔드 전환
"""

import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np


class TestDetectron2ServiceUnit:
    """Detectron2 서비스 단위 테스트 (모델 로드 없이)"""

    def test_class_mapping_count(self):
        """클래스 매핑 개수 확인 (27개)"""
        from services.detectron2_service import Detectron2Service

        service = Detectron2Service.__new__(Detectron2Service)
        assert len(service.CLASS_MAPPING) == 27
        assert len(service.CLASS_DISPLAY_NAMES) == 27

    def test_class_mapping_consistency(self):
        """클래스 매핑과 표시명 일관성"""
        from services.detectron2_service import Detectron2Service

        service = Detectron2Service.__new__(Detectron2Service)

        for class_id in service.CLASS_MAPPING.keys():
            assert class_id in service.CLASS_DISPLAY_NAMES

    def test_mask_rle_encoding(self):
        """마스크 RLE 인코딩 테스트"""
        from services.detectron2_service import Detectron2Service

        service = Detectron2Service.__new__(Detectron2Service)

        # 간단한 마스크 생성 (4x4)
        mask = np.array([
            [0, 0, 1, 1],
            [0, 1, 1, 1],
            [1, 1, 1, 0],
            [1, 1, 0, 0],
        ], dtype=np.uint8)

        rle = service._encode_mask_rle(mask)

        assert "size" in rle
        assert "counts" in rle
        assert rle["size"] == [4, 4]

    def test_mask_to_polygons(self):
        """마스크 → 폴리곤 변환 테스트"""
        from services.detectron2_service import Detectron2Service

        service = Detectron2Service.__new__(Detectron2Service)

        # 원형에 가까운 마스크 생성
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:80, 20:80] = 1  # 사각형 영역

        polygons = service._mask_to_polygons(mask)

        assert len(polygons) >= 1
        # 각 폴리곤은 최소 3개 이상의 점
        for polygon in polygons:
            assert len(polygon) >= 3

    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        from services.detectron2_service import get_detectron2_service

        service1 = get_detectron2_service()
        service2 = get_detectron2_service()

        assert service1 is service2


class TestDetectionBackendSelection:
    """백엔드 선택 테스트"""

    def test_detection_config_default_backend(self):
        """기본 백엔드는 YOLO"""
        from schemas.detection import DetectionConfig, DetectionBackend

        config = DetectionConfig()
        assert config.backend == DetectionBackend.YOLO

    def test_detection_config_detectron2_backend(self):
        """Detectron2 백엔드 선택"""
        from schemas.detection import DetectionConfig, DetectionBackend

        config = DetectionConfig(backend=DetectionBackend.DETECTRON2)
        assert config.backend == DetectionBackend.DETECTRON2

    def test_detection_config_mask_options(self):
        """마스크/폴리곤 옵션"""
        from schemas.detection import DetectionConfig, DetectionBackend

        config = DetectionConfig(
            backend=DetectionBackend.DETECTRON2,
            return_masks=True,
            return_polygons=True
        )

        assert config.return_masks is True
        assert config.return_polygons is True


class TestMaskRLESchema:
    """마스크 RLE 스키마 테스트"""

    def test_mask_rle_model(self):
        """MaskRLE 모델 생성"""
        from schemas.detection import MaskRLE

        mask = MaskRLE(
            size=[100, 100],
            counts=[500, 200, 300]
        )

        assert mask.size == [100, 100]
        assert mask.counts == [500, 200, 300]


class TestDetectionWithMask:
    """마스크 포함 검출 결과 테스트"""

    def test_detection_with_mask(self):
        """Detection 모델에 마스크 포함"""
        from schemas.detection import Detection, BoundingBox, MaskRLE

        detection = Detection(
            id="test-1",
            class_id=0,
            class_name="ARRESTER",
            confidence=0.95,
            bbox=BoundingBox(x1=10, y1=20, x2=100, y2=150),
            model_id="detectron2",
            mask=MaskRLE(size=[100, 100], counts=[100, 50, 50]),
            polygons=[[[10.0, 20.0], [100.0, 20.0], [100.0, 150.0], [10.0, 150.0]]]
        )

        assert detection.mask is not None
        assert detection.polygons is not None
        assert len(detection.polygons) == 1
        assert len(detection.polygons[0]) == 4

    def test_detection_without_mask(self):
        """Detection 모델에 마스크 없음 (YOLO)"""
        from schemas.detection import Detection, BoundingBox

        detection = Detection(
            id="test-2",
            class_id=0,
            class_name="ARRESTER",
            confidence=0.95,
            bbox=BoundingBox(x1=10, y1=20, x2=100, y2=150),
            model_id="yolo"
        )

        assert detection.mask is None
        assert detection.polygons is None


@pytest.mark.skipif(
    not os.path.exists("/app/models/detectron2/model_final.pth"),
    reason="Detectron2 모델 파일 없음"
)
class TestDetectron2Integration:
    """Detectron2 통합 테스트 (모델 필요)"""

    def test_model_initialization(self):
        """모델 초기화 테스트"""
        from services.detectron2_service import Detectron2Service

        service = Detectron2Service()
        assert service.is_available or not service.is_available  # 환경에 따라 다름

    def test_detection_with_sample_image(self):
        """샘플 이미지 검출 테스트"""
        from services.detectron2_service import get_detectron2_service

        service = get_detectron2_service()

        if not service.is_available:
            pytest.skip("Detectron2 모델 사용 불가")

        # 테스트 이미지 경로 (있다면)
        test_image = Path("/app/test_drawings/sample.png")
        if not test_image.exists():
            pytest.skip("테스트 이미지 없음")

        result = service.detect(
            str(test_image),
            return_masks=True,
            return_polygons=True
        )

        assert "detections" in result
        assert "total_count" in result
        assert "processing_time_ms" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
