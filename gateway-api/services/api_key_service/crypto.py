"""
API Key 암호화/복호화 유틸리티
"""

import os
import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_or_create_encryption_key(config_dir: Path) -> bytes:
    """암호화 키 가져오기 또는 생성"""
    key_env = os.getenv("SECRET_KEY")
    if key_env:
        return base64.urlsafe_b64encode(key_env.encode()[:32].ljust(32, b'\0'))

    key_file = config_dir / ".encryption_key"
    if key_file.exists():
        return key_file.read_bytes()

    # 새 키 생성
    try:
        from cryptography.fernet import Fernet
        new_key = Fernet.generate_key()
    except ImportError:
        import secrets
        new_key = base64.urlsafe_b64encode(secrets.token_bytes(32))

    key_file.write_bytes(new_key)
    key_file.chmod(0o600)
    return new_key


def encrypt(plaintext: str, encryption_key: bytes) -> str:
    """문자열 암호화"""
    try:
        from cryptography.fernet import Fernet
        f = Fernet(encryption_key)
        return f.encrypt(plaintext.encode()).decode()
    except ImportError:
        return base64.urlsafe_b64encode(plaintext.encode()).decode()


def decrypt(ciphertext: str, encryption_key: bytes) -> str:
    """문자열 복호화"""
    try:
        from cryptography.fernet import Fernet
        f = Fernet(encryption_key)
        return f.decrypt(ciphertext.encode()).decode()
    except ImportError:
        return base64.urlsafe_b64decode(ciphertext.encode()).decode()
    except Exception as e:
        logger.warning(f"Decryption failed: {e}")
        return ""
