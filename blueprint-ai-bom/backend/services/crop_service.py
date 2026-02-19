"""CropService - 서버사이드 이미지 크롭 서비스

검출 영역 크롭, 컨텍스트 이미지, 참조 이미지 제공
Agent Verification UI에서 사용
"""
import logging
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Dict, Any

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# 참조 이미지 디렉토리
BASE_DIR = Path(__file__).parent.parent
CLASS_EXAMPLES_DIR = BASE_DIR / "class_examples"
CLASS_EXAMPLES_PID_DIR = BASE_DIR / "class_examples_pid"
CLASS_EXAMPLES_BOM_DIR = BASE_DIR / "class_examples_bom_detector"


class CropService:
    """서버사이드 이미지 크롭 서비스"""

    def __init__(self, session_service):
        self.session_service = session_service

    def _get_session_and_detection(
        self, session_id: str, detection_id: str
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """세션과 검출 항목 조회"""
        session = self.session_service.get_session(session_id)
        if not session:
            return None, None

        for det in session.get("detections", []):
            if det.get("id") == detection_id:
                return session, det
        return session, None

    def _load_image(self, file_path: str) -> Optional[Image.Image]:
        """이미지 로드"""
        try:
            return Image.open(file_path).convert("RGB")
        except Exception as e:
            logger.error(f"이미지 로드 실패: {file_path} - {e}")
            return None

    def _to_jpeg_bytes(self, img: Image.Image, quality: int = 85) -> bytes:
        """PIL Image → JPEG bytes"""
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()

    def get_detection_crop(
        self, session_id: str, detection_id: str, padding: int = 20
    ) -> Optional[bytes]:
        """검출 영역 크롭 -> JPEG bytes (400x400 max 리사이즈)"""
        session, detection = self._get_session_and_detection(session_id, detection_id)
        if not session or not detection:
            return None

        img = self._load_image(session["file_path"])
        if not img:
            return None

        bbox = detection.get("bbox", {})
        x1 = max(0, int(bbox.get("x1", 0)) - padding)
        y1 = max(0, int(bbox.get("y1", 0)) - padding)
        x2 = min(img.width, int(bbox.get("x2", 0)) + padding)
        y2 = min(img.height, int(bbox.get("y2", 0)) + padding)

        cropped = img.crop((x1, y1, x2, y2))

        # 400x400 내로 리사이즈 (aspect ratio 유지)
        cropped.thumbnail((400, 400), Image.LANCZOS)

        return self._to_jpeg_bytes(cropped)

    def get_context_image(
        self, session_id: str, detection_id: str
    ) -> Optional[bytes]:
        """전체 도면 축소 + 검출 위치 빨간 박스 표시 -> JPEG bytes"""
        session, detection = self._get_session_and_detection(session_id, detection_id)
        if not session or not detection:
            return None

        img = self._load_image(session["file_path"])
        if not img:
            return None

        # 800px 폭으로 리사이즈
        ratio = 800 / img.width
        new_h = int(img.height * ratio)
        img = img.resize((800, new_h), Image.LANCZOS)

        # 검출 bbox에 빨간 박스 그리기
        bbox = detection.get("bbox", {})
        draw = ImageDraw.Draw(img)
        x1 = int(bbox.get("x1", 0) * ratio)
        y1 = int(bbox.get("y1", 0) * ratio)
        x2 = int(bbox.get("x2", 0) * ratio)
        y2 = int(bbox.get("y2", 0) * ratio)

        for i in range(3):  # 3px 두께
            draw.rectangle(
                [x1 - i, y1 - i, x2 + i, y2 + i],
                outline="red"
            )

        return self._to_jpeg_bytes(img)

    def get_reference_images(
        self, class_name: str, drawing_type: str = "electrical"
    ) -> List[bytes]:
        """클래스 참조 이미지 반환 (class_examples/ 폴더)"""
        if drawing_type == "pid":
            examples_dir = CLASS_EXAMPLES_PID_DIR
        elif drawing_type == "bom_detector":
            examples_dir = CLASS_EXAMPLES_BOM_DIR
        else:
            examples_dir = CLASS_EXAMPLES_DIR

        if not examples_dir.exists():
            return []

        # class_name을 소문자로 변환하여 매칭
        target = class_name.lower().replace(" ", "_")
        results = []

        for f in sorted(examples_dir.glob("*.jpg")):
            fname = f.stem.lower()
            if target in fname:
                img = self._load_image(str(f))
                if img:
                    img.thumbnail((200, 200), Image.LANCZOS)
                    results.append(self._to_jpeg_bytes(img))
                if len(results) >= 3:
                    break

        return results
