"""
Model Selection UI Components Module
모델 선택 관련 UI 컴포넌트들
"""
import streamlit as st
from typing import List, Dict, Any
from .detection import detect_with_model

def render_model_selection(system):
    """AI 모델 선택 및 검출 실행"""
    st.header("🤖 AI 모델 선택 및 검출")

    if 'current_image' not in st.session_state or not st.session_state.current_image:
        st.warning("⚠️ 먼저 도면 파일을 업로드하세요.")
        return

    # 사용 가능한 모델 표시
    st.subheader("📋 사용 가능한 AI 모델")

    available_models = system.model_registry.get_available_models()
    if not available_models:
        st.error("사용 가능한 모델이 없습니다.")
        return

    # 현재 선택된 모델들 (기본값: YOLOv11X만 선택)
    if 'selected_models' not in st.session_state:
        st.session_state.selected_models = ['yolov11x']

    # 모델 선택 UI
    st.write("**검출에 사용할 모델을 선택하세요:**")

    for model_id in available_models:
        model_info = system.model_registry.registry["models"][model_id]
        is_selected = model_id in st.session_state.selected_models

        col1, col2 = st.columns([1, 4])

        with col1:
            if st.checkbox("", value=is_selected, key=f"model_{model_id}"):
                if model_id not in st.session_state.selected_models:
                    st.session_state.selected_models.append(model_id)
            else:
                if model_id in st.session_state.selected_models:
                    st.session_state.selected_models.remove(model_id)

        with col2:
            # 모델 정보 표시
            emoji = model_info.get('emoji', '🤖')
            name = model_info.get('name', 'Unknown Model')
            description = model_info.get('description', 'No description')
            accuracy = model_info.get('accuracy')

            st.markdown(f"**{emoji} {name}**")
            st.write(f"설명: {description}")
            if accuracy is not None:
                st.write(f"정확도: {accuracy:.1%}")
            else:
                st.write("정확도: 정보 없음")

        st.divider()

    # 검출 설정
    st.subheader("⚙️ 검출 설정")

    col1, col2, col3 = st.columns(3)

    with col1:
        confidence_threshold = st.slider(
            "신뢰도 임계값",
            min_value=0.1,
            max_value=0.9,
            value=0.25,
            step=0.05,
            help="이 값보다 높은 신뢰도를 가진 검출만 표시합니다."
        )

    with col2:
        nms_threshold = st.slider(
            "NMS 임계값",
            min_value=0.1,
            max_value=0.9,
            value=0.45,
            step=0.05,
            help="Non-Maximum Suppression을 위한 IoU 임계값입니다."
        )

    with col3:
        enable_ocr = st.checkbox(
            "🔍 Enhanced OCR 텍스트 인식 향상",
            value=False,
            help="OCR을 통한 텍스트 인식으로 검출 정확도를 향상시킵니다."
        )

    # 검출 실행 버튼
    st.subheader("🚀 AI 검출 실행")

    if not st.session_state.selected_models:
        st.warning("⚠️ 최소 하나의 모델을 선택하세요.")
        return

    selected_model_names = []
    for model_id in st.session_state.selected_models:
        model_info = system.model_registry.registry["models"][model_id]
        selected_model_names.append(model_info.get('name', model_id))

    st.write(f"**선택된 모델:** {', '.join(selected_model_names)}")
    st.write(f"**검출 설정:** 신뢰도 {confidence_threshold}, NMS {nms_threshold}")

    if enable_ocr:
        st.write("**Enhanced OCR:** ✅ 활성화")
    else:
        st.write("**Enhanced OCR:** ❌ 비활성화")

    # 검출 실행
    if st.button("🔍 AI 검출 실행"):
        # 검출 진행률 표시
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 결과 저장할 딕셔너리 초기화
        if 'detection_results' not in st.session_state:
            st.session_state.detection_results = {}

        total_models = len(st.session_state.selected_models)

        for i, model_id in enumerate(st.session_state.selected_models):
            model_info = system.model_registry.registry["models"][model_id]
            model_name = model_info.get('name', model_id)

            # 진행률 업데이트
            progress = i / total_models
            progress_bar.progress(progress)
            status_text.text(f"🔍 {model_name} 모델로 검출 중... ({i+1}/{total_models})")

            try:
                # 모델로 검출 수행
                detections = detect_with_model(
                    system,
                    model_id,
                    st.session_state.current_image['image'],
                    confidence_threshold=confidence_threshold,
                    nms_threshold=nms_threshold,
                    enable_ocr=enable_ocr
                )

                # 결과 저장
                st.session_state.detection_results[model_id] = detections

                st.success(f"✅ {model_name}: {len(detections)}개 검출 완료")

            except Exception as e:
                st.error(f"❌ {model_name} 검출 실패: {str(e)}")
                # 실패한 모델은 빈 리스트로 저장
                st.session_state.detection_results[model_id] = []

        # 완료
        progress_bar.progress(1.0)
        status_text.success("✅ 모든 모델 검출 완료!")

        # 전체 결과 요약
        total_detections = sum(len(detections) for detections in st.session_state.detection_results.values())
        st.balloons()
        st.success(f"🎉 총 {total_detections}개의 객체가 검출되었습니다!")

        # 다음 탭으로 이동 안내
        st.info("💡 'AI 검출 결과' 탭에서 검출 결과를 확인하세요.")

    # 기존 검출 결과가 있으면 요약 표시
    if 'detection_results' in st.session_state and st.session_state.detection_results:
        st.divider()
        st.subheader("📊 이전 검출 결과 요약")

        for model_id, detections in st.session_state.detection_results.items():
            model_info = system.model_registry.registry["models"][model_id]
            model_name = model_info.get('name', model_id)
            emoji = model_info.get('emoji', '🤖')

            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{emoji} **{model_name}**")
            with col2:
                st.metric("검출 수", len(detections))

        if st.button("🗑️ 검출 결과 초기화", key="clear_results"):
            st.session_state.detection_results = {}
            st.success("검출 결과가 초기화되었습니다.")
            st.rerun()