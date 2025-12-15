"""Session Service - 세션 관리"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from schemas.session import SessionStatus, SessionResponse, SessionDetail


class SessionService:
    """세션 관리 서비스"""

    def __init__(self, upload_dir: Path, results_dir: Path):
        self.upload_dir = upload_dir
        self.results_dir = results_dir
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        session_id: str,
        filename: str,
        file_path: str
    ) -> Dict[str, Any]:
        """새 세션 생성"""
        now = datetime.now()

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
            "image_width": None,
            "image_height": None,
            "error_message": None,
        }

        self.sessions[session_id] = session
        self._save_session(session_id)

        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 조회"""
        # 메모리에 있으면 반환
        if session_id in self.sessions:
            return self.sessions[session_id]

        # 파일에서 로드 시도
        session = self._load_session(session_id)
        if session:
            self.sessions[session_id] = session
            return session

        return None

    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """세션 업데이트"""
        session = self.get_session(session_id)
        if not session:
            return None

        session.update(updates)
        session["updated_at"] = datetime.now().isoformat()

        self.sessions[session_id] = session
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
        detections: List[Dict[str, Any]],
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
        modified_bbox: Optional[Dict] = None
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

        self.sessions[session_id] = session
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
        # 파일에서 모든 세션 로드
        session_files = list(self.upload_dir.glob("*/session.json"))
        sessions = []

        for session_file in session_files[-limit:]:
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session = json.load(f)
                    sessions.append(session)
            except Exception:
                continue

        # 최신순 정렬
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return sessions[:limit]

    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        import shutil

        session_dir = self.upload_dir / session_id

        if session_dir.exists():
            shutil.rmtree(session_dir)

        if session_id in self.sessions:
            del self.sessions[session_id]

        return True

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

    def _load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 파일 로드"""
        session_file = self.upload_dir / session_id / "session.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
