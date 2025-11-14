#!/usr/bin/env python3
"""
역할 기반 접근 제어 (RBAC) 모듈
온프레미스 보안 강화를 위한 권한 관리 시스템
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import hashlib
import secrets
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """사용자 역할 정의"""
    ADMIN = "admin"  # 전체 시스템 관리자
    OPERATOR = "operator"  # 시스템 운영자 (학습, 배포)
    VIEWER = "viewer"  # 읽기 전용 사용자
    DEVELOPER = "developer"  # 개발자 (API 테스트, 로그 확인)


class Permission(str, Enum):
    """권한 정의"""
    # 시스템 관리
    SYSTEM_VIEW = "system:view"
    SYSTEM_MANAGE = "system:manage"
    SYSTEM_CONFIG = "system:config"

    # 모델 관리
    MODEL_VIEW = "model:view"
    MODEL_TRAIN = "model:train"
    MODEL_DEPLOY = "model:deploy"
    MODEL_DELETE = "model:delete"

    # API 관리
    API_VIEW = "api:view"
    API_TEST = "api:test"
    API_MANAGE = "api:manage"

    # Docker 관리
    DOCKER_VIEW = "docker:view"
    DOCKER_MANAGE = "docker:manage"

    # 로그 관리
    LOG_VIEW = "log:view"
    LOG_DOWNLOAD = "log:download"
    LOG_DELETE = "log:delete"

    # 사용자 관리
    USER_VIEW = "user:view"
    USER_MANAGE = "user:manage"

    # 감사 로그
    AUDIT_VIEW = "audit:view"


# 역할별 권한 매핑
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # 모든 권한
        Permission.SYSTEM_VIEW,
        Permission.SYSTEM_MANAGE,
        Permission.SYSTEM_CONFIG,
        Permission.MODEL_VIEW,
        Permission.MODEL_TRAIN,
        Permission.MODEL_DEPLOY,
        Permission.MODEL_DELETE,
        Permission.API_VIEW,
        Permission.API_TEST,
        Permission.API_MANAGE,
        Permission.DOCKER_VIEW,
        Permission.DOCKER_MANAGE,
        Permission.LOG_VIEW,
        Permission.LOG_DOWNLOAD,
        Permission.LOG_DELETE,
        Permission.USER_VIEW,
        Permission.USER_MANAGE,
        Permission.AUDIT_VIEW,
    },
    Role.OPERATOR: {
        # 운영 관련 권한
        Permission.SYSTEM_VIEW,
        Permission.MODEL_VIEW,
        Permission.MODEL_TRAIN,
        Permission.MODEL_DEPLOY,
        Permission.API_VIEW,
        Permission.API_TEST,
        Permission.DOCKER_VIEW,
        Permission.DOCKER_MANAGE,
        Permission.LOG_VIEW,
        Permission.LOG_DOWNLOAD,
    },
    Role.DEVELOPER: {
        # 개발 관련 권한
        Permission.SYSTEM_VIEW,
        Permission.MODEL_VIEW,
        Permission.API_VIEW,
        Permission.API_TEST,
        Permission.DOCKER_VIEW,
        Permission.LOG_VIEW,
        Permission.LOG_DOWNLOAD,
    },
    Role.VIEWER: {
        # 읽기 전용 권한
        Permission.SYSTEM_VIEW,
        Permission.MODEL_VIEW,
        Permission.API_VIEW,
        Permission.DOCKER_VIEW,
        Permission.LOG_VIEW,
    },
}


class User:
    """사용자 클래스"""

    def __init__(
        self,
        username: str,
        role: Role,
        password_hash: Optional[str] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        created_at: Optional[str] = None,
        last_login: Optional[str] = None,
        enabled: bool = True,
    ):
        self.username = username
        self.role = role
        self.password_hash = password_hash
        self.full_name = full_name or username
        self.email = email
        self.created_at = created_at or datetime.now().isoformat()
        self.last_login = last_login
        self.enabled = enabled

    def has_permission(self, permission: Permission) -> bool:
        """권한 확인"""
        if not self.enabled:
            return False
        return permission in ROLE_PERMISSIONS.get(self.role, set())

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """여러 권한 중 하나라도 있는지 확인"""
        return any(self.has_permission(p) for p in permissions)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (비밀번호 제외)"""
        return {
            "username": self.username,
            "role": self.role.value,
            "full_name": self.full_name,
            "email": self.email,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "enabled": self.enabled,
            "permissions": [p.value for p in ROLE_PERMISSIONS.get(self.role, set())],
        }


class RBACManager:
    """RBAC 관리 클래스"""

    def __init__(self, users_file: str = "users.json"):
        self.users_file = Path(users_file)
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}  # session_token -> user_info

        # 사용자 데이터 로드
        self._load_users()

        # 기본 관리자 계정 생성 (없는 경우)
        if "admin" not in self.users:
            self.create_user(
                username="admin",
                password="changeme123",
                role=Role.ADMIN,
                full_name="System Administrator",
            )
            logger.warning("기본 관리자 계정이 생성되었습니다. 비밀번호를 변경하세요!")

    def _load_users(self):
        """사용자 데이터 로드"""
        if self.users_file.exists():
            try:
                with open(self.users_file, "r") as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        self.users[username] = User(
                            username=username,
                            role=Role(user_data["role"]),
                            password_hash=user_data["password_hash"],
                            full_name=user_data.get("full_name"),
                            email=user_data.get("email"),
                            created_at=user_data.get("created_at"),
                            last_login=user_data.get("last_login"),
                            enabled=user_data.get("enabled", True),
                        )
                logger.info(f"사용자 데이터 로드 완료: {len(self.users)} 명")
            except Exception as e:
                logger.error(f"사용자 데이터 로드 실패: {e}")

    def _save_users(self):
        """사용자 데이터 저장"""
        try:
            data = {}
            for username, user in self.users.items():
                data[username] = {
                    "role": user.role.value,
                    "password_hash": user.password_hash,
                    "full_name": user.full_name,
                    "email": user.email,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                    "enabled": user.enabled,
                }

            with open(self.users_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"사용자 데이터 저장 완료: {len(self.users)} 명")
        except Exception as e:
            logger.error(f"사용자 데이터 저장 실패: {e}")

    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해시"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(
        self,
        username: str,
        password: str,
        role: Role,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> User:
        """사용자 생성"""
        if username in self.users:
            raise ValueError(f"사용자가 이미 존재합니다: {username}")

        user = User(
            username=username,
            role=role,
            password_hash=self.hash_password(password),
            full_name=full_name,
            email=email,
        )

        self.users[username] = user
        self._save_users()

        logger.info(f"사용자 생성: {username} (role: {role.value})")
        return user

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """사용자 인증 및 세션 토큰 생성"""
        user = self.users.get(username)

        if not user:
            logger.warning(f"존재하지 않는 사용자: {username}")
            return None

        if not user.enabled:
            logger.warning(f"비활성화된 사용자: {username}")
            return None

        password_hash = self.hash_password(password)
        if user.password_hash != password_hash:
            logger.warning(f"잘못된 비밀번호: {username}")
            return None

        # 세션 토큰 생성
        session_token = secrets.token_urlsafe(32)

        # 세션 정보 저장
        self.sessions[session_token] = {
            "username": username,
            "role": user.role.value,
            "created_at": datetime.now().isoformat(),
        }

        # 마지막 로그인 시간 업데이트
        user.last_login = datetime.now().isoformat()
        self._save_users()

        logger.info(f"사용자 로그인: {username}")
        return session_token

    def validate_session(self, session_token: str) -> Optional[User]:
        """세션 검증 및 사용자 반환"""
        session = self.sessions.get(session_token)

        if not session:
            return None

        username = session["username"]
        user = self.users.get(username)

        if not user or not user.enabled:
            return None

        return user

    def logout(self, session_token: str):
        """로그아웃"""
        if session_token in self.sessions:
            username = self.sessions[session_token]["username"]
            del self.sessions[session_token]
            logger.info(f"사용자 로그아웃: {username}")

    def check_permission(self, session_token: str, permission: Permission) -> bool:
        """권한 확인"""
        user = self.validate_session(session_token)

        if not user:
            return False

        return user.has_permission(permission)

    def get_user(self, username: str) -> Optional[User]:
        """사용자 조회"""
        return self.users.get(username)

    def list_users(self) -> List[Dict[str, Any]]:
        """모든 사용자 목록"""
        return [user.to_dict() for user in self.users.values()]

    def update_user(
        self,
        username: str,
        role: Optional[Role] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> bool:
        """사용자 정보 수정"""
        user = self.users.get(username)

        if not user:
            return False

        if role is not None:
            user.role = role
        if full_name is not None:
            user.full_name = full_name
        if email is not None:
            user.email = email
        if enabled is not None:
            user.enabled = enabled

        self._save_users()
        logger.info(f"사용자 정보 수정: {username}")
        return True

    def change_password(self, username: str, new_password: str) -> bool:
        """비밀번호 변경"""
        user = self.users.get(username)

        if not user:
            return False

        user.password_hash = self.hash_password(new_password)
        self._save_users()

        logger.info(f"비밀번호 변경: {username}")
        return True

    def delete_user(self, username: str) -> bool:
        """사용자 삭제"""
        if username == "admin":
            logger.error("관리자 계정은 삭제할 수 없습니다")
            return False

        if username in self.users:
            del self.users[username]
            self._save_users()
            logger.info(f"사용자 삭제: {username}")
            return True

        return False


# 전역 RBAC 관리자 인스턴스
rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """RBAC 관리자 인스턴스 가져오기"""
    global rbac_manager
    if rbac_manager is None:
        rbac_manager = RBACManager()
    return rbac_manager


def require_permission(permission: Permission):
    """권한 확인 데코레이터 (FastAPI용)"""
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # FastAPI Request에서 세션 토큰 추출
            # 실제 구현 시 header 또는 cookie에서 추출
            session_token = kwargs.get("session_token")

            if not session_token:
                from fastapi import HTTPException

                raise HTTPException(status_code=401, detail="인증이 필요합니다")

            rbac = get_rbac_manager()
            if not rbac.check_permission(session_token, permission):
                from fastapi import HTTPException

                raise HTTPException(status_code=403, detail="권한이 없습니다")

            return await func(*args, **kwargs)

        return wrapper

    return decorator
