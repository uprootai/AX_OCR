"""Session Service - 세션 관리"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

from schemas.session import (
    SessionStatus,
    SessionResponse,
    SessionDetail,
    ImageReviewStatus,
    SessionImageProgress,
)
from schemas.classification import DrawingType
from schemas.typed_dicts import SessionData, DetectionDict, BBoxDict


import secrets


_UNSET = object()


class SessionService:
    """세션 관리 서비스"""

    def __init__(self, upload_dir: Path, results_dir: Path):
        self.upload_dir = upload_dir
        self.results_dir = results_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, SessionData] = {}
        self._session_list_cache: Optional[List[str]] = None
        self._project_session_cache: Dict[str, List[str]] = {}
        self._session_ids_by_project: Dict[str, Set[str]] = {}
        self._sessions_loaded = False
        self._load_all_sessions()

    def _load_all_sessions(self):
        """디스크의 세션 파일을 메모리로 초기화"""
        self.sessions.clear()
        self._session_ids_by_project.clear()

        for session_file in self.upload_dir.glob("*/session.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session = json.load(f)
            except Exception:
                continue

            session_id = session.get("session_id") or session_file.parent.name
            self._store_session(session_id, session, invalidate_cache=False)

        self._sessions_loaded = True
        self.invalidate_session_list_cache()

    def invalidate_session_cache(self, reload_from_disk: bool = False):
        """세션 메모리 캐시 전체 무효화"""
        self.sessions.clear()
        self._session_ids_by_project.clear()
        self._sessions_loaded = False
        self.invalidate_session_list_cache()

        if reload_from_disk:
            self._load_all_sessions()

    def invalidate_session_list_cache(self):
        """세션 목록/프로젝트별 파생 캐시 무효화"""
        self._session_list_cache = None
        self._project_session_cache.clear()

    def _ensure_sessions_loaded(self):
        """세션 메모리 캐시 초기화 보장"""
        if not self._sessions_loaded:
            self._load_all_sessions()

    def _get_sorted_session_ids(self) -> List[str]:
        """생성일 기준 최신순 세션 ID 목록 반환"""
        self._ensure_sessions_loaded()

        if self._session_list_cache is None:
            self._session_list_cache = sorted(
                self.sessions.keys(),
                key=lambda session_id: self.sessions[session_id].get("created_at", ""),
                reverse=True,
            )

        return self._session_list_cache

    def _add_project_index(self, session_id: str, project_id: Optional[str]):
        """프로젝트별 세션 인덱스 추가"""
        if not project_id:
            return
        self._session_ids_by_project.setdefault(project_id, set()).add(session_id)

    def _remove_project_index(self, session_id: str, project_id: Optional[str]):
        """프로젝트별 세션 인덱스 제거"""
        if not project_id:
            return

        session_ids = self._session_ids_by_project.get(project_id)
        if not session_ids:
            return

        session_ids.discard(session_id)
        if not session_ids:
            del self._session_ids_by_project[project_id]

    def _store_session(
        self,
        session_id: str,
        session: Dict[str, Any],
        invalidate_cache: bool = True,
        previous_project_id: Any = _UNSET,
    ):
        """세션 메모리 저장 및 프로젝트 인덱스 동기화"""
        existing = self.sessions.get(session_id)
        if existing:
            project_id_to_remove = (
                existing.get("project_id")
                if previous_project_id is _UNSET
                else previous_project_id
            )
            self._remove_project_index(session_id, project_id_to_remove)

        session["session_id"] = session_id
        self.sessions[session_id] = session
        self._add_project_index(session_id, session.get("project_id"))

        if invalidate_cache:
            self.invalidate_session_list_cache()

    def _copy_session_for_response(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """목록 응답용 세션 복사본 반환"""
        session_copy = session.copy()
        session_copy.pop("image_base64", None)
        return session_copy

    def create_session(
        self,
        session_id: str,
        filename: str,
        file_path: str,
        drawing_type: str = "auto",  # 빌더에서 설정한 도면 타입
        image_width: int = None,
        image_height: int = None,
        features: List[str] = None,  # 활성화된 기능 목록 (2025-12-24)
        # Phase 2: 프로젝트/템플릿 연결
        project_id: str = None,
        template_id: str = None,
        model_type: str = None,
        # BOM 메타데이터
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """새 세션 생성"""
        now = datetime.now()

        # drawing_type 유효성 검사
        try:
            dt = DrawingType(drawing_type)
        except ValueError:
            dt = DrawingType.AUTO

        session = {
            "session_id": session_id,
            "filename": filename,
            "file_path": file_path,
            "status": SessionStatus.UPLOADED,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "detections": [],
            "detection_count": 0,
            "verification_status": {},
            "verified_count": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "bom_data": None,
            "bom_generated": False,
            "image_width": image_width,
            "image_height": image_height,
            "error_message": None,
            # 도면 분류 정보
            "drawing_type": dt.value,
            "drawing_type_source": "builder" if dt != DrawingType.AUTO else "pending",
            "drawing_type_confidence": None,
            "vlm_classification_result": None,
            # 활성화된 기능 목록 (2025-12-24: 기능 기반 재설계)
            "features": features or [],
            # Phase 2: 프로젝트/템플릿 연결
            "project_id": project_id,
            "project_name": None,  # 조인 시 채움
            "template_id": template_id,
            "template_name": None,  # 조인 시 채움
            "model_type": model_type,
            # BOM 메타데이터
            "metadata": metadata,
        }

        self._store_session(session_id, session)
        self._save_session(session_id)

        return session

    def create_locked_session(
        self,
        workflow_name: str,
        workflow_definition: Dict[str, Any],
        lock_level: str = "full",
        allowed_parameters: List[str] = None,
        customer_name: str = None,
        expires_in_days: int = 30,
    ) -> Dict[str, Any]:
        """BlueprintFlow 워크플로우로부터 잠긴 세션 생성

        Args:
            workflow_name: 워크플로우 이름
            workflow_definition: 워크플로우 정의 (nodes, edges)
            lock_level: 잠금 수준 ('full', 'parameters', 'none')
            allowed_parameters: 수정 가능한 파라미터 목록
            customer_name: 고객명
            expires_in_days: 만료 기간 (일)

        Returns:
            생성된 세션 정보 (session_id, access_token, expires_at 포함)
        """
        from datetime import timedelta

        session_id = str(uuid.uuid4())
        access_token = secrets.token_urlsafe(32)
        now = datetime.now()
        expires_at = now + timedelta(days=expires_in_days)

        session = {
            "session_id": session_id,
            "filename": f"workflow_{workflow_name}",
            "file_path": "",  # 이미지는 나중에 업로드
            "status": SessionStatus.CREATED,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "detections": [],
            "detection_count": 0,
            "verification_status": {},
            "verified_count": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "bom_data": None,
            "bom_generated": False,
            "image_width": None,
            "image_height": None,
            "error_message": None,
            # 도면 분류 정보
            "drawing_type": "auto",
            "drawing_type_source": "workflow",
            "drawing_type_confidence": None,
            "vlm_classification_result": None,
            # 활성화된 기능 목록
            "features": [],
            # 프로젝트/템플릿 연결
            "project_id": None,
            "project_name": None,
            "template_id": None,
            "template_name": None,
            "model_type": None,
            # Phase 2G: 워크플로우 잠금 시스템
            "workflow_locked": True,
            "workflow_definition": workflow_definition,
            "lock_level": lock_level,
            "allowed_parameters": allowed_parameters or [],
            "customer_name": customer_name,
            "access_token": access_token,
            "expires_at": expires_at.isoformat(),
            # 이미지 목록 초기화
            "images": [],
            "image_count": 0,
            "images_approved": 0,
            "images_rejected": 0,
            "images_modified": 0,
            "images_pending": 0,
            "export_ready": False,
        }

        self._store_session(session_id, session)
        self._save_session(session_id)

        return session

    def validate_session_access(
        self,
        session_id: str,
        access_token: str = None,
    ) -> bool:
        """세션 접근 권한 검증

        Args:
            session_id: 세션 ID
            access_token: 접근 토큰 (선택)

        Returns:
            접근 가능 여부
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # 워크플로우 잠금 세션인 경우 토큰 검증
        if session.get("workflow_locked"):
            stored_token = session.get("access_token")
            if stored_token and access_token != stored_token:
                return False

            # 만료 시간 확인
            expires_at = session.get("expires_at")
            if expires_at:
                from datetime import datetime as dt
                try:
                    expire_time = dt.fromisoformat(expires_at.replace("Z", "+00:00"))
                    if dt.now() > expire_time:
                        return False
                except (ValueError, AttributeError):
                    pass

        return True

    def validate_parameter_modification(
        self,
        session_id: str,
        parameters: Dict[str, Any],
    ) -> tuple[bool, str]:
        """파라미터 수정 권한 검증

        Args:
            session_id: 세션 ID
            parameters: 수정할 파라미터

        Returns:
            (허용 여부, 에러 메시지)
        """
        session = self.get_session(session_id)
        if not session:
            return False, "세션을 찾을 수 없습니다"

        lock_level = session.get("lock_level", "none")

        if lock_level == "full":
            return False, "이 세션은 파라미터 수정이 허용되지 않습니다"

        if lock_level == "parameters":
            allowed = session.get("allowed_parameters", [])
            for param in parameters.keys():
                if param not in allowed:
                    return False, f"파라미터 '{param}' 수정이 허용되지 않습니다"

        return True, ""

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 조회"""
        self._ensure_sessions_loaded()
        return self.sessions.get(session_id)

    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """세션 업데이트"""
        session = self.get_session(session_id)
        if not session:
            return None

        previous_project_id = session.get("project_id")
        session.update(updates)
        session["updated_at"] = datetime.now().isoformat()

        self._store_session(
            session_id,
            session,
            previous_project_id=previous_project_id,
        )
        self._save_session(session_id)

        return session

    def update_status(
        self,
        session_id: str,
        status: SessionStatus,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """세션 상태 업데이트"""
        updates = {"status": status}
        if error_message:
            updates["error_message"] = error_message

        return self.update_session(session_id, updates)

    def set_detections(
        self,
        session_id: str,
        detections: List[DetectionDict],
        image_width: int,
        image_height: int
    ) -> Optional[Dict[str, Any]]:
        """검출 결과 저장"""
        updates = {
            "detections": detections,
            "detection_count": len(detections),
            "status": SessionStatus.DETECTED,
            "image_width": image_width,
            "image_height": image_height,
            "verification_status": {d["id"]: "pending" for d in detections},
        }
        return self.update_session(session_id, updates)

    def update_verification(
        self,
        session_id: str,
        detection_id: str,
        status: str,
        modified_class_name: Optional[str] = None,
        modified_bbox: Optional[BBoxDict] = None
    ) -> Optional[Dict[str, Any]]:
        """검증 상태 업데이트"""
        session = self.get_session(session_id)
        if not session:
            return None

        # 검증 상태 업데이트
        session["verification_status"][detection_id] = status

        # 검출 결과에서 해당 항목 업데이트
        for detection in session["detections"]:
            if detection["id"] == detection_id:
                detection["verification_status"] = status
                if modified_class_name:
                    detection["modified_class_name"] = modified_class_name
                if modified_bbox:
                    detection["modified_bbox"] = modified_bbox
                break

        # 통계 업데이트
        statuses = list(session["verification_status"].values())
        session["verified_count"] = len([s for s in statuses if s != "pending"])
        session["approved_count"] = len([s for s in statuses if s in ("approved", "modified", "manual")])
        session["rejected_count"] = len([s for s in statuses if s == "rejected"])

        self._store_session(session_id, session)
        self._save_session(session_id)

        return session

    def set_bom_data(
        self,
        session_id: str,
        bom_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """BOM 데이터 저장"""
        updates = {
            "bom_data": bom_data,
            "bom_generated": True,
            "status": SessionStatus.COMPLETED,
        }
        return self.update_session(session_id, updates)

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """세션 목록 조회"""
        session_ids = self._get_sorted_session_ids()[:limit]
        return [self._copy_session_for_response(self.sessions[session_id]) for session_id in session_ids]

    def list_sessions_by_project(
        self,
        project_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """프로젝트별 세션 목록 조회 (Phase 2)"""
        self._ensure_sessions_loaded()

        if project_id not in self._project_session_cache:
            self._project_session_cache[project_id] = [
                session_id
                for session_id in self._get_sorted_session_ids()
                if session_id in self._session_ids_by_project.get(project_id, set())
            ]

        session_ids = self._project_session_cache[project_id][:limit]
        return [self._copy_session_for_response(self.sessions[session_id]) for session_id in session_ids]

    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        import shutil

        session_dir = self.upload_dir / session_id

        if session_dir.exists():
            shutil.rmtree(session_dir)

        session = self.sessions.pop(session_id, None)
        if session:
            self._remove_project_index(session_id, session.get("project_id"))

        self.invalidate_session_list_cache()
        return True

    def delete_all_sessions(self) -> int:
        """모든 세션 삭제"""
        import shutil

        # 모든 세션 디렉토리 찾기
        session_dirs = [d for d in self.upload_dir.iterdir() if d.is_dir()]
        deleted_count = 0

        for session_dir in session_dirs:
            try:
                shutil.rmtree(session_dir)
                deleted_count += 1
            except Exception:
                continue

        # 메모리에서도 삭제
        self.sessions.clear()
        self._session_ids_by_project.clear()
        self._sessions_loaded = True
        self.invalidate_session_list_cache()

        return deleted_count

    # =========================================================================
    # Phase 2C: 다중 이미지 세션 관리
    # =========================================================================

    def add_image(
        self,
        session_id: str,
        image_id: str,
        filename: str,
        file_path: str,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
        thumbnail_base64: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """세션에 이미지 추가"""
        session = self.get_session(session_id)
        if not session:
            return None

        # images 리스트 초기화
        if "images" not in session:
            session["images"] = []

        # 새 이미지 생성
        new_image = {
            "image_id": image_id,
            "filename": filename,
            "file_path": file_path,
            "review_status": ImageReviewStatus.PENDING.value,
            "detections": [],
            "detection_count": 0,
            "verified_count": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "image_width": image_width,
            "image_height": image_height,
            "thumbnail_base64": thumbnail_base64,
            "reviewed_at": None,
            "reviewed_by": None,
            "review_notes": None,
            "order_index": len(session["images"]),
        }

        session["images"].append(new_image)
        self._update_image_counts(session)
        self._save_session(session_id)

        return new_image

    def get_images(self, session_id: str) -> List[Dict[str, Any]]:
        """세션의 이미지 목록 조회"""
        session = self.get_session(session_id)
        if not session:
            return []
        return session.get("images", [])

    def get_image(
        self,
        session_id: str,
        image_id: str
    ) -> Optional[Dict[str, Any]]:
        """세션의 특정 이미지 조회"""
        images = self.get_images(session_id)
        for img in images:
            if img.get("image_id") == image_id:
                return img
        return None

    def update_image(
        self,
        session_id: str,
        image_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """이미지 정보 업데이트"""
        session = self.get_session(session_id)
        if not session:
            return None

        images = session.get("images", [])
        for img in images:
            if img.get("image_id") == image_id:
                img.update(updates)
                img["updated_at"] = datetime.now().isoformat()
                self._update_image_counts(session)
                self._save_session(session_id)
                return img
        return None

    def update_image_review(
        self,
        session_id: str,
        image_id: str,
        review_status: str,
        reviewed_by: Optional[str] = None,
        review_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """이미지 검토 상태 업데이트"""
        updates = {
            "review_status": review_status,
            "reviewed_at": datetime.now().isoformat(),
        }
        if reviewed_by:
            updates["reviewed_by"] = reviewed_by
        if review_notes:
            updates["review_notes"] = review_notes

        return self.update_image(session_id, image_id, updates)

    def set_image_detections(
        self,
        session_id: str,
        image_id: str,
        detections: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """이미지 검출 결과 저장"""
        updates = {
            "detections": detections,
            "detection_count": len(detections),
            "review_status": ImageReviewStatus.PROCESSED.value,
            "verification_status": {d["id"]: "pending" for d in detections},
        }
        return self.update_image(session_id, image_id, updates)

    def delete_image(
        self,
        session_id: str,
        image_id: str
    ) -> bool:
        """이미지 삭제"""
        import shutil

        session = self.get_session(session_id)
        if not session:
            return False

        images = session.get("images", [])
        original_count = len(images)

        # 이미지 찾기 및 파일 삭제
        for img in images:
            if img.get("image_id") == image_id:
                file_path = Path(img.get("file_path", ""))
                if file_path.exists():
                    file_path.unlink()
                break

        # 목록에서 제거
        session["images"] = [
            img for img in images
            if img.get("image_id") != image_id
        ]

        # 순서 재정렬
        for i, img in enumerate(session["images"]):
            img["order_index"] = i

        self._update_image_counts(session)
        self._save_session(session_id)

        return len(session["images"]) < original_count

    def get_image_progress(self, session_id: str) -> SessionImageProgress:
        """세션 이미지 진행률 조회"""
        session = self.get_session(session_id)
        if not session:
            return SessionImageProgress()

        images = session.get("images", [])
        total = len(images)

        if total == 0:
            return SessionImageProgress()

        counts = {
            "pending": 0,
            "processed": 0,
            "approved": 0,
            "rejected": 0,
            "modified": 0,
            "manual_labeled": 0,
        }

        for img in images:
            status = img.get("review_status", "pending")
            if status in counts:
                counts[status] += 1

        # 완료 항목 (approved, modified, manual_labeled)
        completed = counts["approved"] + counts["modified"] + counts["manual_labeled"]
        progress = (completed / total) * 100 if total > 0 else 0

        # Export 가능 여부 (pending, processed가 없고, rejected만 있지 않을 때)
        all_reviewed = counts["pending"] == 0 and counts["processed"] == 0
        export_ready = all_reviewed and completed > 0

        return SessionImageProgress(
            total_images=total,
            pending_count=counts["pending"],
            processed_count=counts["processed"],
            approved_count=counts["approved"],
            rejected_count=counts["rejected"],
            modified_count=counts["modified"],
            manual_labeled_count=counts["manual_labeled"],
            progress_percent=round(progress, 1),
            all_reviewed=all_reviewed,
            export_ready=export_ready,
        )

    def _update_image_counts(self, session: Dict[str, Any]):
        """세션의 이미지 카운트 업데이트"""
        images = session.get("images", [])

        counts = {
            "pending": 0,
            "processed": 0,
            "approved": 0,
            "rejected": 0,
            "modified": 0,
            "manual_labeled": 0,
        }

        for img in images:
            status = img.get("review_status", "pending")
            if status in counts:
                counts[status] += 1

        session["image_count"] = len(images)
        session["images_approved"] = counts["approved"]
        session["images_rejected"] = counts["rejected"]
        session["images_modified"] = counts["modified"]
        session["images_pending"] = counts["pending"] + counts["processed"]

        # Export 가능 여부
        completed = counts["approved"] + counts["modified"] + counts["manual_labeled"]
        all_reviewed = counts["pending"] == 0 and counts["processed"] == 0
        session["export_ready"] = all_reviewed and completed > 0

    def _save_session(self, session_id: str):
        """세션 파일 저장"""
        session = self.sessions.get(session_id)
        if not session:
            return

        session_dir = self.upload_dir / session_id
        session_dir.mkdir(exist_ok=True)

        session_file = session_dir / "session.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2, default=str)

        self._sessions_loaded = True
        self.invalidate_session_list_cache()

    def _load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 파일 로드"""
        session_file = self.upload_dir / session_id / "session.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session = json.load(f)
                session["session_id"] = session.get("session_id", session_id)
                return session
        except Exception:
            return None
