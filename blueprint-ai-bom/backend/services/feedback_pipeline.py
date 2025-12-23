"""Feedback Loop Pipeline Service

검증된 데이터를 수집하여 모델 재학습용 데이터셋 생성
- YOLO 형식 라벨 내보내기
- 검증 통계 리포트
- 세션별/기간별 데이터 집계
"""

import os
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict
from dataclasses import dataclass, field

from services.session_service import SessionService

logger = logging.getLogger(__name__)

# 환경 변수
FEEDBACK_DATA_PATH = Path(os.getenv("FEEDBACK_DATA_PATH", "/data/feedback"))
YOLO_EXPORT_PATH = Path(os.getenv("YOLO_EXPORT_PATH", "/data/yolo_training"))


class FeedbackStats(TypedDict):
    """피드백 통계"""
    total_sessions: int
    total_detections: int
    approved_count: int
    rejected_count: int
    modified_count: int
    approval_rate: float
    rejection_rate: float
    modification_rate: float


class YOLOLabel(TypedDict):
    """YOLO 라벨 형식"""
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float


@dataclass
class ExportResult:
    """내보내기 결과"""
    success: bool
    output_path: str
    image_count: int
    label_count: int
    class_distribution: Dict[str, int]
    timestamp: str
    error: Optional[str] = None


class FeedbackPipelineService:
    """
    피드백 루프 파이프라인

    검증된 데이터를 수집하여 YOLO 재학습용 데이터셋 생성
    """

    def __init__(
        self,
        session_service: SessionService,
        feedback_path: Path = FEEDBACK_DATA_PATH,
        yolo_export_path: Path = YOLO_EXPORT_PATH
    ):
        self.session_service = session_service
        self.feedback_path = feedback_path
        self.yolo_export_path = yolo_export_path

        # 디렉토리 생성
        self.feedback_path.mkdir(parents=True, exist_ok=True)
        self.yolo_export_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"FeedbackPipelineService 초기화: {self.feedback_path}")

    def collect_verified_sessions(
        self,
        min_approved_rate: float = 0.5,
        days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        검증 완료된 세션 수집

        Args:
            min_approved_rate: 최소 승인율 (기본 50%)
            days_back: 최근 N일 내 세션만 (None이면 전체)

        Returns:
            검증 완료 세션 목록
        """
        all_sessions = self.session_service.list_sessions()
        verified_sessions = []

        cutoff_date = None
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)

        for session in all_sessions:
            session_id = session.get("session_id")
            if not session_id:
                continue

            try:
                session_detail = self.session_service.get_session(session_id)
                if not session_detail:
                    continue

                # 날짜 필터
                if cutoff_date:
                    created_at = session_detail.get("created_at", "")
                    if created_at:
                        session_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if session_date < cutoff_date:
                            continue

                detections = session_detail.get("detections", [])
                if not detections:
                    continue

                # 검증 통계 계산
                total = len(detections)
                approved = sum(1 for d in detections if d.get("verification_status") == "approved")
                rejected = sum(1 for d in detections if d.get("verification_status") == "rejected")
                pending = sum(1 for d in detections if d.get("verification_status") == "pending")

                # 미완료 세션 제외
                if pending > 0:
                    continue

                # 승인율 필터
                approval_rate = approved / total if total > 0 else 0
                if approval_rate < min_approved_rate:
                    continue

                verified_sessions.append({
                    "session_id": session_id,
                    "filename": session_detail.get("filename", ""),
                    "image_path": session_detail.get("image_path", ""),
                    "image_width": session_detail.get("image_width", 0),
                    "image_height": session_detail.get("image_height", 0),
                    "detections": detections,
                    "stats": {
                        "total": total,
                        "approved": approved,
                        "rejected": rejected,
                        "approval_rate": approval_rate
                    }
                })

            except Exception as e:
                logger.warning(f"세션 {session_id} 조회 실패: {e}")
                continue

        return verified_sessions

    def export_yolo_dataset(
        self,
        sessions: Optional[List[Dict[str, Any]]] = None,
        output_name: Optional[str] = None,
        include_rejected: bool = False,
        class_mapping: Optional[Dict[str, int]] = None
    ) -> ExportResult:
        """
        YOLO 형식 데이터셋 내보내기

        Args:
            sessions: 내보낼 세션들 (None이면 자동 수집)
            output_name: 출력 디렉토리명 (None이면 타임스탬프)
            include_rejected: 거부된 항목도 포함 여부
            class_mapping: 클래스명 -> ID 매핑 (None이면 자동 생성)

        Returns:
            내보내기 결과
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = output_name or f"feedback_dataset_{timestamp}"
        output_dir = self.yolo_export_path / output_name

        try:
            # 디렉토리 구조 생성
            images_dir = output_dir / "images"
            labels_dir = output_dir / "labels"
            images_dir.mkdir(parents=True, exist_ok=True)
            labels_dir.mkdir(parents=True, exist_ok=True)

            # 세션 수집
            if sessions is None:
                sessions = self.collect_verified_sessions()

            if not sessions:
                return ExportResult(
                    success=False,
                    output_path=str(output_dir),
                    image_count=0,
                    label_count=0,
                    class_distribution={},
                    timestamp=timestamp,
                    error="No verified sessions found"
                )

            # 클래스 매핑 생성/로드
            if class_mapping is None:
                class_mapping = self._build_class_mapping(sessions)

            image_count = 0
            label_count = 0
            class_distribution: Dict[str, int] = {}

            for session in sessions:
                session_id = session["session_id"]
                image_path = session.get("image_path", "")
                image_width = session.get("image_width", 1)
                image_height = session.get("image_height", 1)
                detections = session.get("detections", [])

                # 이미지 복사
                if image_path and os.path.exists(image_path):
                    ext = os.path.splitext(image_path)[1]
                    dest_image = images_dir / f"{session_id}{ext}"
                    shutil.copy2(image_path, dest_image)
                    image_count += 1

                # 라벨 생성
                labels = []
                for det in detections:
                    status = det.get("verification_status", "pending")

                    # 거부된 항목 제외 (옵션)
                    if status == "rejected" and not include_rejected:
                        continue

                    # 승인/수정된 항목만 포함
                    if status not in ["approved", "modified"]:
                        continue

                    # 클래스명 (수정된 경우 수정된 값 사용)
                    class_name = det.get("modified_class_name") or det.get("class_name", "unknown")

                    # 클래스 ID
                    if class_name not in class_mapping:
                        class_mapping[class_name] = len(class_mapping)
                    class_id = class_mapping[class_name]

                    # 바운딩 박스 (수정된 경우 수정된 값 사용)
                    bbox = det.get("modified_bbox") or det.get("bbox", {})
                    x1 = bbox.get("x1", 0)
                    y1 = bbox.get("y1", 0)
                    x2 = bbox.get("x2", 0)
                    y2 = bbox.get("y2", 0)

                    # YOLO 형식으로 변환 (정규화된 중심 좌표 + 크기)
                    x_center = ((x1 + x2) / 2) / image_width
                    y_center = ((y1 + y2) / 2) / image_height
                    width = (x2 - x1) / image_width
                    height = (y2 - y1) / image_height

                    # 유효성 검사
                    if 0 <= x_center <= 1 and 0 <= y_center <= 1 and width > 0 and height > 0:
                        labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

                        # 통계 업데이트
                        class_distribution[class_name] = class_distribution.get(class_name, 0) + 1
                        label_count += 1

                # 라벨 파일 저장
                if labels:
                    label_file = labels_dir / f"{session_id}.txt"
                    with open(label_file, "w") as f:
                        f.write("\n".join(labels))

            # 클래스 파일 저장
            classes_file = output_dir / "classes.txt"
            sorted_classes = sorted(class_mapping.items(), key=lambda x: x[1])
            with open(classes_file, "w") as f:
                for class_name, _ in sorted_classes:
                    f.write(f"{class_name}\n")

            # 메타데이터 저장
            metadata = {
                "created_at": timestamp,
                "image_count": image_count,
                "label_count": label_count,
                "class_count": len(class_mapping),
                "class_mapping": class_mapping,
                "class_distribution": class_distribution,
                "sessions": [s["session_id"] for s in sessions]
            }
            metadata_file = output_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # YOLO data.yaml 생성
            data_yaml = output_dir / "data.yaml"
            with open(data_yaml, "w") as f:
                f.write(f"path: {output_dir}\n")
                f.write("train: images\n")
                f.write("val: images\n")
                f.write(f"nc: {len(class_mapping)}\n")
                f.write(f"names: {list(class_mapping.keys())}\n")

            logger.info(
                f"YOLO 데이터셋 내보내기 완료: {output_dir}, "
                f"이미지 {image_count}개, 라벨 {label_count}개"
            )

            return ExportResult(
                success=True,
                output_path=str(output_dir),
                image_count=image_count,
                label_count=label_count,
                class_distribution=class_distribution,
                timestamp=timestamp
            )

        except Exception as e:
            logger.error(f"YOLO 데이터셋 내보내기 실패: {e}")
            return ExportResult(
                success=False,
                output_path=str(output_dir),
                image_count=0,
                label_count=0,
                class_distribution={},
                timestamp=timestamp,
                error=str(e)
            )

    def _build_class_mapping(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        """세션들에서 클래스 매핑 생성"""
        class_names = set()
        for session in sessions:
            for det in session.get("detections", []):
                class_name = det.get("modified_class_name") or det.get("class_name")
                if class_name:
                    class_names.add(class_name)

        return {name: idx for idx, name in enumerate(sorted(class_names))}

    def get_feedback_stats(
        self,
        days_back: Optional[int] = None
    ) -> FeedbackStats:
        """
        피드백 통계 조회

        Args:
            days_back: 최근 N일 내 (None이면 전체)

        Returns:
            피드백 통계
        """
        sessions = self.collect_verified_sessions(min_approved_rate=0, days_back=days_back)

        total_detections = 0
        approved_count = 0
        rejected_count = 0
        modified_count = 0

        for session in sessions:
            for det in session.get("detections", []):
                total_detections += 1
                status = det.get("verification_status", "pending")

                if status == "approved":
                    approved_count += 1
                elif status == "rejected":
                    rejected_count += 1
                elif status == "modified":
                    modified_count += 1

        return FeedbackStats(
            total_sessions=len(sessions),
            total_detections=total_detections,
            approved_count=approved_count,
            rejected_count=rejected_count,
            modified_count=modified_count,
            approval_rate=approved_count / total_detections if total_detections > 0 else 0,
            rejection_rate=rejected_count / total_detections if total_detections > 0 else 0,
            modification_rate=modified_count / total_detections if total_detections > 0 else 0
        )

    def list_exports(self) -> List[Dict[str, Any]]:
        """내보내기 목록 조회"""
        exports = []

        for export_dir in self.yolo_export_path.iterdir():
            if not export_dir.is_dir():
                continue

            metadata_file = export_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    exports.append({
                        "name": export_dir.name,
                        "path": str(export_dir),
                        "created_at": metadata.get("created_at"),
                        "image_count": metadata.get("image_count", 0),
                        "label_count": metadata.get("label_count", 0),
                        "class_count": metadata.get("class_count", 0)
                    })

        return sorted(exports, key=lambda x: x.get("created_at", ""), reverse=True)


# 싱글톤 (SessionService 주입 필요)
_feedback_pipeline_service: Optional[FeedbackPipelineService] = None


def get_feedback_pipeline_service(session_service: SessionService) -> FeedbackPipelineService:
    """싱글톤 FeedbackPipelineService 반환"""
    global _feedback_pipeline_service
    if _feedback_pipeline_service is None:
        _feedback_pipeline_service = FeedbackPipelineService(session_service)
    return _feedback_pipeline_service
