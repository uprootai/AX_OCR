"""
OCR API 통합 기본 설정

모든 OCR API의 기본 설정을 중앙에서 관리
각 API는 자체 config/defaults.py를 가지며, 이 파일은 Gateway에서 통합 관리용으로 사용

지원 OCR API (8개):
- edocr2: 한국어 치수/GD&T 인식
- paddleocr: 다국어 OCR (PP-OCRv5)
- tesseract: 전통적 OCR 엔진
- trocr: Transformer 기반 OCR (인쇄체/필기체)
- surya: 90+ 언어 지원, 레이아웃 분석
- doctr: 2단계 파이프라인 (검출+인식)
- easyocr: 80+ 언어 지원, CPU 친화적
- ensemble: 4엔진 가중 투표
"""

from typing import Dict, Any, Optional, List


# OCR API별 기본 설정
OCR_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "edocr2": {
        "name": "eDOCr2",
        "description": "한국어 치수/GD&T 인식",
        "port": 5002,
        "profiles": ["full", "dimension_only", "gdt_only", "text_only", "accurate", "fast", "debug"],
        "default_profile": "full",
        "base_params": {
            "extract_dimensions": True,
            "extract_gdt": True,
            "extract_text": True,
            "use_vl_model": False,
            "visualize": False,
            "use_gpu_preprocessing": False,
        },
    },
    "paddleocr": {
        "name": "PaddleOCR",
        "description": "다국어 OCR (PP-OCRv5)",
        "port": 5006,
        "profiles": ["general", "korean", "engineering", "accurate", "fast", "debug"],
        "default_profile": "general",
        "base_params": {
            "model_version": "PP-OCRv5",
            "lang": "en",
            "det_db_thresh": 0.3,
            "det_db_box_thresh": 0.6,
            "use_textline_orientation": True,
            "min_confidence": 0.5,
            "visualize": False,
        },
    },
    "tesseract": {
        "name": "Tesseract",
        "description": "전통적 OCR 엔진",
        "port": 5008,
        "profiles": ["general", "korean", "engineering", "single_line", "sparse", "block", "raw"],
        "default_profile": "general",
        "base_params": {
            "lang": "eng",
            "psm": "3",
            "oem": "3",
            "output_type": "data",
        },
    },
    "trocr": {
        "name": "TrOCR",
        "description": "Transformer 기반 OCR",
        "port": 5009,
        "profiles": ["general", "printed", "handwritten", "engineering", "accurate", "fast"],
        "default_profile": "general",
        "base_params": {
            "model_type": "printed",
            "max_length": 64,
            "num_beams": 4,
        },
    },
    "surya": {
        "name": "Surya OCR",
        "description": "90+ 언어 지원",
        "port": 5013,
        "profiles": ["general", "korean", "english", "multilingual", "document", "engineering", "debug"],
        "default_profile": "general",
        "base_params": {
            "languages": "ko,en",
            "detect_layout": False,
            "visualize": False,
        },
    },
    "doctr": {
        "name": "DocTR",
        "description": "2단계 파이프라인",
        "port": 5014,
        "profiles": ["general", "document", "structured", "engineering", "scanned", "debug"],
        "default_profile": "general",
        "base_params": {
            "straighten_pages": False,
            "export_as_xml": False,
            "visualize": False,
        },
    },
    "easyocr": {
        "name": "EasyOCR",
        "description": "80+ 언어 지원",
        "port": 5015,
        "profiles": ["general", "korean", "english", "document", "engineering", "fast", "debug"],
        "default_profile": "general",
        "base_params": {
            "languages": "ko,en",
            "detail": True,
            "paragraph": False,
            "batch_size": 1,
            "visualize": False,
        },
    },
    "ensemble": {
        "name": "OCR Ensemble",
        "description": "4엔진 가중 투표",
        "port": 5011,
        "profiles": ["general", "dimension", "korean", "engineering", "accurate", "fast", "handwritten"],
        "default_profile": "general",
        "base_params": {
            "edocr2_weight": 0.40,
            "paddleocr_weight": 0.35,
            "tesseract_weight": 0.15,
            "trocr_weight": 0.10,
            "similarity_threshold": 0.7,
            "engines": "all",
        },
    },
}

# 용도별 권장 OCR 설정
USE_CASE_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "dimension": {
        "description": "치수 인식",
        "primary": "edocr2",
        "profile": "dimension_only",
        "fallback": "ensemble",
        "fallback_profile": "dimension",
    },
    "korean_document": {
        "description": "한국어 문서",
        "primary": "paddleocr",
        "profile": "korean",
        "fallback": "easyocr",
        "fallback_profile": "korean",
    },
    "engineering_drawing": {
        "description": "기계/전기 도면",
        "primary": "edocr2",
        "profile": "full",
        "fallback": "paddleocr",
        "fallback_profile": "engineering",
    },
    "handwritten": {
        "description": "필기체 인식",
        "primary": "trocr",
        "profile": "handwritten",
        "fallback": "ensemble",
        "fallback_profile": "handwritten",
    },
    "multilingual": {
        "description": "다국어 인식",
        "primary": "surya",
        "profile": "multilingual",
        "fallback": "easyocr",
        "fallback_profile": "general",
    },
    "high_accuracy": {
        "description": "최대 정확도",
        "primary": "ensemble",
        "profile": "accurate",
        "fallback": "edocr2",
        "fallback_profile": "accurate",
    },
    "fast_processing": {
        "description": "빠른 처리",
        "primary": "paddleocr",
        "profile": "fast",
        "fallback": "ensemble",
        "fallback_profile": "fast",
    },
}


def get_ocr_config(ocr_type: str) -> Optional[Dict[str, Any]]:
    """
    특정 OCR API의 설정 반환

    Args:
        ocr_type: OCR API 타입 (edocr2, paddleocr, tesseract, trocr, surya, doctr, easyocr, ensemble)

    Returns:
        설정 딕셔너리 또는 None
    """
    return OCR_DEFAULTS.get(ocr_type)


def get_ocr_base_params(ocr_type: str) -> Dict[str, Any]:
    """
    특정 OCR API의 기본 파라미터 반환

    Args:
        ocr_type: OCR API 타입

    Returns:
        기본 파라미터 딕셔너리
    """
    config = OCR_DEFAULTS.get(ocr_type)
    if config:
        return config.get("base_params", {}).copy()
    return {}


def get_available_profiles(ocr_type: str) -> List[str]:
    """
    특정 OCR API의 사용 가능한 프로파일 목록

    Args:
        ocr_type: OCR API 타입

    Returns:
        프로파일 목록
    """
    config = OCR_DEFAULTS.get(ocr_type)
    if config:
        return config.get("profiles", [])
    return []


def get_recommendation(use_case: str) -> Optional[Dict[str, Any]]:
    """
    용도에 따른 OCR 권장 설정 반환

    Args:
        use_case: 용도 (dimension, korean_document, engineering_drawing, handwritten, multilingual, high_accuracy, fast_processing)

    Returns:
        권장 설정 딕셔너리
    """
    return USE_CASE_RECOMMENDATIONS.get(use_case)


def list_ocr_apis() -> Dict[str, str]:
    """
    사용 가능한 OCR API 목록과 설명 반환
    """
    return {
        ocr_type: config.get("description", config.get("name", ocr_type))
        for ocr_type, config in OCR_DEFAULTS.items()
    }


def list_use_cases() -> Dict[str, str]:
    """
    지원되는 용도 목록과 설명 반환
    """
    return {
        use_case: config.get("description", use_case)
        for use_case, config in USE_CASE_RECOMMENDATIONS.items()
    }
