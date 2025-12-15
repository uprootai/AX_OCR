"""Detection Service Tests"""

import pytest
from pathlib import Path
import sys

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.detection_service import DetectionService
from schemas.detection import DetectionConfig


class TestDetectionService:
    """DetectionService 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.service = DetectionService(model_path=None)

    def test_class_mapping(self):
        """클래스 매핑 테스트"""
        mapping = self.service.get_class_mapping()

        assert len(mapping) == 27
        assert mapping[0] == "beam"
        assert mapping[17] == "valve"
        assert mapping[26] == "strainer"

    def test_get_class_names(self):
        """클래스 이름 목록 테스트"""
        names = self.service.get_class_names()

        assert len(names) == 27
        assert "bolt" in names
        assert "pipe" in names
        assert "valve" in names

    def test_add_manual_detection(self):
        """수동 검출 추가 테스트"""
        detection = self.service.add_manual_detection(
            class_name="valve",
            bbox={"x1": 100, "y1": 100, "x2": 200, "y2": 200}
        )

        assert detection["class_name"] == "valve"
        assert detection["class_id"] == 17  # valve의 ID
        assert detection["confidence"] == 1.0
        assert detection["verification_status"] == "manual"
        assert "id" in detection

    def test_add_manual_detection_unknown_class(self):
        """알 수 없는 클래스 수동 검출 테스트"""
        detection = self.service.add_manual_detection(
            class_name="unknown_part",
            bbox={"x1": 0, "y1": 0, "x2": 50, "y2": 50}
        )

        assert detection["class_name"] == "unknown_part"
        assert detection["class_id"] == -1  # 알 수 없는 클래스
        assert detection["confidence"] == 1.0


class TestDetectionConfig:
    """DetectionConfig 테스트"""

    def test_default_config(self):
        """기본 설정 테스트"""
        config = DetectionConfig()

        assert config.confidence == 0.7
        assert config.iou_threshold == 0.45
        assert config.model_id == "yolo_v11n"
        assert config.device is None

    def test_custom_config(self):
        """커스텀 설정 테스트"""
        config = DetectionConfig(
            confidence=0.5,
            iou_threshold=0.6,
            model_id="custom_model",
            device="cuda"
        )

        assert config.confidence == 0.5
        assert config.iou_threshold == 0.6
        assert config.model_id == "custom_model"
        assert config.device == "cuda"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
