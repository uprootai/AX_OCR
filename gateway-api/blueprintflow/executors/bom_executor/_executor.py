"""
Blueprint AI BOM Executor
Human-in-the-Loop 기반 BOM 생성 노드 실행기
"""

import logging
import os
from typing import Dict, Any, Optional

from ..base_executor import BaseNodeExecutor, APICallerMixin
from ..executor_registry import ExecutorRegistry
from ._api_helpers import BOMAPIHelpersMixin
from ._session_ops import BOMSessionOpsMixin
from ._file_ops import BOMFileOpsMixin

logger = logging.getLogger(__name__)


class BOMExecutor(BOMAPIHelpersMixin, BOMSessionOpsMixin, BOMFileOpsMixin, BaseNodeExecutor, APICallerMixin):
    """
    Blueprint AI BOM 실행기

    Human-in-the-Loop 검증이 필요한 경우 UI URL을 반환하고,
    자동 모드에서는 직접 BOM을 생성합니다.

    APICallerMixin을 상속받아 재시도 로직이 포함된 API 호출 사용.
    """

    # Blueprint AI BOM 백엔드 URL
    BASE_URL = "http://blueprint-ai-bom-backend:5020"
    API_BASE_URL = "http://blueprint-ai-bom-backend:5020"  # APICallerMixin용
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # 재시도 설정 (APICallerMixin 오버라이드)
    DEFAULT_TIMEOUT = 60
    DEFAULT_MAX_RETRIES = 3

    # ========================================
    # 메인 실행 메서드
    # ========================================

    async def execute(self, inputs: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        """
        BOM 세션 생성 및 검증 UI 열기

        이 노드는 자체적으로 검출을 수행하지 않습니다.
        반드시 YOLO 노드에서 detections를 받아야 합니다.
        세션 생성 후 검증 UI URL을 반환합니다.

        Args:
            inputs: 입력 데이터 (image, detections - 둘 다 필수)
            context: 실행 컨텍스트

        Returns:
            검증 UI URL, 세션 정보
        """
        try:
            # 0. 다중 부모 노드 입력 처리 (from_ prefix 병합)
            # input_collector.py는 부모가 2개 이상이면 from_<node_id> prefix를 유지함
            # 예: {'from_imageinput_1': {...}, 'from_yolo_1': {...}}
            # 이를 단일 딕셔너리로 병합: {'image': '...', 'detections': [...], ...}
            if any(key.startswith("from_") for key in inputs.keys()):
                merged_inputs = {}
                for key, value in inputs.items():
                    if key.startswith("from_") and isinstance(value, dict):
                        merged_inputs.update(value)
                    elif not key.startswith("from_"):
                        merged_inputs[key] = value
                logger.info(f"다중 부모 입력 병합: {list(inputs.keys())} → {list(merged_inputs.keys())}")
                inputs = merged_inputs

            # 0. 활성화할 기능 가져오기
            # ImageInput features + 노드 파라미터 features를 병합 (중복 제거)
            input_features = inputs.get("features", [])
            param_features = self.parameters.get("features", [])
            if isinstance(input_features, str):
                input_features = [input_features]
            if isinstance(param_features, str):
                param_features = [param_features]
            # 병합: input features + param features (중복 제거, 순서 유지)
            seen = set()
            features = []
            for f in list(input_features) + list(param_features):
                if f and f not in seen:
                    seen.add(f)
                    features.append(f)
            if not features:
                features = ["verification"]
            logger.info(f"활성화된 기능 (inputs: {input_features}, params: {param_features} → merged: {features})")

            # drawing_type: inputs 우선, 없으면 노드 파라미터, 최종 기본값 auto
            drawing_type = inputs.get("drawing_type") or self.parameters.get("drawing_type", "auto")
            logger.info(f"도면 타입: {drawing_type} (source: {'inputs' if inputs.get('drawing_type') else 'parameters'})")

            # 1. 이미지 확인 (필수)
            # 원본 이미지: 수작업 라벨 추가용 (깨끗한 이미지)
            # visualized_image: AI 검출 결과 비교용 (YOLO 결과 시각화)
            original_image = inputs.get("image")
            visualized_image = inputs.get("visualized_image")

            # 원본 이미지가 없으면 다른 소스에서 시도
            if not original_image:
                original_image = (
                    inputs.get("upscaled_image") or
                    inputs.get("segmented_image")
                )

            # 최소한 하나의 이미지는 필요
            if not original_image and not visualized_image:
                available_keys = list(inputs.keys())
                raise ValueError(f"이미지 입력이 필요합니다. 사용 가능한 키: {available_keys}")

            # 원본 이미지가 없으면 visualized_image를 원본으로 사용 (경고)
            if not original_image and visualized_image:
                logger.warning("원본 이미지(image)가 없어 visualized_image를 사용합니다. 수작업 라벨 추가 시 바운딩박스가 보일 수 있습니다.")
                original_image = visualized_image

            image_data = original_image

            # 2. detections 확인 (drawing_type에 따라 선택적)
            external_detections = inputs.get("detections", [])

            # drawing_type별 검출 요구사항
            # - auto: VLM 분류 미사용 시 detections 없이 허용 (수동 라벨링)
            # - dimension: 치수 도면 → detections 불필요 (OCR만 사용)
            # - dimension_bom: 치수+BOM → detections 불필요 (OCR + 수동 라벨링)
            # - electrical_panel, pid, assembly: detections 필수 (YOLO 사용)
            # 모든 타입에서 detections 없이 허용 (수동 라벨링 지원)
            # YOLO 연결 시 자동 가져오기, 없으면 검증 UI에서 수동 추가
            detection_optional_types = ["auto", "dimension", "dimension_bom", "electrical_panel", "pid", "assembly"]

            if drawing_type not in detection_optional_types:
                if not external_detections or len(external_detections) == 0:
                    raise ValueError(
                        f"detections 입력이 필요합니다. '{drawing_type}' 타입은 YOLO 노드가 필요합니다."
                    )
            else:
                if not external_detections:
                    logger.info(f"'{drawing_type}' 타입: detections 없이 세션 생성 (OCR 전용 모드)")

            # 3. 세션 생성 (이미지 크기 자동 추출 및 업데이트, 도면 타입, features 전달)
            # project_id, metadata는 inputs에서 가져옴 (BOM 계층 워크플로우)
            project_id = inputs.get("project_id") or self.parameters.get("project_id")
            metadata = inputs.get("metadata") or self.parameters.get("metadata")
            session_id, image_width, image_height = await self._create_session(
                image_data, drawing_type, features,
                project_id=project_id, metadata=metadata
            )
            logger.info(f"세션 생성됨: {session_id} (이미지 크기: {image_width}x{image_height}, features: {features}, project: {project_id})")

            # 4. YOLO 노드의 검출 결과 가져오기 (있는 경우만)
            if external_detections and len(external_detections) > 0:
                logger.info(f"YOLO detections 가져오기: {len(external_detections)}개")
                await self._import_detections_v2(session_id, external_detections)
            else:
                logger.info("detections 없음 - OCR 전용 모드로 세션 생성됨")

            # 5. GT 파일 업로드 (Builder에서 첨부된 경우)
            gt_file = inputs.get("gt_file")
            if gt_file:
                await self._upload_gt_file(session_id, gt_file, image_width, image_height)

            # 6. 단가 파일 업로드 (Builder에서 첨부된 경우)
            pricing_file = inputs.get("pricing_file")
            if pricing_file:
                await self._upload_pricing_file(session_id, pricing_file)

            # 7. eDOCr2 치수 결과 가져오기 (있는 경우)
            dimensions = inputs.get("dimensions", [])
            if dimensions and len(dimensions) > 0:
                logger.info(f"eDOCr2 dimensions 가져오기: {len(dimensions)}개")
                await self._import_dimensions(session_id, dimensions)
            else:
                logger.info("dimensions 없음 - 검증 UI에서 직접 치수 인식 필요")

            # 8. BOM 백엔드 자체 분석 실행 (PaddleOCR 타일 기반 치수 추출)
            success, result, error = await self._post_api(
                f"/analysis/run/{session_id}",
                timeout=120
            )
            if success and result:
                paddle_dims = result.get("dimensions_count", 0)
                internal_tables = result.get("tables_count", 0)
                logger.info(f"BOM 분석 완료: PaddleOCR dims={paddle_dims}, tables={internal_tables}")
            elif error:
                logger.warning(f"BOM 분석 실행 중 오류 (무시): {error}")

            # 9. Gateway Table Detector 결과 덮어쓰기 (내부 테이블보다 품질 높음)
            tables = inputs.get("tables", [])
            regions = inputs.get("regions", [])
            if tables and len(tables) > 0:
                await self._import_tables(session_id, tables, regions)
            else:
                logger.info("Table Detector 결과 없음 - 내부 테이블 유지")

            # 10. 검증 UI URL 반환 (항상 Human-in-the-Loop)
            # WorkflowPage 사용 - GT 비교, Precision, Recall, F1 Score 표시
            # features 파라미터를 URL에 포함
            features_param = ",".join(features) if features else "verification"
            verification_url = f"{self.FRONTEND_URL}/workflow?session={session_id}&features={features_param}"
            detection_count = len(external_detections) if external_detections else 0
            dimension_count = len(dimensions) if dimensions else 0

            # drawing_type에 따른 메시지
            if dimension_count > 0:
                message = f"eDOCr2에서 {dimension_count}개 치수 가져옴. 검증 UI에서 확인하세요."
            elif drawing_type in detection_optional_types and detection_count == 0:
                message = "OCR 전용 모드: 검증 UI에서 수동으로 부품을 추가하고 BOM을 생성하세요."
            else:
                message = "검증 UI에서 검출 결과를 확인하고 BOM을 생성하세요."

            return {
                "status": "pending_verification",
                "session_id": session_id,
                "verification_url": verification_url,
                "detection_count": detection_count,
                "dimension_count": dimension_count,
                "image_width": image_width,
                "image_height": image_height,
                "features": features,
                "drawing_type": drawing_type,
                "message": message,
                "interactive": True,
                "ui_action": {
                    "type": "open_url",
                    "url": verification_url,
                    "label": "검증 UI 열기"
                }
            }

        except Exception as e:
            logger.error(f"BOM 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사 - 파라미터 없음"""
        return True, None


# 실행기 등록
ExecutorRegistry.register("blueprint-ai-bom", BOMExecutor)
