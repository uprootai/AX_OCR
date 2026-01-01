"""
GT Comparison Executor
Ground Truth와 검출 결과 비교 - 정밀도, 재현율, F1 스코어 계산
"""
from typing import Dict, Any
import json
from pathlib import Path

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
import httpx


class GTComparisonExecutor(BaseNodeExecutor):
    """GT Comparison 실행기 - 검출 성능 평가"""

    API_BASE_URL = "http://blueprint-ai-bom-backend:5020"

    def validate_parameters(self) -> tuple[bool, str | None]:
        """파라미터 유효성 검사"""
        iou_threshold = self.parameters.get("iou_threshold", 0.5)
        if not 0 < iou_threshold <= 1:
            return False, "iou_threshold는 0과 1 사이여야 합니다."
        return True, None

    def get_input_schema(self) -> dict:
        """입력 스키마 정의"""
        return {
            "type": "object",
            "properties": {
                "detections": {"type": "array", "description": "YOLO 검출 결과"},
                "image": {"type": "object", "description": "이미지 정보"},
            },
        }

    def get_output_schema(self) -> dict:
        """출력 스키마 정의"""
        return {
            "type": "object",
            "properties": {
                "metrics": {"type": "object"},
                "tp_matches": {"type": "array"},
                "fp_detections": {"type": "array"},
                "fn_labels": {"type": "array"},
            },
        }

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        GT 비교 실행

        Inputs (이전 노드 출력에서 받음):
            - detections: YOLO 검출 결과 [{class_name, bbox: {x1,y1,x2,y2}, confidence}]
            - image: 원본 이미지 정보 (파일명 필요)

        Parameters:
            - gt_file: GT 파일 경로 (YOLO TXT 형식)
            - iou_threshold: IoU 매칭 임계값 (기본 0.5)
            - class_agnostic: 클래스 무시 모드 (기본 false)
            - model_type: 모델 타입 (bom_detector, engineering, pid_class_aware 등)

        Returns:
            - metrics: 평가 지표 (precision, recall, f1_score, tp, fp, fn)
            - tp_matches: True Positive 매칭 목록
            - fp_detections: False Positive 목록
            - fn_labels: False Negative GT 목록
        """
        # 입력 데이터 추출
        detections = []
        filename = ""
        img_width = 1000
        img_height = 1000

        # 직접 입력 확인
        if "detections" in inputs:
            detections = inputs.get("detections", [])
        if "image" in inputs:
            image_info = inputs.get("image", {})
            if isinstance(image_info, dict):
                filename = image_info.get("filename", "")
                img_width = image_info.get("width", 1000)
                img_height = image_info.get("height", 1000)
            elif isinstance(image_info, str):
                filename = image_info

        # from_ prefix 입력 확인 (다중 부모 - Merge 패턴)
        for key, value in inputs.items():
            if key.startswith("from_") and isinstance(value, dict):
                if "detections" in value and not detections:
                    detections = value.get("detections", [])
                if "image" in value and not filename:
                    image_info = value.get("image", {})
                    if isinstance(image_info, dict):
                        filename = image_info.get("filename", "")
                        img_width = image_info.get("width", img_width)
                        img_height = image_info.get("height", img_height)
                # YOLO 결과에서 이미지 정보 추출
                if "image_info" in value and not filename:
                    image_info = value.get("image_info", {})
                    filename = image_info.get("filename", "")
                    img_width = image_info.get("width", img_width)
                    img_height = image_info.get("height", img_height)

        # 파일명이 없으면 context에서 찾기
        if not filename:
            filename = context.get("filename", "")
            if not filename:
                filename = context.get("image_filename", "unknown.png")

        # 파라미터 추출
        gt_file = self.parameters.get("gt_file", "")
        iou_threshold = float(self.parameters.get("iou_threshold", 0.5))
        class_agnostic = self.parameters.get("class_agnostic", False)
        model_type = self.parameters.get("model_type", "bom_detector")

        # 검출 결과가 없는 경우
        if not detections:
            return {
                "metrics": {
                    "tp": 0,
                    "fp": 0,
                    "fn": 0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "iou_threshold": iou_threshold
                },
                "gt_count": 0,
                "detection_count": 0,
                "tp_matches": [],
                "fp_detections": [],
                "fn_labels": [],
                "has_ground_truth": False,
                "note": "검출 결과가 없습니다. YOLO 노드를 먼저 연결하세요."
            }

        # detections 형식 변환 (YOLO 출력 → GT Compare 입력)
        formatted_detections = []
        for det in detections:
            formatted_det = {
                "class_name": det.get("class_name", det.get("label", "")),
                "confidence": det.get("confidence", 0.0),
                "bbox": det.get("bbox", det.get("box", {}))
            }
            # bbox 형식 확인 및 변환
            bbox = formatted_det["bbox"]
            if isinstance(bbox, dict):
                # x, y, width, height → x1, y1, x2, y2 변환
                if "width" in bbox and "x" in bbox:
                    formatted_det["bbox"] = {
                        "x1": bbox.get("x", 0),
                        "y1": bbox.get("y", 0),
                        "x2": bbox.get("x", 0) + bbox.get("width", 0),
                        "y2": bbox.get("y", 0) + bbox.get("height", 0)
                    }
            formatted_detections.append(formatted_det)

        # API 호출
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.API_BASE_URL}/api/ground-truth/compare",
                    params={
                        "filename": filename,
                        "img_width": img_width,
                        "img_height": img_height,
                        "iou_threshold": iou_threshold,
                        "model_type": model_type,
                        "class_agnostic": str(class_agnostic).lower()
                    },
                    json=formatted_detections
                )

                if response.status_code != 200:
                    error_text = response.text
                    # GT 파일이 없는 경우
                    if "GT 라벨 파일" in error_text or "ground-truth" in error_text.lower():
                        return {
                            "metrics": {
                                "tp": 0,
                                "fp": len(formatted_detections),
                                "fn": 0,
                                "precision": 0.0,
                                "recall": 0.0,
                                "f1_score": 0.0,
                                "iou_threshold": iou_threshold
                            },
                            "gt_count": 0,
                            "detection_count": len(formatted_detections),
                            "tp_matches": [],
                            "fp_detections": formatted_detections,
                            "fn_labels": [],
                            "has_ground_truth": False,
                            "note": f"GT 파일을 찾을 수 없습니다: {filename}. GT 라벨 디렉토리에 해당 파일이 있는지 확인하세요."
                        }
                    raise Exception(f"GT Comparison API 에러: {response.status_code} - {error_text}")

                result = response.json()

        except httpx.ConnectError:
            # Blueprint AI BOM 백엔드 연결 실패
            return {
                "metrics": {
                    "tp": 0,
                    "fp": 0,
                    "fn": 0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "iou_threshold": iou_threshold
                },
                "gt_count": 0,
                "detection_count": len(formatted_detections),
                "tp_matches": [],
                "fp_detections": [],
                "fn_labels": [],
                "has_ground_truth": False,
                "error": "Blueprint AI BOM 백엔드에 연결할 수 없습니다. 컨테이너가 실행 중인지 확인하세요."
            }

        # GT가 없는 경우
        if not result.get("has_ground_truth", False):
            return {
                "metrics": {
                    "tp": 0,
                    "fp": len(formatted_detections),
                    "fn": 0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "iou_threshold": iou_threshold
                },
                "gt_count": 0,
                "detection_count": len(formatted_detections),
                "tp_matches": [],
                "fp_detections": formatted_detections,
                "fn_labels": [],
                "has_ground_truth": False,
                "note": result.get("error", "GT 파일을 찾을 수 없습니다.")
            }

        # 결과 반환
        return {
            "metrics": result.get("metrics", {}),
            "gt_count": result.get("gt_count", 0),
            "detection_count": result.get("detection_count", len(formatted_detections)),
            "tp_matches": result.get("tp_matches", []),
            "fp_detections": result.get("fp_detections", []),
            "fn_labels": result.get("fn_labels", []),
            "has_ground_truth": True,
            "filename": filename
        }


# 레지스트리에 등록
ExecutorRegistry.register("gtcomparison", GTComparisonExecutor)
