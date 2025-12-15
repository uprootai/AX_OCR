"""
BOM Generation UI Components Module
BOM 생성 관련 UI 컴포넌트들
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from .helpers import safe_mean

def render_bom_generation(system):
    """BOM 생성 및 내보내기"""
    st.header("📊 BOM 생성 및 내보내기")

    # 승인된 검출 결과만 필터링
    approved_detections = []

    # 검증 상태 확인하여 승인된 검출만 수집
    if 'verification_status' in st.session_state:
        # 통합 결과에서 승인된 것들
        for key, status in st.session_state.verification_status.items():
            if status == "approved":
                # key 형식: "unified_0", "voting_1", "model_id_2" 등
                parts = key.split('_')
                if len(parts) >= 2:
                    prefix = parts[0]
                    index = int(parts[-1])

                    # 해당하는 검출 찾기
                    if prefix == "unified":
                        # 통합 결과에서 찾기
                        all_dets = []
                        for model_id, dets in st.session_state.detection_results.items():
                            for det in dets:
                                det_copy = det.copy()
                                det_copy['model_id'] = model_id
                                all_dets.append(det_copy)
                        unique_dets = system.remove_duplicate_detections(all_dets)
                        if index < len(unique_dets):
                            detection = unique_dets[index].copy()
                            # 수정된 클래스 이름이 있으면 적용
                            if key in st.session_state.modified_classes:
                                detection['class_name'] = st.session_state.modified_classes[key]
                            approved_detections.append(detection)
                    elif prefix == "voting":
                        # Voting 결과에서 찾기
                        all_dets = []
                        for model_id, dets in st.session_state.detection_results.items():
                            for det in dets:
                                det_copy = det.copy()
                                det_copy['model_id'] = model_id
                                all_dets.append(det_copy)
                        voting_dets, _ = system.remove_duplicate_detections_with_voting(all_dets)
                        if index < len(voting_dets):
                            detection = voting_dets[index].copy()
                            # 수정된 클래스 이름이 있으면 적용
                            if key in st.session_state.modified_classes:
                                detection['class_name'] = st.session_state.modified_classes[key]
                            approved_detections.append(detection)
                    elif prefix in st.session_state.detection_results:
                        # 개별 모델 결과에서 찾기
                        model_dets = st.session_state.detection_results[prefix]
                        if index < len(model_dets):
                            detection = model_dets[index].copy()
                            # 수정된 클래스 이름이 있으면 적용
                            if key in st.session_state.modified_classes:
                                detection['class_name'] = st.session_state.modified_classes[key]
                            approved_detections.append(detection)

    # 승인된 검출이 없으면 전체 검출 사용 (기본값)
    if not approved_detections:
        st.info("승인된 검출이 없습니다. 전체 검출 결과를 사용합니다.")
        all_detections = []
        for model_id, detections in st.session_state.detection_results.items():
            all_detections.extend(detections)
        approved_detections = all_detections

    if not approved_detections:
        st.info("BOM 생성을 위한 검출 결과가 없습니다.")
        return

    # BOM 테이블 생성
    bom_data = system.create_bom_table(approved_detections)

    st.subheader("📋 생성된 BOM")

    # 승인된 검출 수 표시
    st.success(f"✅ 승인된 검출 {len(approved_detections)}개로 BOM 생성")

    st.dataframe(bom_data)

    # 통계 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 부품 수", len(bom_data))
    with col2:
        total_cost = bom_data['총 가격'].sum()
        st.metric("총 예상 비용", f"{total_cost:,}원")
    with col3:
        unique_types = len(bom_data['부품명'].unique())
        st.metric("부품 종류", unique_types)
    with col4:
        avg_confidence = safe_mean([d['confidence'] for d in approved_detections])
        st.metric("평균 신뢰도", f"{avg_confidence:.3f}")

    # 내보내기 옵션
    st.subheader("📤 내보내기")

    col1, col2 = st.columns(2)
    with col1:
        # Excel 내보내기
        excel_data = system.create_excel_export(approved_detections, bom_data)
        if excel_data:
            st.download_button(
                label="📊 Excel 다운로드",
                data=excel_data,
                file_name=f"BOM_결과_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

    with col2:
        # CSV 내보내기
        csv_data = bom_data.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📄 CSV 다운로드",
            data=csv_data,
            file_name=f"BOM_결과_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )

    # 상세 분석
    st.subheader("📈 상세 분석")

    # 클래스별 분포
    class_distribution = bom_data.groupby('부품명')['수량'].sum().sort_values(ascending=False)
    st.bar_chart(class_distribution)

    # 비용 분석
    cost_analysis = bom_data[['부품명', '총 가격']].sort_values('총 가격', ascending=False).head(10)
    st.write("**비용 상위 10개 부품:**")
    st.dataframe(cost_analysis)