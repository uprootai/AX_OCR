"""
Symbol Verification UI Components Module
심볼 검증 관련 UI 컴포넌트들
"""
import streamlit as st
import os
import glob
import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any
from .helpers import safe_mean

def render_symbol_verification(system):
    """심볼 검증 섹션"""
    st.header("✅ 심볼 검증 및 수정")

    # 승인/거부 상태 초기화
    if 'verification_status' not in st.session_state:
        st.session_state.verification_status = {}

    # 편집 상태 초기화
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = {}

    # 수정된 클래스 이름 저장
    if 'modified_classes' not in st.session_state:
        st.session_state.modified_classes = {}

    # 검출 결과가 없으면 리턴
    if not st.session_state.detection_results:
        st.info("검출된 심볼이 없습니다.")
        return

    # 메인 컨텐츠와 사이드 패널로 레이아웃 분리
    main_col, side_panel = st.columns([4, 1])  # 80% 메인, 20% 사이드

    with side_panel:
        # 심볼 참조 리스트 표시
        system.render_symbol_reference_panel()

    with main_col:
        # 탭으로 모델별 결과와 통합 결과 구분
        # 탭 리스트 생성 - 고정 탭 3개 + 모델별 탭
        fixed_tabs = ["📊 통합 결과 (중복 제거)", "🗳️ Voting 기반 통합", "🔍 OCR 키워드 분석"]
        model_tabs = []
        for model_id in st.session_state.detection_results.keys():
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
            model_tabs.append(f"🤖 {model_info['name']}")

        all_tabs = fixed_tabs + model_tabs
        tabs = st.tabs(all_tabs)

        # 통합 결과 탭
        with tabs[0]:
            # 모든 검출 결과를 하나의 리스트로 합치기
            all_detections = []
            for model_id, detections in st.session_state.detection_results.items():
                for detection in detections:
                    detection_with_model = detection.copy()
                    detection_with_model['model_id'] = model_id
                    all_detections.append(detection_with_model)

            if not all_detections:
                st.info("검출된 심볼이 없습니다.")
            else:
                # 중복 제거
                unique_detections = system.remove_duplicate_detections(all_detections)

                # 통계 표시
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("전체 검출", len(all_detections))
                with col2:
                    st.metric("중복 제거 후", len(unique_detections))
                with col3:
                    if len(all_detections) > 0:
                        st.metric("중복률", f"{((len(all_detections)-len(unique_detections))/len(all_detections)*100):.1f}%")

                st.write(f"중복 제거 후 {len(unique_detections)}개의 고유한 심볼이 검출되었습니다:")

                # 일괄 처리 버튼
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔘 모두 승인", key="approve_all_unified"):
                        for i, detection in enumerate(unique_detections):
                            st.session_state.verification_status[f"unified_{i}"] = "approved"
                        st.success("모든 검출이 승인되었습니다.")
                        st.rerun()
                with col2:
                    if st.button("❌ 모두 거부", key="reject_all_unified"):
                        for i, detection in enumerate(unique_detections):
                            st.session_state.verification_status[f"unified_{i}"] = "rejected"
                        st.warning("모든 검출이 거부되었습니다.")
                        st.rerun()
                with col3:
                    if st.button("🔄 상태 초기화", key="reset_status_unified"):
                        # 통합 결과 상태만 초기화
                        keys_to_remove = [k for k in st.session_state.verification_status.keys() if k.startswith("unified_")]
                        for k in keys_to_remove:
                            del st.session_state.verification_status[k]
                        st.info("상태가 초기화되었습니다.")
                        st.rerun()

                # 검출 결과 표시
                render_detection_list(system, unique_detections, "unified")

                # 최종 통합 이미지 표시
                st.divider()
                st.subheader("🖼️ 최종 검증 결과 이미지")

                # 최종 이미지 생성 (승인/거부/수정/수작업 모두 포함)
                final_image = system.create_final_verified_image(
                    st.session_state.current_image['image'].copy(),
                    unique_detections,
                    "unified"
                )
                if final_image is not None:
                    st.image(final_image, caption="최종 검증 결과 (✅승인 ❌거부 ✏️수정 🎨수작업)")
                else:
                    st.info("검출된 결과가 없습니다.")

                # 수작업 라벨링 섹션 추가
                st.divider()
                render_manual_labeling(system, "unified")

        # Voting 기반 통합 탭
        with tabs[1]:
            st.subheader("🗳️ Voting & Weighted Ensemble")

            # Voting 설정
            col1, col2 = st.columns(2)
            with col1:
                min_votes = st.slider("최소 투표 수", min_value=1, max_value=4, value=2,
                                     help="검출을 유효하게 만들기 위한 최소 모델 수")
            with col2:
                st.info(f"현재 {len(st.session_state.detection_results)}개 모델에서 검출 중")

            # 모델 가중치 설정 섹션
            with st.expander("⚙️ 모델 가중치 설정", expanded=False):
                st.write("각 모델의 가중치를 설정하여 Weighted Ensemble의 성능을 조정할 수 있습니다.")

                # 가중치 오버라이드를 위한 세션 상태
                if 'model_weights_override' not in st.session_state:
                    st.session_state.model_weights_override = system.model_weights.copy()

                # 각 모델에 대한 가중치 슬라이더
                for model_id in st.session_state.detection_results.keys():
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
                    current_weight = st.session_state.model_weights_override.get(model_id, 1.0)

                    new_weight = st.slider(
                        f"{model_info['name']} 가중치",
                        min_value=0.1,
                        max_value=2.0,
                        value=current_weight,
                        step=0.1,
                        key=f"weight_{model_id}",
                        help=f"{model_info['description']}"
                    )
                    st.session_state.model_weights_override[model_id] = new_weight

                # 가중치 초기화 버튼
                if st.button("🔄 기본값으로 초기화", key="reset_weights"):
                    st.session_state.model_weights_override = system.model_weights.copy()
                    st.rerun()

                # 현재 가중치 표시
                st.write("현재 설정된 가중치:")
                for model_id, weight in st.session_state.model_weights_override.items():
                    if model_id in st.session_state.detection_results:
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
                        st.write(f"  - {model_info['name']}: **{weight:.1f}**")

            # 모든 검출 결과를 하나의 리스트로 합치기
            all_detections_voting = []
            for model_id, detections in st.session_state.detection_results.items():
                for detection in detections:
                    detection_with_model = detection.copy()
                    detection_with_model['model_id'] = model_id
                    all_detections_voting.append(detection_with_model)

            if not all_detections_voting:
                st.info("검출된 심볼이 없습니다.")
            else:
                # 세션 상태의 가중치를 임시로 사용
                original_weights = system.model_weights.copy()
                if 'model_weights_override' in st.session_state:
                    system.model_weights = st.session_state.model_weights_override.copy()

                # Voting 기반 중복 제거
                unique_detections_voting, voting_info = system.remove_duplicate_detections_with_voting(
                    all_detections_voting, min_votes=min_votes)

                # 원래 가중치로 복원
                system.model_weights = original_weights

                # 통계 표시
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("전체 검출", len(all_detections_voting))
                with col2:
                    st.metric("Voting 후", len(unique_detections_voting))
                with col3:
                    st.metric("최소 투표 수", min_votes)
                with col4:
                    if len(all_detections_voting) > 0:
                        st.metric("제거율", f"{((len(all_detections_voting)-len(unique_detections_voting))/len(all_detections_voting)*100):.1f}%")

                st.write(f"Voting 결과 {len(unique_detections_voting)}개의 검증된 심볼이 검출되었습니다:")

                # Voting 상세 정보 표시
                if voting_info:
                    with st.expander("📊 Voting 상세 정보", expanded=False):
                        for info in voting_info:
                            st.write(f"**{info['class_name']}** - 투표 수: {info['vote_count']}, 가중치 합: {info['weighted_score']:.2f}")
                            st.write(f"  참여 모델: {', '.join(info['models'])}")
                            st.write(f"  평균 신뢰도: {info['avg_confidence']:.3f}")
                            st.divider()

                # 일괄 처리 버튼
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔘 모두 승인", key="approve_all_voting"):
                        for i, detection in enumerate(unique_detections_voting):
                            st.session_state.verification_status[f"voting_{i}"] = "approved"
                        st.success("모든 검출이 승인되었습니다.")
                        st.rerun()
                with col2:
                    if st.button("❌ 모두 거부", key="reject_all_voting"):
                        for i, detection in enumerate(unique_detections_voting):
                            st.session_state.verification_status[f"voting_{i}"] = "rejected"
                        st.warning("모든 검출이 거부되었습니다.")
                        st.rerun()
                with col3:
                    if st.button("🔄 상태 초기화", key="reset_status_voting"):
                        # Voting 결과 상태만 초기화
                        keys_to_remove = [k for k in st.session_state.verification_status.keys() if k.startswith("voting_")]
                        for k in keys_to_remove:
                            del st.session_state.verification_status[k]
                        st.info("상태가 초기화되었습니다.")
                        st.rerun()

                # 검출 결과 표시
                render_detection_list_with_voting(system, unique_detections_voting, "voting")

                # 최종 Voting 이미지 표시
                st.divider()
                st.subheader("🖼️ Voting 기반 검증 결과 이미지")

                # 최종 이미지 생성
                final_image_voting = system.create_final_verified_image(
                    st.session_state.current_image['image'].copy(),
                    unique_detections_voting,
                    "voting"
                )
                if final_image_voting is not None:
                    st.image(final_image_voting, caption="Voting 기반 검증 결과 (✅승인 ❌거부 ✏️수정)")
                else:
                    st.info("검출된 결과가 없습니다.")

        # OCR 키워드 분석 탭
        with tabs[2]:
            st.subheader("🔍 OCR 키워드 분석")
            st.info("OCR 기반 텍스트 인식으로 검출 결과의 정확도를 향상시킵니다.")

            # OCR 분석 결과가 있는지 확인
            if hasattr(st.session_state, 'ocr_analysis_results') and st.session_state.ocr_analysis_results:
                st.write(f"📊 OCR 분석 결과: {len(st.session_state.ocr_analysis_results)}개")

                for i, ocr_result in enumerate(st.session_state.ocr_analysis_results):
                    with st.expander(f"OCR 결과 {i+1}: {ocr_result.get('suggested_class', 'Unknown')}", expanded=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**OCR 텍스트:**")
                            st.code(ocr_result.get('ocr_text', ''))
                            st.write("**제안 클래스:**")
                            st.success(ocr_result.get('suggested_class', 'Unknown'))
                            st.write("**매칭 키워드:**")
                            st.write(ocr_result.get('matching_keywords', []))

                        with col2:
                            if 'cropped_image' in ocr_result:
                                st.write("**검출 영역:**")
                                st.image(ocr_result['cropped_image'], width=200)

                        # OCR 기반 수정 버튼
                        if st.button(f"OCR 제안 적용", key=f"apply_ocr_{i}"):
                            # 해당 검출에 OCR 제안 클래스 적용
                            detection_key = ocr_result.get('detection_key')
                            suggested_class = ocr_result.get('suggested_class')
                            if detection_key and suggested_class:
                                st.session_state.modified_classes[detection_key] = suggested_class
                                st.success(f"클래스가 '{suggested_class}'로 수정되었습니다.")
                                st.rerun()
            else:
                st.info("OCR 분석 결과가 없습니다. AI 모델 선택 탭에서 'Enhanced OCR'을 활성화하고 검출을 실행하세요.")

        # 모델별 탭들
        for tab_idx, model_id in enumerate(st.session_state.detection_results.keys()):
            with tabs[3 + tab_idx]:  # 고정 탭 3개 이후
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

                emoji = model_info.get('emoji', '🤖')
                st.subheader(f"{emoji} {model_info['name']}")

                detections = st.session_state.detection_results[model_id]

                if not detections:
                    st.info("검출된 심볼이 없습니다.")
                    continue

                # 모델별 통계
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("검출 수", len(detections))
                with col2:
                    avg_conf = safe_mean([d['confidence'] for d in detections])
                    st.metric("평균 신뢰도", f"{avg_conf:.3f}")
                with col3:
                    unique_classes = len(set(d['class_name'] for d in detections))
                    st.metric("클래스 수", unique_classes)

                # 일괄 처리 버튼
                # 안전한 키 생성 (특수문자 제거)
                safe_model_id = model_id.replace(".", "_").replace("-", "_").replace(" ", "_")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔘 모두 승인", key=f"approve_all_old_{safe_model_id}"):
                        for i, detection in enumerate(detections):
                            st.session_state.verification_status[f"{model_id}_{i}"] = "approved"
                        st.success("모든 검출이 승인되었습니다.")
                        st.rerun()
                with col2:
                    if st.button("❌ 모두 거부", key=f"reject_all_old_{safe_model_id}"):
                        for i, detection in enumerate(detections):
                            st.session_state.verification_status[f"{model_id}_{i}"] = "rejected"
                        st.warning("모든 검출이 거부되었습니다.")
                        st.rerun()
                with col3:
                    if st.button("🔄 상태 초기화", key=f"reset_status_old_{safe_model_id}"):
                        # 해당 모델 상태만 초기화
                        keys_to_remove = [k for k in st.session_state.verification_status.keys() if k.startswith(f"{model_id}_")]
                        for k in keys_to_remove:
                            del st.session_state.verification_status[k]
                        st.info("상태가 초기화되었습니다.")
                        st.rerun()

                # 모델별 검출 결과 표시
                system.render_detection_list(detections, model_id)

        # 수작업 라벨링 섹션
        st.divider()
        st.subheader("✏️ 수작업 라벨링")

        # 수작업 라벨링 활성화 체크박스
        enable_manual = st.checkbox("🎨 수작업 라벨링 모드 활성화",
                                   help="이미지에 직접 바운딩 박스를 그려 라벨을 추가할 수 있습니다.")

        if enable_manual:
            if st.session_state.current_image:
                st.info("💡 이미지를 클릭하고 드래그하여 바운딩 박스를 그릴 수 있습니다.")

                # 수작업 라벨링을 위한 클래스 선택
                available_classes = system.class_names if hasattr(system, 'class_names') else []
                if available_classes:
                    selected_class = st.selectbox("라벨 클래스 선택:", available_classes, key="manual_class_select")

                    # 수작업 검출 결과 초기화
                    if 'manual_detections' not in st.session_state:
                        st.session_state.manual_detections = []

                    # 간단한 수작업 라벨링 인터페이스
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write("**수작업 라벨링 좌표 입력:**")
                        with st.form("manual_labeling_form"):
                            col_x1, col_y1, col_x2, col_y2 = st.columns(4)
                            with col_x1:
                                x1 = st.number_input("X1", min_value=0, step=1, key="manual_x1")
                            with col_y1:
                                y1 = st.number_input("Y1", min_value=0, step=1, key="manual_y1")
                            with col_x2:
                                x2 = st.number_input("X2", min_value=0, step=1, key="manual_x2")
                            with col_y2:
                                y2 = st.number_input("Y2", min_value=0, step=1, key="manual_y2")

                            if st.form_submit_button("➕ 라벨 추가"):
                                if x2 > x1 and y2 > y1:
                                    manual_detection = {
                                        'class_name': selected_class,
                                        'confidence': 1.0,  # 수작업은 100% 신뢰도
                                        'bbox': [x1, y1, x2, y2],
                                        'model_id': 'manual'
                                    }
                                    st.session_state.manual_detections.append(manual_detection)

                                    # detection_results에 manual 모델 추가
                                    if 'manual' not in st.session_state.detection_results:
                                        st.session_state.detection_results['manual'] = []
                                    st.session_state.detection_results['manual'] = st.session_state.manual_detections.copy()

                                    st.success(f"✅ {selected_class} 라벨이 추가되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("❌ 올바른 좌표를 입력하세요 (X2 > X1, Y2 > Y1)")

                    with col2:
                        st.write("**현재 수작업 라벨:**")
                        if st.session_state.manual_detections:
                            for i, detection in enumerate(st.session_state.manual_detections):
                                st.write(f"{i+1}. {detection['class_name']}")
                                if st.button("🗑️", key=f"delete_manual_{i}", help="삭제"):
                                    st.session_state.manual_detections.pop(i)
                                    st.session_state.detection_results['manual'] = st.session_state.manual_detections.copy()
                                    st.rerun()
                        else:
                            st.info("수작업 라벨이 없습니다.")

                    # 현재 이미지에 수작업 라벨 오버레이 표시
                    if st.session_state.manual_detections:
                        overlay_image = st.session_state.current_image['image'].copy()
                        for detection in st.session_state.manual_detections:
                            x1, y1, x2, y2 = detection['bbox']
                            cv2.rectangle(overlay_image, (x1, y1), (x2, y2), (255, 0, 255), 3)  # 보라색
                            cv2.putText(overlay_image, detection['class_name'], (x1, y1-10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

                        st.image(overlay_image, caption="수작업 라벨링 결과")
                else:
                    st.warning("⚠️ 사용 가능한 클래스가 없습니다.")
                    st.info("📚 기본 클래스 목록을 제공합니다.")
                    # 기본 클래스 참조 표시
                    default_classes = [
                        "17_POWER OUTLET(CONCENT)_(PO)_p01",
                        "22_CM1214 RS422-485_6ES7241-1CH32-0XB0(PLC RS422-485)_p01",
                        "24,25_GRAPHIC PANEL_6AV7240-3MC07-0HA0(GP)_p01",
                        "19_AUXILIARY RELAY(1a1b)_PLC-RSC-230UC-21_p01",
                        "2,3,4,5_CIRCUIT BREAKER_BK63H 2P_p01"
                    ]
                    for i, class_name in enumerate(default_classes):
                        st.text(f"{i}: {class_name}")
            else:
                st.warning("⚠️ 먼저 도면을 업로드하세요.")

        # 각 모델별 결과 탭 (고정 탭 3개 이후부터 시작)
        for tab_idx, (model_id, detections) in enumerate(st.session_state.detection_results.items()):
            actual_tab_idx = tab_idx + 3  # 고정 탭 3개 다음부터
            with tabs[actual_tab_idx]:
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

                if not detections:
                    st.info(f"{model_info['name']} 모델에서 검출된 심볼이 없습니다.")
                else:
                    # 모델별 통계
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("검출 수", len(detections))
                    with col2:
                        import numpy as np
                        avg_conf = np.mean([d['confidence'] for d in detections])
                        st.metric("평균 신뢰도", f"{avg_conf:.3f}")
                    with col3:
                        unique_classes = len(set(d['class_name'] for d in detections))
                        st.metric("검출 클래스 수", unique_classes)

                    # 모델별 일괄 처리 버튼
                    # 안전한 키 생성 (특수문자 제거)
                    safe_model_id = model_id.replace(".", "_").replace("-", "_").replace(" ", "_")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔘 모두 승인", key=f"approve_all_{safe_model_id}"):
                            for i, detection in enumerate(detections):
                                st.session_state.verification_status[f"{model_id}_{i}"] = "approved"
                            st.success(f"{model_info['name']}의 모든 검출이 승인되었습니다.")
                            st.rerun()
                    with col2:
                        if st.button("❌ 모두 거부", key=f"reject_all_{safe_model_id}"):
                            for i, detection in enumerate(detections):
                                st.session_state.verification_status[f"{model_id}_{i}"] = "rejected"
                            st.warning(f"{model_info['name']}의 모든 검출이 거부되었습니다.")
                            st.rerun()
                    with col3:
                        if st.button("🔄 상태 초기화", key=f"reset_status_{safe_model_id}"):
                            # 해당 모델 상태만 초기화
                            keys_to_remove = [k for k in st.session_state.verification_status.keys() if k.startswith(f"{model_id}_")]
                            for k in keys_to_remove:
                                del st.session_state.verification_status[k]
                            st.info("상태가 초기화되었습니다.")
                            st.rerun()

                    # 검출 결과 표시
                    # 모델 ID를 추가한 검출 결과
                    detections_with_model = []
                    for detection in detections:
                        det = detection.copy()
                        det['model_id'] = model_id
                        detections_with_model.append(det)
                    render_detection_list(system, detections_with_model, model_id)


def render_detection_list(system, detections, prefix):
    """검출 결과를 리스트 형태로 표시 (정답 비교 포함)"""
    import os  # 함수 내에서 명시적으로 import
    # 안전한 prefix 생성 (특수문자 제거)
    safe_prefix = prefix.replace(".", "_").replace("-", "_").replace(" ", "_")
    # 검출 결과를 리스트 형태로 표시
    st.subheader("🔍 검출 결과")
    for i, detection in enumerate(detections):
        status_key = f"{prefix}_{i}"  # 실제 저장용 키는 원본 prefix 사용
        current_status = st.session_state.verification_status.get(status_key, "pending")

        # 상태에 따른 컨테이너 스타일
        if current_status == "approved":
            container_style = "background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
        elif current_status == "rejected":
            container_style = "background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
        else:
            container_style = "background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; border-radius: 5px; margin-bottom: 10px;"

        with st.container():
            col1, col2, col3, col4 = st.columns([2, 4, 2, 2])

            with col1:
                # 4개의 서브 컬럼으로 나누기 (Ground Truth, 모델 검출, OCR 결과, 실제 심볼)
                x1, y1, x2, y2 = detection['bbox']
                image = st.session_state.current_image['image']
                h, w = image.shape[:2]
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
                cropped = image[y1:y2, x1:x2]

                img_col1, img_col2, img_col3, img_col4 = st.columns(4)

                with img_col1:
                    # Ground Truth 라벨링 이미지 표시
                    st.caption("🏷️ 실제 라벨링", help="모델 훈련 시 사용된 정답 라벨링 데이터입니다. Ground Truth와의 IoU(Intersection over Union)를 통해 검출 정확도를 확인할 수 있습니다.")
                    ground_truth = system.load_ground_truth_for_current_image()
                    if ground_truth:
                        # 현재 검출 위치와 가장 가까운 Ground Truth 찾기
                        best_gt = None
                        best_iou = 0
                        # 검출 bbox를 정수로 변환
                        det_bbox = [int(x) for x in detection['bbox']]

                        for gt in ground_truth:
                            gt_bbox = system.yolo_to_xyxy(
                                gt['x_center'], gt['y_center'],
                                gt['width'], gt['height'],
                                w, h
                            )
                            iou = system.calculate_iou(det_bbox, gt_bbox)
                            if iou > best_iou:
                                best_iou = iou
                                best_gt = gt

                        # IoU 임계값을 0.1로 낮춤 (10% 이상 겹치면 매칭)
                        if best_gt and best_iou > 0.1:
                            # Ground Truth 박스 영역 crop
                            gt_x1, gt_y1, gt_x2, gt_y2 = system.yolo_to_xyxy(
                                best_gt['x_center'], best_gt['y_center'],
                                best_gt['width'], best_gt['height'],
                                w, h
                            )
                            gt_x1, gt_y1, gt_x2, gt_y2 = max(0, gt_x1), max(0, gt_y1), min(w, gt_x2), min(h, gt_y2)
                            gt_cropped = image[gt_y1:gt_y2, gt_x1:gt_x2]
                            if gt_cropped.size > 0:
                                st.image(gt_cropped, width=100, caption=f"GT: {best_gt['class_name']} (IoU:{best_iou:.2f})")
                            else:
                                st.info("GT 영역 오류")
                        elif best_gt:
                            # IoU가 낮더라도 가장 가까운 GT 표시
                            st.info(f"낮은 IoU: {best_iou:.2f}")
                        else:
                            st.info("GT 없음")
                    else:
                        st.info("라벨 없음")

                with img_col2:
                    # 모델이 검출한 이미지 표시
                    st.caption("🔍 모델 검출", help="AI 모델(YOLOv8)이 현재 검출한 영역입니다. 바운딩 박스 좌표와 신뢰도를 기반으로 추출된 이미지를 보여줍니다.")
                    if cropped.size > 0:
                        st.image(cropped, width=100, caption=f"검출: {detection['class_name']}")
                    else:
                        st.warning("검출 영역 오류")

                with img_col3:
                    # OCR 결과 컬럼 추가
                    st.caption("🔍 OCR 결과", help="Enhanced OCR로 추출된 텍스트 결과입니다.")
                    if detection.get('ocr_text'):
                        st.success(f"✅ '{detection['ocr_text']}'")
                        if detection.get('matched_truth'):
                            st.info(f"GT: {detection['matched_truth']}")
                    elif detection.get('detection_type') == 'ocr_verified':
                        st.success("✅ OCR 검증됨")
                    elif st.session_state.get('use_enhanced_ocr', False):
                        # Enhanced OCR가 활성화되었지만 이 검출에서는 OCR 텍스트가 추출되지 않음
                        st.warning("OCR 추출 실패")
                    else:
                        st.info("OCR 미적용")

                with img_col4:
                    # 검출된 클래스의 실제 심볼 이미지 표시
                    st.caption("📚 실제 심볼", help="해당 클래스의 표준 심볼 이미지입니다. class_examples 폴더의 참조 이미지로 올바른 심볼인지 시각적으로 비교할 수 있습니다.")
                    example_path = system.get_class_example_image(detection['class_name'])
                    if example_path and os.path.exists(example_path):
                        # 파일명에서 심볼 정보 추출
                        filename = os.path.basename(example_path)
                        st.image(example_path, width=100, caption=detection['class_name'])
                    else:
                        st.info("심볼 이미지 없음")

            with col2:
                # 현재 클래스 이름 (수정된 것이 있으면 그것을 사용)
                current_class_name = st.session_state.modified_classes.get(
                    status_key, detection['class_name']
                )

                # 항상 클래스 이름 표시
                st.write(f"**클래스**: {current_class_name}")

                # 편집 모드일 때만 선택박스 표시
                is_editing = st.session_state.edit_mode.get(status_key, False)
                if is_editing:
                    # 클래스 선택을 위한 드롭다운
                    available_classes = list(system.pricing_data.keys())

                    new_class_name = st.selectbox(
                        "새 클래스 선택:",
                        available_classes,
                        index=available_classes.index(current_class_name) if current_class_name in available_classes else 0,
                        key=f"select_new_{prefix}_{i}",
                        help="클래스를 선택한 후 '💾 수정 완료' 버튼을 눌러주세요"
                    )

                    # 선택된 값을 임시로 저장
                    st.session_state[f"temp_class_{status_key}"] = new_class_name

                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    st.write(f"📊 **신뢰도**: {detection['confidence']:.1%}")
                    model_name = detection.get('model', detection.get('model_id', 'unknown'))
                    st.write(f"🤖 **모델**: {model_name}")
                with col2_2:
                    st.write(f"📍 **위치**: ({x1},{y1})")
                    st.write(f"📏 **크기**: {x2-x1}×{y2-y1}px")

            with col3:
                # 현재 상태 표시
                if current_status == "approved":
                    st.success("✅ 승인됨")
                elif current_status == "rejected":
                    st.error("❌ 거부됨")
                else:
                    st.info("⏳ 대기중")

            with col4:
                # 액션 버튼
                is_editing = st.session_state.edit_mode.get(status_key, False)

                # 모든 버튼을 세로로 배치 (안전한 키 사용)
                if st.button("✅ 승인", key=f"approve_{safe_prefix}_{i}",
                            disabled=(current_status=="approved" or is_editing),
                            use_container_width=True):
                    st.session_state.verification_status[status_key] = "approved"
                    st.rerun()

                if st.button("❌ 거부", key=f"reject_{safe_prefix}_{i}",
                            disabled=(current_status=="rejected" or is_editing),
                            use_container_width=True):
                    st.session_state.verification_status[status_key] = "rejected"
                    st.rerun()

                # 토글 방식으로 수정 버튼 동작
                edit_button_label = "💾 수정 완료" if is_editing else "✏️ 수정"
                edit_button_type = "primary" if is_editing else "secondary"
                if st.button(edit_button_label, key=f"edit_{safe_prefix}_{i}",
                            use_container_width=True,
                            type=edit_button_type):
                    if is_editing:
                        # 수정 완료 - 선택된 클래스 저장
                        temp_class = st.session_state.get(f"temp_class_{status_key}")
                        if temp_class:
                            st.session_state.modified_classes[status_key] = temp_class
                        st.session_state.edit_mode[status_key] = False
                    else:
                        # 수정 시작
                        st.session_state.edit_mode[status_key] = True
                    st.rerun()

                if st.button("↩️ 초기화", key=f"reset_{safe_prefix}_{i}",
                            use_container_width=True):
                    if status_key in st.session_state.verification_status:
                        del st.session_state.verification_status[status_key]
                    if status_key in st.session_state.modified_classes:
                        del st.session_state.modified_classes[status_key]
                    if status_key in st.session_state.edit_mode:
                        del st.session_state.edit_mode[status_key]
                    st.rerun()


def render_detection_list_with_voting(system, detections, prefix):
    """검출 결과를 리스트 형태로 표시 (Voting 정보 포함)"""
    import os  # 함수 내에서 명시적으로 import
    # 검출 결과를 리스트 형태로 표시
    st.subheader("🔍 검출 결과 (Voting 정보 포함)")
    for i, detection in enumerate(detections):
        status_key = f"{prefix}_{i}"
        current_status = st.session_state.verification_status.get(status_key, "pending")

        # 상태에 따른 컨테이너 스타일
        if current_status == "approved":
            container_style = "background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
        elif current_status == "rejected":
            container_style = "background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
        else:
            container_style = "background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; border-radius: 5px; margin-bottom: 10px;"

        with st.container():
            col1, col2, col3, col4 = st.columns([2, 4, 2, 2])

            with col1:
                # 4개의 서브 컬럼으로 나누기 (Ground Truth, 모델 검출, OCR 결과, 실제 심볼)
                x1, y1, x2, y2 = detection['bbox']
                image = st.session_state.current_image['image']
                h, w = image.shape[:2]
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
                cropped = image[y1:y2, x1:x2]

                img_col1, img_col2, img_col3, img_col4 = st.columns(4)

                with img_col1:
                    # Ground Truth 라벨링 이미지 표시
                    st.caption("🏷️ 실제 라벨링", help="모델 훈련 시 사용된 정답 라벨링 데이터입니다. Ground Truth와의 IoU(Intersection over Union)를 통해 검출 정확도를 확인할 수 있습니다.")
                    ground_truth = system.load_ground_truth_for_current_image()
                    if ground_truth:
                        # 현재 검출 위치와 가장 가까운 Ground Truth 찾기
                        best_gt = None
                        best_iou = 0
                        # 검출 bbox를 정수로 변환
                        det_bbox = [int(x) for x in detection['bbox']]

                        for gt in ground_truth:
                            gt_bbox = system.yolo_to_xyxy(
                                gt['x_center'], gt['y_center'],
                                gt['width'], gt['height'],
                                w, h
                            )
                            iou = system.calculate_iou(det_bbox, gt_bbox)
                            if iou > best_iou:
                                best_iou = iou
                                best_gt = gt

                        # IoU 임계값을 0.1로 낮춤 (10% 이상 겹치면 매칭)
                        if best_gt and best_iou > 0.1:
                            # Ground Truth 박스 영역 crop
                            gt_x1, gt_y1, gt_x2, gt_y2 = system.yolo_to_xyxy(
                                best_gt['x_center'], best_gt['y_center'],
                                best_gt['width'], best_gt['height'],
                                w, h
                            )
                            gt_x1, gt_y1, gt_x2, gt_y2 = max(0, gt_x1), max(0, gt_y1), min(w, gt_x2), min(h, gt_y2)
                            gt_cropped = image[gt_y1:gt_y2, gt_x1:gt_x2]
                            if gt_cropped.size > 0:
                                # Ground Truth에 이미 class_name이 있음 (load 시 추가함)
                                gt_class_name = best_gt.get('class_name', f"Class {best_gt['class_id']}")
                                st.image(gt_cropped, caption=f"GT: {gt_class_name} (IoU:{best_iou:.2f})")
                            else:
                                st.info("GT 영역 오류")
                        elif best_gt:
                            # IoU가 낮더라도 가장 가까운 GT 표시
                            st.info(f"낮은 IoU: {best_iou:.2f}")
                        else:
                            st.info("GT 없음")
                    else:
                        st.info("라벨 없음")

                with img_col2:
                    # 모델이 검출한 이미지 표시
                    st.caption("🔍 모델 검출", help="AI 모델(YOLOv8)이 현재 검출한 영역입니다. 바운딩 박스 좌표와 신뢰도를 기반으로 추출된 이미지를 보여줍니다.")
                    if cropped.size > 0:
                        st.image(cropped, caption=f"검출: {detection['class_name']}")
                    else:
                        st.warning("검출 영역 오류")

                with img_col3:
                    # OCR 결과 컬럼 추가
                    st.caption("🔍 OCR 결과", help="Enhanced OCR로 추출된 텍스트 결과입니다.")
                    if detection.get('ocr_text'):
                        st.success(f"✅ '{detection['ocr_text']}'")
                        if detection.get('matched_truth'):
                            st.info(f"GT: {detection['matched_truth']}")
                    elif detection.get('detection_type') == 'ocr_verified':
                        st.success("✅ OCR 검증됨")
                    elif st.session_state.get('use_enhanced_ocr', False):
                        # Enhanced OCR가 활성화되었지만 이 검출에서는 OCR 텍스트가 추출되지 않음
                        st.warning("OCR 추출 실패")
                    else:
                        st.info("OCR 미적용")

                with img_col4:
                    # 검출된 클래스의 실제 심볼 이미지 표시
                    st.caption("📚 실제 심볼", help="해당 클래스의 표준 심볼 이미지입니다. class_examples 폴더의 참조 이미지로 올바른 심볼인지 시각적으로 비교할 수 있습니다.")
                    example_path = system.get_class_example_image(detection['class_name'])
                    if example_path and os.path.exists(example_path):
                        st.image(example_path, caption=detection['class_name'])
                    else:
                        st.info("심볼 이미지 없음")

            with col2:
                # 클래스명 표시
                st.write(f"**클래스**: {detection['class_name']}")

                # Voting 정보 표시
                if 'voting_info' in detection:
                    voting_info = detection['voting_info']
                    st.write(f"🗳️ **투표**: {voting_info['total_votes']}개 모델")
                    st.write(f"📊 **신뢰도**: {detection['confidence']:.1%}")

                    # 참여 모델 목록 (간단히)
                    if 'models' in voting_info:
                        models_str = ", ".join(voting_info['models'][:3])  # 처음 3개만
                        if len(voting_info['models']) > 3:
                            models_str += f" 외 {len(voting_info['models'])-3}개"
                        st.write(f"🤖 **모델**: {models_str}")

            with col3:
                # 현재 상태 표시
                if current_status == "approved":
                    st.success("✅ 승인됨")
                elif current_status == "rejected":
                    st.error("❌ 거부됨")
                else:
                    st.info("🕰️ 대기 중")

            with col4:
                # 개별 상태 변경 버튼
                if current_status != "approved":
                    if st.button("✅ 승인", key=f"approve_{prefix}_{i}"):
                        st.session_state.verification_status[status_key] = "approved"
                        st.rerun()
                if current_status != "rejected":
                    if st.button("❌ 거부", key=f"reject_{prefix}_{i}"):
                        st.session_state.verification_status[status_key] = "rejected"
                        st.rerun()
                if current_status != "pending":
                    if st.button("🔄 초기화", key=f"reset_{prefix}_{i}"):
                        del st.session_state.verification_status[status_key]
                        st.rerun()

def render_manual_labeling(system, prefix="unified"):
    """수작업 라벨링 섹션"""
    st.subheader("🎨 수작업 라벨링")
    st.write("모델이 놓친 부품이 있다면 직접 그려서 추가하세요:")

    # 수작업 라벨링 활성화 옵션
    enable_manual = st.checkbox("수작업 라벨링 활성화", value=False, key=f"enable_manual_labeling_{prefix}")

    if enable_manual:
        # streamlit-drawable-canvas 가용성 확인
        try:
            from streamlit_drawable_canvas import st_canvas
            CANVAS_AVAILABLE = True
        except ImportError:
            CANVAS_AVAILABLE = False

        if not CANVAS_AVAILABLE:
            st.error("❌ streamlit-drawable-canvas가 설치되지 않았습니다.")
            st.code("pip install streamlit-drawable-canvas")
            return

        try:
            # 이미지가 있는지 확인
            if not (st.session_state.current_image and 'image' in st.session_state.current_image):
                st.info("이미지를 먼저 로드해주세요.")
                return

            import cv2
            import numpy as np
            from PIL import Image
            import base64
            from io import BytesIO

            img_array = st.session_state.current_image['image']
            # BGR to RGB 변환 (OpenCV 이미지인 경우)
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)

            # 그리기 도구 설정 (네모 박스만 사용)
            drawing_mode = "rect"

            # 이미지 크기 조정
            canvas_height = 700
            img_height, img_width = img_array.shape[:2]
            aspect_ratio = img_width / img_height
            canvas_width = int(canvas_height * aspect_ratio)

            # 이미지를 캔버스 크기에 맞게 리사이즈
            img_resized = cv2.resize(img_array, (canvas_width, canvas_height))

            st.write("✏️ 수작업 라벨링:")
            st.info("🎯 캔버스에서 빨간 박스를 그려주세요:")

            # 캔버스 생성 - 더 안전한 접근법
            try:
                # PIL 이미지 생성 시 더 안전한 방법 사용
                pil_image = Image.fromarray(img_resized.astype(np.uint8))

                canvas_result = st_canvas(
                    fill_color="rgba(255, 165, 0, 0.3)",  # 투명한 주황색 채우기
                    stroke_width=3,
                    stroke_color="#FF0000",  # 빨간색 테두리
                    background_image=pil_image,
                    update_streamlit=True,
                    height=canvas_height,
                    width=canvas_width,
                    drawing_mode=drawing_mode,
                    point_display_radius=0,
                    key=f"canvas_{prefix}",
                    display_toolbar=True,
                )
            except Exception as canvas_error:
                st.error(f"캔버스 생성 오류: {str(canvas_error)}")
                st.info("streamlit-drawable-canvas 버전 호환성 문제일 수 있습니다.")
                st.code("pip install streamlit-drawable-canvas==0.9.3")

                # 대안적 해결책: 기본 이미지 표시
                st.warning("🔧 캔버스 대신 기본 이미지를 표시합니다.")
                st.image(img_resized, caption="수작업 라벨링할 이미지")
                st.info("수작업 라벨링을 사용하려면 streamlit-drawable-canvas 패키지를 다시 설치해주세요.")
                return

            # 그려진 객체가 있으면 처리
            if canvas_result.json_data is not None:
                objects = canvas_result.json_data["objects"]

                if objects:
                    st.write(f"🎯 {len(objects)}개의 박스가 그려졌습니다.")

                    # 클래스 선택을 위한 selectbox
                    available_classes = list(system.pricing_data.keys())
                    selected_class = st.selectbox(
                        "검출할 클래스를 선택하세요:",
                        available_classes,
                        key=f"manual_class_select_{prefix}"
                    )

                    # 신뢰도 설정
                    confidence = st.slider(
                        "신뢰도 설정:",
                        min_value=0.1,
                        max_value=1.0,
                        value=0.9,
                        step=0.1,
                        key=f"manual_confidence_{prefix}"
                    )

                    if st.button("✅ 수작업 검출 추가", key=f"add_manual_detection_{prefix}"):
                        # 캔버스 좌표를 원본 이미지 좌표로 변환
                        scale_x = img_width / canvas_width
                        scale_y = img_height / canvas_height

                        manual_detections = []
                        for obj in objects:
                            if obj["type"] == "rect":
                                # 캔버스 좌표
                                left = obj["left"]
                                top = obj["top"]
                                width = obj["width"]
                                height = obj["height"]

                                # 원본 이미지 좌표로 변환
                                x1 = int(left * scale_x)
                                y1 = int(top * scale_y)
                                x2 = int((left + width) * scale_x)
                                y2 = int((top + height) * scale_y)

                                # 이미지 경계 내로 제한
                                x1 = max(0, min(x1, img_width))
                                y1 = max(0, min(y1, img_height))
                                x2 = max(0, min(x2, img_width))
                                y2 = max(0, min(y2, img_height))

                                detection = {
                                    'bbox': [x1, y1, x2, y2],
                                    'confidence': confidence,
                                    'class_name': selected_class,
                                    'model': 'manual',
                                    'detection_type': 'manual'
                                }
                                manual_detections.append(detection)

                        # 세션 상태에 추가
                        if 'manual' not in st.session_state.detection_results:
                            st.session_state.detection_results['manual'] = []
                        st.session_state.detection_results['manual'].extend(manual_detections)

                        st.success(f"✅ {len(manual_detections)}개의 수작업 검출이 추가되었습니다.")
                        st.rerun()

        except Exception as e:
            st.error(f"수작업 라벨링 오류: {str(e)}")
            st.info("streamlit-drawable-canvas 패키지 설치를 확인해주세요: pip install streamlit-drawable-canvas")
            import traceback
            with st.expander("상세 오류 정보"):
                st.code(traceback.format_exc())
    else:
        st.info("수작업 라벨링을 사용하려면 위의 체크박스를 선택하세요.")