"""
Detection Results UI Components Module
검출 결과 관련 UI 컴포넌트들
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from .helpers import safe_mean
from .detection import calculate_detection_metrics
from .visualization import draw_detections_only, draw_ground_truth_only
from .file_handler import load_ground_truth_for_current_image

def render_detection_results(system):
    """검출 결과 표시"""
    st.header("🔍 AI 검출 결과")

    if not st.session_state.detection_results:
        st.info("검출 결과가 없습니다. 먼저 'AI 모델 선택 및 검출' 탭에서 AI 검출을 실행하세요.")
        return

    # Ground Truth 라벨 로드 (있는 경우)
    ground_truth = system.load_ground_truth_for_current_image()

    # 각 모델별 결과 표시
    for model_id, detections in st.session_state.detection_results.items():
        # manual 모델은 model_registry에 없으므로 별도 처리
        if model_id == 'manual':
            model_info = {
                'name': '수작업 라벨링',
                'emoji': '✏️',
                'type': 'MANUAL',
                'description': '사용자가 수동으로 추가한 검출'
            }
        else:
            model_info = system.model_registry.registry["models"][model_id]

        # F1 스코어 계산 (Ground Truth가 있는 경우)
        f1_score = None
        metrics = None
        if ground_truth:
            metrics = system.calculate_detection_metrics(detections, ground_truth)
            f1_score = metrics['f1_score']

        # 확장 패널 제목에 F1 스코어, 정밀도, 재현율 포함
        expander_title = f"📊 {model_info['name']} - {len(detections)}개 검출"
        if f1_score is not None:
            expander_title += f" (F1: {f1_score:.1%}, 정밀도: {metrics['precision']:.1%}, 재현율: {metrics['recall']:.1%})"

        with st.expander(expander_title, expanded=True):
            if detections or ground_truth:
                # 디버깅: Ground Truth 상태 표시
                if ground_truth:
                    st.info(f"✅ Ground Truth 로드됨: {len(ground_truth)}개 라벨")
                else:
                    st.warning("⚠️ Ground Truth 없음")

                # Ground Truth가 있으면 분리 표시, 없으면 기존 방식
                if ground_truth:
                    # Ground Truth와 예측을 분리하여 표시
                    col_gt, col_det = st.columns(2)

                    with col_gt:
                        # Ground Truth만 표시 (초록색, 두꺼운 선)
                        gt_image = system.draw_ground_truth_only(
                            st.session_state.current_image['image'].copy(),
                            ground_truth
                        )
                        gt_width = gt_image.shape[1]
                        gt_display_width = int(gt_width * 0.25)
                        st.image(gt_image, caption=f"🟢 Ground Truth ({len(ground_truth)}개)", width=gt_display_width)

                    with col_det:
                        # 검출 결과만 표시 (빨간색, 두꺼운 선)
                        det_image = system.draw_detections_only(
                            st.session_state.current_image['image'].copy(),
                            detections
                        )
                        det_width = det_image.shape[1]
                        det_display_width = int(det_width * 0.25)
                        st.image(det_image, caption=f"🔴 {model_info['name']} 검출 ({len(detections)}개)", width=det_display_width)
                else:
                    # 기존 방식: 다양한 색상으로 표시
                    result_image = system.draw_detection_results(
                        st.session_state.current_image['image'].copy(),
                        detections
                    )
                    caption = f"{model_info['name']} 검출 결과"

                    # 검출 결과 이미지도 1/4 크기로 표시
                    result_width = result_image.shape[1]
                    display_width = int(result_width * 0.25)
                    st.image(result_image, caption=caption, width=display_width)

                # 검출 통계 및 정확도 메트릭
                if f1_score is not None:
                    # Ground Truth가 있을 때: 4개 컬럼
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("총 검출 수", len(detections))
                    with col2:
                        avg_conf = safe_mean([d['confidence'] for d in detections])
                        st.metric("평균 신뢰도", f"{avg_conf:.3f}")
                    with col3:
                        st.metric("Precision", f"{metrics['precision']:.1%}")
                    with col4:
                        st.metric("Recall", f"{metrics['recall']:.1%}")

                    # F1 스코어를 강조 표시
                    st.success(f"🎯 F1 Score: {f1_score:.1%} (TP:{metrics['true_positives']}, FP:{metrics['false_positives']}, FN:{metrics['false_negatives']})")
                else:
                    # Ground Truth가 없을 때: 기존처럼 3개 컬럼
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 검출 수", len(detections))
                    with col2:
                        avg_conf = safe_mean([d['confidence'] for d in detections])
                        st.metric("평균 신뢰도", f"{avg_conf:.3f}")
                    with col3:
                        unique_classes = len(set(d['class_name'] for d in detections))
                        st.metric("검출 클래스 수", unique_classes)
            else:
                st.info("검출된 객체가 없습니다.")