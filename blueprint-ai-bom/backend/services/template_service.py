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
    TemplateVersion,
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
        self.versions_dir = data_dir / "template_versions"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        # 메모리 캐시
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[str, List[Dict[str, Any]]] = {}  # template_id -> versions

        # 기존 템플릿 로드
        self._load_all_templates()
        self._load_all_versions()

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

    # ============ 버전 관리 메서드 ============

    def _load_all_versions(self):
        """모든 버전 파일 로드"""
        for version_file in self.versions_dir.glob("*.json"):
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    version_data = json.load(f)
                    template_id = version_data.get("template_id")
                    if template_id:
                        if template_id not in self.versions:
                            self.versions[template_id] = []
                        self.versions[template_id].append(version_data)
            except Exception as e:
                logger.error(f"버전 로드 실패: {version_file} - {e}")

        # 각 템플릿의 버전을 버전 번호순 정렬
        for template_id in self.versions:
            self.versions[template_id].sort(key=lambda v: v.get("version", 0))

        total_versions = sum(len(v) for v in self.versions.values())
        logger.info(f"템플릿 버전 {total_versions}개 로드 완료")

    def _create_version_snapshot(
        self,
        template_id: str,
        change_summary: str = "",
        created_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """현재 템플릿 상태의 버전 스냅샷 생성"""
        template = self.get_template(template_id)
        if not template:
            return None

        # 현재 버전 번호 계산
        current_versions = self.versions.get(template_id, [])
        next_version = len(current_versions) + 1

        # 버전 스냅샷 생성
        version_data = {
            "version": next_version,
            "template_id": template_id,
            "name": template.get("name"),
            "description": template.get("description"),
            "model_type": template.get("model_type"),
            "detection_params": template.get("detection_params", {}),
            "features": template.get("features", []),
            "drawing_type": template.get("drawing_type", "auto"),
            "nodes": template.get("nodes", []),
            "edges": template.get("edges", []),
            "node_count": template.get("node_count", 0),
            "edge_count": template.get("edge_count", 0),
            "change_summary": change_summary,
            "created_at": datetime.now().isoformat(),
            "created_by": created_by,
        }

        # 메모리에 저장
        if template_id not in self.versions:
            self.versions[template_id] = []
        self.versions[template_id].append(version_data)

        # 파일로 저장
        version_file = self.versions_dir / f"{template_id}_v{next_version}.json"
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2, default=str)

        # 템플릿에 현재 버전 정보 업데이트
        template["current_version"] = next_version
        self.templates[template_id] = template
        self._save_template(template_id)

        logger.info(f"템플릿 버전 생성: {template_id} v{next_version}")
        return version_data

    def get_version_history(self, template_id: str) -> List[Dict[str, Any]]:
        """템플릿 버전 히스토리 조회"""
        versions = self.versions.get(template_id, [])
        # 최신순으로 반환
        return sorted(versions, key=lambda v: v.get("version", 0), reverse=True)

    def get_version(self, template_id: str, version: int) -> Optional[Dict[str, Any]]:
        """특정 버전 조회"""
        versions = self.versions.get(template_id, [])
        for v in versions:
            if v.get("version") == version:
                return v
        return None

    def rollback_to_version(
        self,
        template_id: str,
        target_version: int,
        created_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """특정 버전으로 롤백"""
        target = self.get_version(template_id, target_version)
        if not target:
            return None

        # 현재 상태를 먼저 버전으로 저장
        self._create_version_snapshot(
            template_id,
            change_summary=f"v{target_version}으로 롤백 전 백업",
            created_by=created_by
        )

        # 타겟 버전의 데이터로 템플릿 복원
        template = self.get_template(template_id)
        if not template:
            return None

        # 복원할 필드들
        restore_fields = [
            "name", "description", "model_type", "detection_params",
            "features", "drawing_type", "nodes", "edges",
            "node_count", "edge_count"
        ]
        for field in restore_fields:
            if field in target:
                template[field] = target[field]

        template["updated_at"] = datetime.now().isoformat()
        self.templates[template_id] = template
        self._save_template(template_id)

        # 롤백 후 새 버전 생성
        self._create_version_snapshot(
            template_id,
            change_summary=f"v{target_version}에서 롤백 완료",
            created_by=created_by
        )

        logger.info(f"템플릿 롤백: {template_id} → v{target_version}")
        return template

    def compare_versions(
        self,
        template_id: str,
        version_a: int,
        version_b: int
    ) -> Optional[Dict[str, Any]]:
        """두 버전 비교"""
        va = self.get_version(template_id, version_a)
        vb = self.get_version(template_id, version_b)

        if not va or not vb:
            return None

        diff = {
            "template_id": template_id,
            "version_a": version_a,
            "version_b": version_b,
            "changes": []
        }

        # 비교할 필드들
        compare_fields = [
            ("name", "이름"),
            ("model_type", "모델 타입"),
            ("drawing_type", "도면 타입"),
            ("node_count", "노드 수"),
            ("edge_count", "엣지 수"),
        ]

        for field, label in compare_fields:
            val_a = va.get(field)
            val_b = vb.get(field)
            if val_a != val_b:
                diff["changes"].append({
                    "field": field,
                    "label": label,
                    "from": val_a,
                    "to": val_b
                })

        # 파라미터 비교
        params_a = va.get("detection_params", {})
        params_b = vb.get("detection_params", {})
        all_params = set(params_a.keys()) | set(params_b.keys())
        for param in all_params:
            val_a = params_a.get(param)
            val_b = params_b.get(param)
            if val_a != val_b:
                diff["changes"].append({
                    "field": f"detection_params.{param}",
                    "label": f"파라미터: {param}",
                    "from": val_a,
                    "to": val_b
                })

        # 기능 비교
        features_a = set(va.get("features", []))
        features_b = set(vb.get("features", []))
        added = features_b - features_a
        removed = features_a - features_b
        if added or removed:
            diff["changes"].append({
                "field": "features",
                "label": "기능",
                "added": list(added),
                "removed": list(removed)
            })

        return diff

    def update_template_with_version(
        self,
        template_id: str,
        data: TemplateUpdate,
        change_summary: str = "",
        created_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """버전 관리와 함께 템플릿 수정"""
        template = self.get_template(template_id)
        if not template:
            return None

        # 수정 전 버전 스냅샷 생성 (첫 번째 버전이 아닌 경우에만)
        if template_id in self.versions and len(self.versions[template_id]) > 0:
            # 변경 요약 자동 생성
            if not change_summary:
                change_summary = self._generate_change_summary(template, data)
        else:
            # 첫 번째 버전 생성
            self._create_version_snapshot(
                template_id,
                change_summary="초기 버전",
                created_by=created_by
            )

        # 템플릿 수정
        result = self.update_template(template_id, data)
        if not result:
            return None

        # 수정 후 버전 스냅샷 생성
        self._create_version_snapshot(
            template_id,
            change_summary=change_summary or "템플릿 수정",
            created_by=created_by
        )

        return result

    def _generate_change_summary(
        self,
        old_template: Dict[str, Any],
        updates: TemplateUpdate
    ) -> str:
        """변경 요약 자동 생성"""
        changes = []
        update_data = updates.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != old_template.get("name"):
            changes.append(f"이름 변경: {update_data['name']}")

        if "model_type" in update_data and update_data["model_type"] != old_template.get("model_type"):
            changes.append(f"모델 변경: {update_data['model_type']}")

        if "nodes" in update_data:
            old_count = old_template.get("node_count", 0)
            new_count = len(update_data["nodes"])
            if new_count != old_count:
                diff = new_count - old_count
                changes.append(f"노드 {'+' if diff > 0 else ''}{diff}개")

        if "detection_params" in update_data:
            changes.append("검출 파라미터 수정")

        if "features" in update_data:
            changes.append("기능 목록 수정")

        return ", ".join(changes) if changes else "템플릿 수정"

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
