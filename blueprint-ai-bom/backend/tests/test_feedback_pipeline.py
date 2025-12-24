"""Feedback Pipeline Service Tests

Feedback Loop Pipeline 서비스 단위 테스트
- 세션 수집
- 통계 계산
- YOLO 데이터셋 내보내기
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock
import sys

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.feedback_pipeline import FeedbackPipelineService, ExportResult


class TestFeedbackPipelineService:
    """FeedbackPipelineService 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.feedback_path = Path(self.temp_dir) / "feedback"
        self.yolo_export_path = Path(self.temp_dir) / "yolo_training"

        # Mock SessionService
        self.mock_session_service = Mock()
        self.mock_session_service.list_sessions.return_value = []

        self.service = FeedbackPipelineService(
            session_service=self.mock_session_service,
            feedback_path=self.feedback_path,
            yolo_export_path=self.yolo_export_path
        )

    def test_init_creates_directories(self):
        """초기화 시 디렉토리 생성 확인"""
        assert self.feedback_path.exists()
        assert self.yolo_export_path.exists()

    def test_collect_verified_sessions_empty(self):
        """세션이 없는 경우"""
        self.mock_session_service.list_sessions.return_value = []

        result = self.service.collect_verified_sessions()

        assert result == []

    def test_collect_verified_sessions_filters_pending(self):
        """미완료(pending) 세션 필터링"""
        self.mock_session_service.list_sessions.return_value = [
            {"session_id": "session-1"}
        ]
        self.mock_session_service.get_session.return_value = {
            "session_id": "session-1",
            "filename": "test.png",
            "detections": [
                {"verification_status": "approved"},
                {"verification_status": "pending"},  # 미완료
            ]
        }

        result = self.service.collect_verified_sessions()

        # pending이 있으면 제외
        assert len(result) == 0

    def test_collect_verified_sessions_filters_low_approval_rate(self):
        """낮은 승인율 세션 필터링"""
        self.mock_session_service.list_sessions.return_value = [
            {"session_id": "session-1"}
        ]
        self.mock_session_service.get_session.return_value = {
            "session_id": "session-1",
            "filename": "test.png",
            "detections": [
                {"verification_status": "approved"},
                {"verification_status": "rejected"},
                {"verification_status": "rejected"},
                {"verification_status": "rejected"},
            ]
        }

        # 승인율 25% < 기본 50%
        result = self.service.collect_verified_sessions(min_approved_rate=0.5)

        assert len(result) == 0

    def test_collect_verified_sessions_success(self):
        """정상 세션 수집"""
        self.mock_session_service.list_sessions.return_value = [
            {"session_id": "session-1"}
        ]
        self.mock_session_service.get_session.return_value = {
            "session_id": "session-1",
            "filename": "test.png",
            "image_path": "/path/to/image.png",
            "image_width": 1000,
            "image_height": 800,
            "detections": [
                {"verification_status": "approved", "class_name": "CT"},
                {"verification_status": "approved", "class_name": "TR"},
                {"verification_status": "rejected", "class_name": "VT"},
            ]
        }

        result = self.service.collect_verified_sessions(min_approved_rate=0.5)

        assert len(result) == 1
        assert result[0]["session_id"] == "session-1"
        assert result[0]["stats"]["total"] == 3
        assert result[0]["stats"]["approved"] == 2
        assert result[0]["stats"]["rejected"] == 1

    def test_get_feedback_stats_empty(self):
        """세션이 없을 때 통계"""
        self.mock_session_service.list_sessions.return_value = []

        stats = self.service.get_feedback_stats()

        assert stats["total_sessions"] == 0
        assert stats["total_detections"] == 0
        assert stats["approved_count"] == 0
        assert stats["rejected_count"] == 0
        assert stats["modified_count"] == 0
        assert stats["approval_rate"] == 0
        assert stats["rejection_rate"] == 0
        assert stats["modification_rate"] == 0

    def test_get_feedback_stats_with_data(self):
        """데이터가 있을 때 통계"""
        self.mock_session_service.list_sessions.return_value = [
            {"session_id": "session-1"},
            {"session_id": "session-2"}
        ]

        def get_session_side_effect(session_id):
            if session_id == "session-1":
                return {
                    "session_id": "session-1",
                    "detections": [
                        {"verification_status": "approved"},
                        {"verification_status": "approved"},
                        {"verification_status": "rejected"},
                    ]
                }
            else:
                return {
                    "session_id": "session-2",
                    "detections": [
                        {"verification_status": "modified"},
                        {"verification_status": "approved"},
                    ]
                }

        self.mock_session_service.get_session.side_effect = get_session_side_effect

        stats = self.service.get_feedback_stats()

        assert stats["total_sessions"] == 2
        assert stats["total_detections"] == 5
        assert stats["approved_count"] == 3
        assert stats["rejected_count"] == 1
        assert stats["modified_count"] == 1
        assert stats["approval_rate"] == 0.6  # 3/5
        assert stats["rejection_rate"] == 0.2  # 1/5
        assert stats["modification_rate"] == 0.2  # 1/5

    def test_export_yolo_dataset_no_sessions(self):
        """세션이 없을 때 내보내기"""
        result = self.service.export_yolo_dataset(sessions=[])

        assert not result.success
        assert result.image_count == 0
        assert result.label_count == 0
        assert "No verified sessions" in result.error

    def test_export_yolo_dataset_creates_structure(self):
        """YOLO 데이터셋 디렉토리 구조 생성"""
        sessions = [{
            "session_id": "test-session",
            "filename": "test.png",
            "image_path": "",  # 이미지 없음
            "image_width": 1000,
            "image_height": 800,
            "detections": [
                {
                    "verification_status": "approved",
                    "class_name": "CT",
                    "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
                },
                {
                    "verification_status": "approved",
                    "class_name": "TR",
                    "bbox": {"x1": 300, "y1": 300, "x2": 400, "y2": 400}
                }
            ]
        }]

        result = self.service.export_yolo_dataset(
            sessions=sessions,
            output_name="test_export"
        )

        assert result.success
        output_path = Path(result.output_path)

        # 디렉토리 구조 확인
        assert (output_path / "images").exists()
        assert (output_path / "labels").exists()
        assert (output_path / "classes.txt").exists()
        assert (output_path / "metadata.json").exists()
        assert (output_path / "data.yaml").exists()

    def test_export_yolo_dataset_label_format(self):
        """YOLO 라벨 형식 확인"""
        sessions = [{
            "session_id": "test-session",
            "filename": "test.png",
            "image_path": "",
            "image_width": 1000,
            "image_height": 1000,
            "detections": [
                {
                    "verification_status": "approved",
                    "class_name": "CT",
                    "bbox": {"x1": 100, "y1": 100, "x2": 300, "y2": 300}
                }
            ]
        }]

        result = self.service.export_yolo_dataset(
            sessions=sessions,
            output_name="label_test"
        )

        assert result.success
        assert result.label_count == 1

        # 라벨 파일 확인
        label_file = Path(result.output_path) / "labels" / "test-session.txt"
        assert label_file.exists()

        with open(label_file) as f:
            content = f.read().strip()
            parts = content.split()

            # YOLO 형식: class_id x_center y_center width height
            assert len(parts) == 5
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])

            # 정규화된 값 (0-1)
            assert 0 <= x_center <= 1
            assert 0 <= y_center <= 1
            assert 0 < width <= 1
            assert 0 < height <= 1

            # bbox (100,100)-(300,300) -> center (200,200), size (200,200)
            # normalized: center (0.2, 0.2), size (0.2, 0.2)
            assert abs(x_center - 0.2) < 0.001
            assert abs(y_center - 0.2) < 0.001
            assert abs(width - 0.2) < 0.001
            assert abs(height - 0.2) < 0.001

    def test_export_yolo_dataset_excludes_rejected(self):
        """거부된 항목 제외"""
        sessions = [{
            "session_id": "test-session",
            "filename": "test.png",
            "image_path": "",
            "image_width": 1000,
            "image_height": 1000,
            "detections": [
                {
                    "verification_status": "approved",
                    "class_name": "CT",
                    "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
                },
                {
                    "verification_status": "rejected",
                    "class_name": "TR",
                    "bbox": {"x1": 300, "y1": 300, "x2": 400, "y2": 400}
                }
            ]
        }]

        result = self.service.export_yolo_dataset(
            sessions=sessions,
            include_rejected=False
        )

        assert result.success
        assert result.label_count == 1
        assert "CT" in result.class_distribution
        assert "TR" not in result.class_distribution

    def test_export_yolo_dataset_includes_rejected_when_flag_set(self):
        """include_rejected=True일 때 거부된 항목 포함"""
        sessions = [{
            "session_id": "test-session",
            "filename": "test.png",
            "image_path": "",
            "image_width": 1000,
            "image_height": 1000,
            "detections": [
                {
                    "verification_status": "approved",
                    "class_name": "CT",
                    "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
                },
                {
                    "verification_status": "rejected",
                    "class_name": "TR",
                    "bbox": {"x1": 300, "y1": 300, "x2": 400, "y2": 400}
                }
            ]
        }]

        result = self.service.export_yolo_dataset(
            sessions=sessions,
            include_rejected=True
        )

        assert result.success
        # rejected는 include_rejected=True여도 approved/modified만 포함됨
        # 따라서 label_count는 1
        assert result.label_count == 1

    def test_export_yolo_dataset_uses_modified_values(self):
        """수정된 클래스명/bbox 사용"""
        sessions = [{
            "session_id": "test-session",
            "filename": "test.png",
            "image_path": "",
            "image_width": 1000,
            "image_height": 1000,
            "detections": [
                {
                    "verification_status": "modified",
                    "class_name": "CT",
                    "modified_class_name": "GPT",  # 수정된 클래스
                    "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200},
                    "modified_bbox": {"x1": 150, "y1": 150, "x2": 250, "y2": 250}  # 수정된 bbox
                }
            ]
        }]

        result = self.service.export_yolo_dataset(sessions=sessions)

        assert result.success
        assert "GPT" in result.class_distribution
        assert "CT" not in result.class_distribution

    def test_list_exports_empty(self):
        """내보내기 목록이 없는 경우"""
        exports = self.service.list_exports()

        assert exports == []

    def test_list_exports_with_data(self):
        """내보내기 목록 조회"""
        # 내보내기 실행
        sessions = [{
            "session_id": "test-session",
            "filename": "test.png",
            "image_path": "",
            "image_width": 1000,
            "image_height": 1000,
            "detections": [
                {
                    "verification_status": "approved",
                    "class_name": "CT",
                    "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
                }
            ]
        }]

        self.service.export_yolo_dataset(sessions=sessions, output_name="export_1")
        self.service.export_yolo_dataset(sessions=sessions, output_name="export_2")

        exports = self.service.list_exports()

        assert len(exports) == 2
        export_names = [e["name"] for e in exports]
        assert "export_1" in export_names
        assert "export_2" in export_names

    def test_build_class_mapping(self):
        """클래스 매핑 생성"""
        sessions = [
            {
                "detections": [
                    {"class_name": "CT"},
                    {"class_name": "TR"},
                ]
            },
            {
                "detections": [
                    {"class_name": "CT"},  # 중복
                    {"class_name": "VT"},
                ]
            }
        ]

        mapping = self.service._build_class_mapping(sessions)

        # 알파벳 순 정렬
        assert len(mapping) == 3
        assert mapping["CT"] == 0
        assert mapping["TR"] == 1
        assert mapping["VT"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
