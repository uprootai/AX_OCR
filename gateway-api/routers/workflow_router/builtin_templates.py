"""
Built-in Templates
BOM API 연결 실패 시 폴백으로 사용하는 내장 템플릿 데이터
"""

from typing import Optional, Dict, Any, List


def get_builtin_templates() -> List[Dict[str, Any]]:
    """내장 기본 템플릿 목록"""
    return [
        {
            "id": "yolo-detection",
            "name": "YOLO 객체 검출",
            "description": "YOLO를 사용한 도면 객체 검출",
            "category": "detection",
            "drawing_type": "general",
            "created_at": "2026-01-01T00:00:00",
        },
        {
            "id": "ocr-extraction",
            "name": "OCR 텍스트 추출",
            "description": "eDOCr2를 사용한 치수 및 텍스트 추출",
            "category": "ocr",
            "drawing_type": "general",
            "created_at": "2026-01-01T00:00:00",
        },
        {
            "id": "full-analysis",
            "name": "전체 분석 파이프라인",
            "description": "YOLO 검출 + OCR 추출 + 공차 분석",
            "category": "analysis",
            "drawing_type": "mechanical",
            "created_at": "2026-01-01T00:00:00",
        },
    ]


def get_builtin_template(template_id: str) -> Optional[Dict[str, Any]]:
    """내장 템플릿 상세 조회"""
    templates = {
        "yolo-detection": {
            "id": "yolo-detection",
            "name": "YOLO 객체 검출",
            "description": "YOLO를 사용한 도면 객체 검출",
            "category": "detection",
            "drawing_type": "general",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "imageInput",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "이미지 입력"},
                },
                {
                    "id": "yolo-1",
                    "type": "yolo",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "label": "YOLO 검출",
                        "params": {
                            "model_type": "engineering",
                            "confidence": 0.5,
                            "visualize": True,
                        },
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "input-1", "target": "yolo-1"},
            ],
        },
        "ocr-extraction": {
            "id": "ocr-extraction",
            "name": "OCR 텍스트 추출",
            "description": "eDOCr2를 사용한 치수 및 텍스트 추출",
            "category": "ocr",
            "drawing_type": "general",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "imageInput",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "이미지 입력"},
                },
                {
                    "id": "edocr2-1",
                    "type": "edocr2",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "label": "eDOCr2 OCR",
                        "params": {
                            "language": "korean",
                            "extract_dimensions": True,
                            "extract_gdt": True,
                        },
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "input-1", "target": "edocr2-1"},
            ],
        },
        "full-analysis": {
            "id": "full-analysis",
            "name": "전체 분석 파이프라인",
            "description": "YOLO 검출 + OCR 추출 + 공차 분석",
            "category": "analysis",
            "drawing_type": "mechanical",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "imageInput",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "이미지 입력"},
                },
                {
                    "id": "yolo-1",
                    "type": "yolo",
                    "position": {"x": 400, "y": 100},
                    "data": {
                        "label": "YOLO 검출",
                        "params": {
                            "model_type": "engineering",
                            "confidence": 0.5,
                        },
                    },
                },
                {
                    "id": "edocr2-1",
                    "type": "edocr2",
                    "position": {"x": 400, "y": 300},
                    "data": {
                        "label": "eDOCr2 OCR",
                        "params": {
                            "language": "korean",
                            "extract_dimensions": True,
                        },
                    },
                },
                {
                    "id": "skinmodel-1",
                    "type": "skinmodel",
                    "position": {"x": 700, "y": 200},
                    "data": {
                        "label": "공차 분석",
                        "params": {
                            "task": "tolerance_analysis",
                        },
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "input-1", "target": "yolo-1"},
                {"id": "e2", "source": "input-1", "target": "edocr2-1"},
                {"id": "e3", "source": "yolo-1", "target": "skinmodel-1"},
                {"id": "e4", "source": "edocr2-1", "target": "skinmodel-1"},
            ],
        },
    }
    return templates.get(template_id)
