"""Project Service - 프로젝트 관리 서비스

Phase 2: 프로젝트 기반 도면 관리
- 프로젝트 CRUD
- 세션과 프로젝트 연결
- 도면 일괄 업로드
"""

import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetail,
)

logger = logging.getLogger(__name__)


# 프로젝트 타입별 기본 features 프리셋
PROJECT_TYPE_PRESETS = {
    "bom_quotation": {
        "drawing_type": "dimension_bom",
        "features": ["dimension_ocr", "table_extraction", "bom_generation", "title_block_ocr"],
    },
    "pid_detection": {
        "drawing_type": "pid",
        "features": ["symbol_detection", "pid_connectivity", "gt_comparison"],
    },
    "general": {
        "drawing_type": "auto",
        "features": ["symbol_detection", "dimension_ocr", "title_block_ocr"],
    },
}


def get_default_features_for_type(project_type: str) -> dict:
    """프로젝트 타입에 따른 기본 features/drawing_type 프리셋 반환"""
    return PROJECT_TYPE_PRESETS.get(project_type, PROJECT_TYPE_PRESETS["general"])


class ProjectService:
    """프로젝트 관리 서비스"""

    def __init__(self, data_dir: Path):
        """
        Args:
            data_dir: 프로젝트 데이터 저장 디렉토리
        """
        self.data_dir = data_dir
        self.projects_dir = data_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # 메모리 캐시
        self.projects: Dict[str, Dict[str, Any]] = {}

        # 기존 프로젝트 로드
        self._load_all_projects()

    def _load_all_projects(self):
        """모든 프로젝트 파일 로드"""
        for project_file in self.projects_dir.glob("*/project.json"):
            try:
                with open(project_file, "r", encoding="utf-8") as f:
                    project = json.load(f)
                    project.setdefault("project_type", "general")
                    self.projects[project["project_id"]] = project
            except Exception as e:
                logger.error(f"프로젝트 로드 실패: {project_file} - {e}")

        logger.info(f"프로젝트 {len(self.projects)}개 로드 완료")

    def create_project(self, data: ProjectCreate) -> Dict[str, Any]:
        """프로젝트 생성"""
        project_id = str(uuid.uuid4())[:8]  # 짧은 ID
        now = datetime.now()

        project = {
            "project_id": project_id,
            "name": data.name,
            "customer": data.customer,
            "description": data.description,
            "project_type": data.project_type,
            "default_template_id": data.default_template_id,
            "default_template_name": None,
            "default_model_type": data.default_model_type,
            "default_features": data.default_features,
            "gt_folder": None,
            "reference_folder": None,
            # BOM 프로젝트 확장
            "bom_source": getattr(data, "bom_source", None),
            "drawing_folder": getattr(data, "drawing_folder", None),
            # 통계
            "session_count": 0,
            "completed_count": 0,
            "pending_count": 0,
            "bom_item_count": 0,
            "quotation_item_count": 0,
            "quoted_count": 0,
            "total_quotation": 0.0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        # 프로젝트 디렉토리 생성
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # GT 및 참조도면 폴더 생성
        (project_dir / "gt_labels").mkdir(exist_ok=True)
        (project_dir / "references").mkdir(exist_ok=True)

        # 폴더 경로 설정
        project["gt_folder"] = str(project_dir / "gt_labels")
        project["reference_folder"] = str(project_dir / "references")

        # 저장
        self.projects[project_id] = project
        self._save_project(project_id)

        logger.info(f"프로젝트 생성: {project_id} - {data.name}")
        return project

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """프로젝트 조회"""
        return self.projects.get(project_id)

    def get_project_detail(
        self,
        project_id: str,
        session_service=None,
        template_service=None
    ) -> Optional[Dict[str, Any]]:
        """프로젝트 상세 조회 (세션 목록 포함)"""
        project = self.get_project(project_id)
        if not project:
            return None

        detail = project.copy()

        # 세션 목록 조회
        if session_service:
            sessions = session_service.list_sessions_by_project(project_id)
            detail["sessions"] = sessions

            # 통계 업데이트
            detail["session_count"] = len(sessions)
            detail["completed_count"] = len([
                s for s in sessions
                if s.get("status") == "completed"
            ])
            detail["pending_count"] = len([
                s for s in sessions
                if s.get("status") in ("uploaded", "detected", "verifying")
            ])

        # 템플릿 정보 조회
        if template_service and project.get("default_template_id"):
            template = template_service.get_template(project["default_template_id"])
            if template:
                detail["template"] = template
                detail["default_template_name"] = template.get("name")

        return detail

    def update_project(
        self,
        project_id: str,
        data: ProjectUpdate
    ) -> Optional[Dict[str, Any]]:
        """프로젝트 수정"""
        project = self.get_project(project_id)
        if not project:
            return None

        # 업데이트할 필드만 적용
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                project[key] = value

        project["updated_at"] = datetime.now().isoformat()

        self.projects[project_id] = project
        self._save_project(project_id)

        logger.info(f"프로젝트 수정: {project_id}")
        return project

    def delete_project(
        self,
        project_id: str,
        delete_sessions: bool = False,
        session_service=None
    ) -> bool:
        """프로젝트 삭제"""
        import shutil

        project = self.get_project(project_id)
        if not project:
            return False

        # 세션 삭제 (옵션)
        if delete_sessions and session_service:
            sessions = session_service.list_sessions_by_project(project_id)
            for session in sessions:
                session_service.delete_session(session["session_id"])
            logger.info(f"프로젝트 세션 {len(sessions)}개 삭제")

        # 프로젝트 디렉토리 삭제
        project_dir = self.projects_dir / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir)

        # 메모리에서 삭제
        del self.projects[project_id]

        logger.info(f"프로젝트 삭제: {project_id}")
        return True

    def list_projects(
        self,
        customer: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """프로젝트 목록 조회"""
        projects = list(self.projects.values())

        # 고객사 필터
        if customer:
            projects = [p for p in projects if p.get("customer") == customer]

        # 최신순 정렬
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return projects[:limit]

    def update_session_counts(
        self,
        project_id: str,
        session_service=None
    ):
        """프로젝트 세션 통계 업데이트"""
        project = self.get_project(project_id)
        if not project or not session_service:
            return

        sessions = session_service.list_sessions_by_project(project_id)

        project["session_count"] = len(sessions)
        project["completed_count"] = len([
            s for s in sessions
            if s.get("status") == "completed"
        ])
        project["pending_count"] = len([
            s for s in sessions
            if s.get("status") in ("uploaded", "detected", "verifying")
        ])
        project["updated_at"] = datetime.now().isoformat()

        self.projects[project_id] = project
        self._save_project(project_id)

    def _save_project(self, project_id: str):
        """프로젝트 파일 저장"""
        project = self.projects.get(project_id)
        if not project:
            return

        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        project_file = project_dir / "project.json"
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2, default=str)


# 싱글톤 인스턴스
_project_service: Optional[ProjectService] = None


def get_project_service(data_dir: Optional[Path] = None) -> ProjectService:
    """ProjectService 싱글톤 인스턴스 반환"""
    global _project_service

    if _project_service is None:
        if data_dir is None:
            data_dir = Path("/app/data")
        _project_service = ProjectService(data_dir)

    return _project_service
