"""Validation 패키지 — 분석 결과 품질 평가 + 자기수정 루프

사용법:
    from services.validation import validate_and_correct

    result = {"od": "670", "id": "440", "width": "260"}
    context = {"session_name": "스러스트베어링 ASSY (OD670×ID440)"}
    corrected, report = validate_and_correct(result, context)
"""

from .engine import ValidationEngine, get_engine
from .corrector import validate_and_correct

__all__ = ["ValidationEngine", "get_engine", "validate_and_correct"]
