"""
Detection Utilities
검출 관련 유틸리티 함수들
"""
import os
import cv2
import torch
import tempfile
import streamlit as st
from ultralytics import YOLO
from typing import List, Dict, Any, Tuple, Optional
from .helpers import safe_mean
from .model_loader import load_yolo_model_cached

def detect_with_model(system, model_id: str, image, confidence_threshold: float = 0.25, nms_threshold: float = 0.45, enable_ocr: bool = False) -> List[Dict[str, Any]]:
    """특정 모델로 검출 수행"""
    try:
        # 모델 정보 가져오기
        model_info = system.model_registry.registry["models"][model_id]
        model_type = model_info.get('type', 'YOLO')

        if model_type == 'YOLO':
            return _detect_with_yolo(system, model_id, image, model_info, confidence_threshold, nms_threshold, enable_ocr)
        elif model_type == 'Detectron2':
            return _detect_with_detectron2(system, model_id, image, model_info, confidence_threshold, nms_threshold, enable_ocr)
    except Exception as e:
        st.error(f"❌ {model_id} 검출 실패: {str(e)}")
        return []

def _detect_with_yolo(system, model_id: str, image, model_info: Dict[str, Any], confidence_threshold: float, nms_threshold: float, enable_ocr: bool) -> List[Dict[str, Any]]:
    """YOLO 모델 검출 - YOLO11-main 접근법 적용 (캐시 최적화)"""
    # 캐시에서 모델 로드 또는 기존 로드된 모델 사용
    cache_key = f"yolo_model_cache_{model_id}"
    if cache_key not in st.session_state:
        model_path = model_info.get('path', 'models/yolo/best.pt')
        st.info(f"🔍 모델 로드 중: {model_id} from {model_path}")

        # 모델 파일 존재 확인
        if not os.path.exists(model_path):
            st.error(f"❌ 모델 파일을 찾을 수 없습니다: {model_path}")
            # 기본 모델로 대체
            model_path = "models/yolo/best.pt"
            st.warning(f"⚠️ 기본 모델 사용: {model_path}")

        # 모델 직접 로드 (캐시 함수 대신)
        try:
            st.info(f"🔄 모델 로딩 시도: {model_path}")
            model = YOLO(model_path)

            # 모델 유효성 확인
            if not hasattr(model, 'predict'):
                st.error(f"❌ 로드된 모델에 predict 메서드가 없습니다")
                return []

            # GPU 사용 가능한 경우 GPU로 이동
            if torch.cuda.is_available():
                model.to('cuda')
                st.info(f"✅ 모델을 GPU로 이동했습니다")
            else:
                st.info(f"ℹ️ CPU 모드로 실행됩니다")

            # 모델 저장 전 최종 검증
            if model is None or not hasattr(model, 'predict'):
                st.error(f"❌ 로드된 모델이 유효하지 않습니다. 타입: {type(model)}")
                return []

            # 안전한 캐시 저장
            st.session_state[cache_key] = model
            st.success(f"✅ 모델 로드 성공: {model_path}")

        except Exception as e:
            st.error(f"❌ 모델 로드 실패 ({model_path}): {e}")
            import traceback
            st.error(f"상세 오류: {traceback.format_exc()}")
            # 실패 시 캐시에 None도 저장하지 않음
            return []

    model = st.session_state[cache_key]

    # 모델 유효성 검증
    if model is None or not hasattr(model, 'predict'):
        st.error(f"❌ {model_id}: 유효하지 않은 모델입니다. 모델을 다시 로드합니다.")
        # 캐시에서 제거하고 다시 로드 시도
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        return []

    # image 파라미터를 사용 (함수 인자로 전달받음)

    # YOLO11-main 접근법 사용 여부 (기본값: True)
    use_yolo11_approach = st.session_state.get('use_yolo11_approach', True)

    if use_yolo11_approach:
        # YOLO11-main 방식: 사용자 설정 적용, 이미지 크기 최적화
        conf_threshold = confidence_threshold
        iou_threshold = nms_threshold

        # 이미지 크기 최적화 (32의 배수로 조정)
        height, width = image.shape[:2]
        max_dim = max(width, height)

        # YOLO stride(32)의 배수로 조정하여 경고 방지
        max_dim = ((max_dim + 31) // 32) * 32

        # 임시 이미지 파일 저장 (파일 경로로 전달하기 위해)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, image)
            temp_image_path = tmp_file.name

        # 디버깅 정보 표시
        st.info(f"📊 {model_id} 검출 시작 (YOLO11-main 최적화)")
        st.write(f"🔧 설정: 신뢰도={conf_threshold:.2f}, IoU={iou_threshold:.2f}, imgsz={max_dim}")
        st.write(f"🖼️ 이미지 크기: {width}x{height}, 최대 차원: {max_dim}")

        results = model.predict(
            source=temp_image_path,  # 파일 경로 사용
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=max_dim,  # 이미지 크기 설정
            device=system.device['device'],
            verbose=False,
            save=False
        )

        # 임시 파일 삭제
        try:
            os.unlink(temp_image_path)
        except:
            pass

    else:
        # 기존 DrawingBOMExtractor 방식 (낮은 confidence)
        conf_threshold = st.session_state.get('model_confidence_threshold', 0.25)
        iou_threshold = st.session_state.get('model_iou_threshold', 0.45)

        # 디버깅 정보 표시
        st.info(f"📊 {model_id} 검출 시작 (기존 방식)")
        st.write(f"🔧 설정: 신뢰도={conf_threshold:.3f}, IoU={iou_threshold:.3f}, 디바이스={system.device['device']}")
        st.write(f"🖼️ 이미지 크기: {image.shape if hasattr(image, 'shape') else 'Unknown'}")

        results = model.predict(
            source=image,
            conf=conf_threshold,
            iou=iou_threshold,
            device=system.device['device'],
            verbose=False
        )

    # 원시 검출 결과 로깅
    st.write(f"🔍 원시 검출 결과 수: {len(results) if results else 0}")
    if results and len(results) > 0:
        result = results[0]
        raw_detections = len(result.boxes) if result.boxes is not None else 0
        st.write(f"📦 검출된 박스 수: {raw_detections}")
        if result.boxes is not None and raw_detections > 0:
            raw_confidences = result.boxes.conf.cpu().numpy()
            st.write(f"📊 검출 신뢰도 범위: {raw_confidences.min():.3f} - {raw_confidences.max():.3f}")
    else:
        st.write("❌ 검출 결과 없음")

    detections = []
    st.write(f"YOLO 검출 결과 - 총 {len(results[0].boxes) if results and len(results) > 0 and results[0].boxes is not None else 0}개 객체 검출")
    if results and len(results) > 0:
        result = results[0]
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes.xyxy.cpu().numpy()
            confidences = result.boxes.conf.cpu().numpy()
            classes = result.boxes.cls.cpu().numpy().astype(int)
            class_names = result.names

            for box, conf, cls in zip(boxes, confidences, classes):
                x1, y1, x2, y2 = box.astype(int)
                detection = {
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float(conf),
                    'class_id': cls,
                    'class_name': class_names[cls],
                    'model': model_id
                }

                # OCR 향상 적용 (옵션)
                OCR_AVAILABLE = st.session_state.get('OCR_AVAILABLE', False)
                if st.session_state.get('use_ocr_enhancement', True) and OCR_AVAILABLE:
                    detection = system.enhance_detection_with_ocr(image, detection)

                detections.append(detection)

    return detections

def _detect_with_detectron2(system, model_id: str, model_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detectron2 모델 검출"""
    try:
        # Detectron2 import 시도
        from detectron2.config import get_cfg
        from detectron2.engine import DefaultPredictor
        from detectron2.data import MetadataCatalog
        from detectron2 import model_zoo

        st.info(f"ℹ️ {model_id}: Detectron2 모델 로딩 중...")

        # Detectron2 모델 경로
        detectron2_path = model_info.get('path', '')

        if not os.path.exists(detectron2_path):
            st.warning(f"⚠️ Detectron2 모델 파일이 없습니다. YOLO로 대체 실행합니다.")
            return _fallback_to_yolo(system, model_id)

        # Detectron2 설정
        if model_id not in system.loaded_models:
            cfg = get_cfg()
            cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
            cfg.MODEL.ROI_HEADS.NUM_CLASSES = 27  # 27개 클래스
            cfg.MODEL.WEIGHTS = detectron2_path
            cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = st.session_state.get('confidence_threshold', 0.25)
            cfg.MODEL.DEVICE = system.device['device']

            predictor = DefaultPredictor(cfg)
            system.loaded_models[model_id] = predictor

        predictor = system.loaded_models[model_id]
        image = st.session_state.current_image['image']

        # Detectron2 예측
        outputs = predictor(image)

        detections = []
        instances = outputs["instances"].to("cpu")
        boxes = instances.pred_boxes.tensor.numpy()
        scores = instances.scores.numpy()
        classes = instances.pred_classes.numpy()

        for box, score, cls in zip(boxes, scores, classes):
            x1, y1, x2, y2 = box.tolist()
            # data.yaml의 클래스 이름 사용 (있으면)
            if system.data_yaml and 'names' in system.data_yaml:
                class_names = system.data_yaml['names']
                class_name = class_names[int(cls)] if int(cls) < len(class_names) else f"Unknown_{cls}"
            else:
                # fallback to registry.json
                class_name = system.model_registry.registry['classes']['class_names'][int(cls)]

            detection = {
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'confidence': float(score),
                'class_id': int(cls),
                'class_name': class_name,
                'model': model_id
            }
            detections.append(detection)

        st.success(f"✅ {model_id}: {len(detections)}개 객체 검출 완료 (Detectron2)")
        return detections

    except ImportError:
        st.warning("⚠️ Detectron2가 설치되지 않았습니다. YOLO로 대체 실행합니다.")
        return _fallback_to_yolo(system, model_id)
    except Exception as e:
        st.error(f"❌ {model_id} 실행 중 오류: {str(e)}")
        return _fallback_to_yolo(system, model_id)

def _fallback_to_yolo(system, model_id: str) -> List[Dict[str, Any]]:
    """Detectron2 실패 시 YOLO로 대체 실행"""
    st.info("ℹ️ YOLO 모델로 대체 실행 중...")
    yolo_path = "models/yolo/best.pt"

    if not os.path.exists(yolo_path):
        yolo_path = "models/yolo/best.pt"  # 통합된 경로

    if not os.path.exists(yolo_path):
        st.error(f"❌ YOLO 모델 파일을 찾을 수 없습니다")
        return []

    try:
        # 캐시에서 YOLO 모델 로드
        fallback_cache_key = f"fallback_model_{model_id}_yolo"
        if fallback_cache_key not in st.session_state:
            model = load_yolo_model_cached(yolo_path)
            if model is not None:
                st.session_state[fallback_cache_key] = model
            else:
                st.error(f"❌ 대체 YOLO 모델 로드 실패: {yolo_path}")
                return []

        model = st.session_state[fallback_cache_key]
        image = st.session_state.current_image['image']
        conf_threshold = st.session_state.get('confidence_threshold', 0.25)
        iou_threshold = st.session_state.get('iou_threshold', 0.45)

        results = model.predict(
            source=image,
            conf=conf_threshold,
            iou=iou_threshold,
            device=system.device['device'],
            verbose=False
        )

        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()
                scores = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy()

                for box, score, cls in zip(boxes, scores, classes):
                    # data.yaml의 클래스 이름 사용 (있으면)
                    if system.data_yaml and 'names' in system.data_yaml:
                        class_names = system.data_yaml['names']
                        class_name = class_names[int(cls)] if int(cls) < len(class_names) else f"Unknown_{cls}"
                    else:
                        # fallback to registry.json
                        class_name = system.model_registry.registry['classes']['class_names'][int(cls)]

                    detection = {
                        'bbox': box.tolist(),
                        'confidence': float(score),
                        'class_id': int(cls),
                        'class_name': class_name,
                        'model': model_id
                    }
                    detections.append(detection)

        st.success(f"✅ {len(detections)}개 객체 검출 완료 (YOLO 대체)")
        return detections

    except Exception as e:
        st.error(f"❌ YOLO 대체 실행 중 오류: {str(e)}")
        return []

def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """두 바운딩 박스의 IoU(Intersection over Union) 계산"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0

def remove_duplicate_detections(detections: List[Dict[str, Any]], iou_threshold: float = 0.5) -> List[Dict[str, Any]]:
    """중복 검출 제거 (IoU 기반)"""
    if not detections:
        return []

    # 신뢰도 순으로 정렬
    sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)

    unique_detections = []
    for detection in sorted_detections:
        is_duplicate = False
        for unique in unique_detections:
            if calculate_iou(detection['bbox'], unique['bbox']) > iou_threshold:
                # 같은 클래스인 경우만 중복으로 처리
                if detection['class_name'] == unique['class_name']:
                    is_duplicate = True
                    break

        if not is_duplicate:
            unique_detections.append(detection)

    return unique_detections

def calculate_detection_metrics(system, predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]], iou_threshold: float = 0.3) -> Dict[str, Any]:
    """예측과 Ground Truth를 비교하여 정확도 메트릭 계산"""
    if not predictions or not ground_truth:
        return {
            'true_positives': 0,
            'false_positives': len(predictions) if predictions else 0,
            'false_negatives': len(ground_truth) if ground_truth else 0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0
        }

    # 이미지 크기 가져오기
    image = st.session_state.current_image.get('image')
    if image is None:
        return {
            'true_positives': 0,
            'false_positives': len(predictions),
            'false_negatives': len(ground_truth),
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0
        }

    img_height, img_width = image.shape[:2]

    true_positives = 0
    false_positives = len(predictions)
    false_negatives = len(ground_truth)
    matched_gt = set()

    # 각 예측에 대해 가장 잘 매칭되는 GT 찾기
    for pred in predictions:
        best_iou = 0
        best_gt_idx = -1

        pred_bbox = pred.get('bbox', [0, 0, 0, 0])
        pred_class_id = pred.get('class_id', -1)

        # 모든 GT와 비교
        for gt_idx, gt in enumerate(ground_truth):
            if gt_idx not in matched_gt:
                # GT bbox를 xyxy로 변환
                gt_bbox = system.yolo_to_xyxy(
                    gt['x_center'], gt['y_center'],
                    gt['width'], gt['height'],
                    img_width, img_height
                )

                # IoU 계산
                iou = calculate_iou(pred_bbox, gt_bbox)

                # 같은 클래스이고 IoU가 더 높으면 업데이트
                if pred_class_id == gt['class_id'] and iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx

        # IoU 임계값을 넘고 매칭되면 TP
        if best_iou >= iou_threshold and best_gt_idx >= 0:
            true_positives += 1
            matched_gt.add(best_gt_idx)
            false_positives -= 1
            false_negatives -= 1

    # 메트릭 계산
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }