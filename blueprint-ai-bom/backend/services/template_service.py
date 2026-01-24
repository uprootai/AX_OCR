"""Template Service - 워크플로우 템플릿 관리 서비스

Phase 2: 빌더에서 생성한 워크플로우를 템플릿으로 저장
- 템플릿 CRUD
- 프로젝트와 템플릿 연결
- 세션 생성 시 템플릿 적용
"""

import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateDetail,
)

logger = logging.getLogger(__name__)


class TemplateService:
    """워크플로우 템플릿 관리 서비스"""

    def __init__(self, data_dir: Path):
        """
        Args:
            data_dir: 템플릿 데이터 저장 디렉토리
        """
        self.data_dir = data_dir
        self.templates_dir = data_dir / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # 메모리 캐시
        self.templates: Dict[str, Dict[str, Any]] = {}

        # 기존 템플릿 로드
        self._load_all_templates()

    def _load_all_templates(self):
        """모든 템플릿 파일 로드"""
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    template = json.load(f)
                    self.templates[template["template_id"]] = template
            except Exception as e:
                logger.error(f"템플릿 로드 실패: {template_file} - {e}")

        logger.info(f"템플릿 {len(self.templates)}개 로드 완료")

    def create_template(self, data: TemplateCreate) -> Dict[str, Any]:
        """템플릿 생성"""
        template_id = str(uuid.uuid4())[:8]  # 짧은 ID
        now = datetime.now()

        # 노드 타입 추출
        node_types = list(set(node.type for node in data.nodes))

        template = {
            "template_id": template_id,
            "name": data.name,
            "description": data.description,
            "model_type": data.model_type,
            "detection_params": data.detection_params,
            "features": data.features,
            "drawing_type": data.drawing_type,
            "nodes": [node.model_dump() for node in data.nodes],
            "edges": [edge.model_dump() for edge in data.edges],
            "node_count": len(data.nodes),
            "edge_count": len(data.edges),
            "node_types": node_types,
            "usage_count": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        self.templates[template_id] = template
        self._save_template(template_id)

        logger.info(f"템플릿 생성: {template_id} - {data.name}")
        return template

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """템플릿 조회"""
        return self.templates.get(template_id)

    def get_template_summary(self, template_id: str) -> Optional[Dict[str, Any]]:
        """템플릿 요약 조회 (노드/엣지 제외)"""
        template = self.get_template(template_id)
        if not template:
            return None

        # 노드/엣지 제외한 요약 반환
        summary = {k: v for k, v in template.items() if k not in ("nodes", "edges")}
        return summary

    def update_template(
        self,
        template_id: str,
        data: TemplateUpdate
    ) -> Optional[Dict[str, Any]]:
        """템플릿 수정"""
        template = self.get_template(template_id)
        if not template:
            return None

        # 업데이트할 필드만 적용
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                if key == "nodes":
                    template["nodes"] = [n.model_dump() if hasattr(n, 'model_dump') else n for n in value]
                    template["node_count"] = len(value)
                    template["node_types"] = list(set(
                        n.get("type") or n.type for n in value
                    ))
                elif key == "edges":
                    template["edges"] = [e.model_dump() if hasattr(e, 'model_dump') else e for e in value]
                    template["edge_count"] = len(value)
                else:
                    template[key] = value

        template["updated_at"] = datetime.now().isoformat()

        self.templates[template_id] = template
        self._save_template(template_id)

        logger.info(f"템플릿 수정: {template_id}")
        return template

    def delete_template(self, template_id: str) -> bool:
        """템플릿 삭제"""
        template = self.get_template(template_id)
        if not template:
            return False

        # 파일 삭제
        template_file = self.templates_dir / f"{template_id}.json"
        if template_file.exists():
            template_file.unlink()

        # 메모리에서 삭제
        del self.templates[template_id]

        logger.info(f"템플릿 삭제: {template_id}")
        return True

    def list_templates(
        self,
        model_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """템플릿 목록 조회 (요약)"""
        templates = []

        for template in self.templates.values():
            # 모델 타입 필터
            if model_type and template.get("model_type") != model_type:
                continue

            # 요약 정보만 반환 (노드/엣지 제외)
            summary = {k: v for k, v in template.items() if k not in ("nodes", "edges")}
            templates.append(summary)

        # 최신순 정렬
        templates.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return templates[:limit]

    def duplicate_template(
        self,
        template_id: str,
        new_name: str
    ) -> Optional[Dict[str, Any]]:
        """템플릿 복제"""
        original = self.get_template(template_id)
        if not original:
            return None

        # 새 ID로 복제
        new_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        duplicated = original.copy()
        duplicated["template_id"] = new_id
        duplicated["name"] = new_name
        duplicated["usage_count"] = 0
        duplicated["created_at"] = now.isoformat()
        duplicated["updated_at"] = now.isoformat()

        self.templates[new_id] = duplicated
        self._save_template(new_id)

        logger.info(f"템플릿 복제: {template_id} → {new_id}")
        return duplicated

    def increment_usage(self, template_id: str):
        """템플릿 사용 횟수 증가"""
        template = self.get_template(template_id)
        if template:
            template["usage_count"] = template.get("usage_count", 0) + 1
            self.templates[template_id] = template
            self._save_template(template_id)

    def apply_template_to_session(
        self,
        template_id: str,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """템플릿 설정을 세션에 적용"""
        template = self.get_template(template_id)
        if not template:
            return session_data

        # 템플릿 설정 적용
        session_data["template_id"] = template_id
        session_data["model_type"] = template.get("model_type")
        session_data["detection_params"] = template.get("detection_params", {})
        session_data["features"] = template.get("features", [])
        session_data["drawing_type"] = template.get("drawing_type", "auto")

        # 사용 횟수 증가
        self.increment_usage(template_id)

        return session_data

    def _save_template(self, template_id: str):
        """템플릿 파일 저장"""
        template = self.templates.get(template_id)
        if not template:
            return

        template_file = self.templates_dir / f"{template_id}.json"
        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2, default=str)


# 싱글톤 인스턴스
_template_service: Optional[TemplateService] = None


def get_template_service(data_dir: Optional[Path] = None) -> TemplateService:
    """TemplateService 싱글톤 인스턴스 반환"""
    global _template_service

    if _template_service is None:
        if data_dir is None:
            data_dir = Path("/app/data")
        _template_service = TemplateService(data_dir)

    return _template_service
