"""
Basic UI Components Module
기본 UI 컴포넌트들 (사이드바, 도면 표시, 메인 워크플로우)
"""
import streamlit as st
import os
from typing import List, Dict, Any
from .file_handler import get_test_files, process_uploaded_file, load_test_image

def render_sidebar(system):
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("🔧 스마트 BOM 분석 솔루션")
        st.markdown("---")

        # GPU 상태 표시
        gpu_status = system.get_gpu_status()
        if gpu_status.get("available"):
            st.success(f"🖥️ GPU 사용 중 ({gpu_status['gpu_util']}%)")
            st.progress(gpu_status['memory_percent'] / 100)
            st.caption(f"메모리: {gpu_status['memory_used']}MB / {gpu_status['memory_total']}MB")
        else:
            st.info("💻 CPU 모드로 실행 중")

        st.markdown("---")

        # 시스템 정보
        with st.expander("📊 시스템 정보", expanded=False):
            st.write(f"✅ 모델 레지스트리: {len(system.model_registry.get_available_models())}개 모델")
            st.write(f"✅ 가격 데이터: {len(system.pricing_data) if system.pricing_data else 0}개 부품")
            st.write(f"✅ Ground Truth: {len(system.ground_truth) if system.ground_truth else 0}개")
            st.write(f"✅ 클래스: {len(system.class_names)}개")

        # 캐시 관리
        st.markdown("---")
        st.subheader("🗑️ 캐시 관리")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("모델 캐시 정리"):
                system.clear_model_cache()
                st.success("모델 캐시 정리 완료")
                st.rerun()
        with col2:
            if st.button("전체 캐시 정리"):
                system.clear_all_cache()
                st.success("전체 캐시 정리 완료")
                st.rerun()

def render_main_workflow(system):
    """메인 워크플로우 렌더링"""
    st.title("🔧 스마트 BOM 분석 솔루션 v2.0")

    # 탭 구성
    tabs = st.tabs([
        "📁 도면 업로드",
        "🤖 AI 모델 선택",
        "🔍 AI 검출 결과",
        "✅ 심볼 검증 및 수정",
        "📊 BOM 생성"
    ])

    with tabs[0]:
        render_drawing_display(system)

    with tabs[1]:
        from .ui_model import render_model_selection
        render_model_selection(system)

    with tabs[2]:
        from .ui_detection import render_detection_results
        render_detection_results(system)

    with tabs[3]:
        from .ui_verification import render_symbol_verification
        render_symbol_verification(system)

    with tabs[4]:
        from .ui_bom import render_bom_generation
        render_bom_generation(system)

def render_drawing_display(system):
    """도면 표시 섹션"""
    st.header("📁 도면 파일 선택")

    # 파일 선택 방법
    upload_method = st.radio(
        "파일 선택 방법:",
        ["📤 새 파일 업로드", "📂 테스트 이미지 선택"],
        horizontal=True
    )

    if upload_method == "📤 새 파일 업로드":
        uploaded_file = st.file_uploader(
            "도면 파일을 업로드하세요 (PNG, JPG, PDF)",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="PDF 파일은 자동으로 이미지로 변환됩니다."
        )

        if uploaded_file:
            result = process_uploaded_file(uploaded_file, system)
            if result:
                st.session_state.current_image = result
                st.success(f"✅ {result['type']} 파일이 성공적으로 로드되었습니다!")

                # 이미지 표시
                st.image(
                    result['image'],
                    caption=f"업로드된 파일: {result['filename']}",
                    use_container_width=True
                )

    else:  # 테스트 이미지 선택
        test_files = get_test_files(system)

        if test_files:
            selected_file = st.selectbox(
                "테스트 이미지 선택:",
                ["선택하세요..."] + test_files
            )

            if selected_file != "선택하세요...":
                result = load_test_image(selected_file, system)
                if result:
                    st.session_state.current_image = result
                    st.success(f"✅ 테스트 파일이 성공적으로 로드되었습니다!")

                    # 이미지 표시
                    st.image(
                        result['image'],
                        caption=f"테스트 파일: {result['filename']}",
                        use_container_width=True
                    )
        else:
            st.warning("⚠️ test_drawings 폴더에 테스트 파일이 없습니다.")
            st.info("테스트 파일이 있는 경우 test_drawings 폴더에 넣어주세요.")

    # 현재 로드된 이미지 정보 표시
    if 'current_image' in st.session_state and st.session_state.current_image:
        current = st.session_state.current_image

        st.divider()
        st.subheader("📋 현재 로드된 파일 정보")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("파일명", current['filename'])
        with col2:
            st.metric("파일 타입", current['type'])
        with col3:
            if 'image' in current:
                h, w = current['image'].shape[:2]
                st.metric("이미지 크기", f"{w} × {h}")