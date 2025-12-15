"""
BOM Generator Utilities
BOM 생성 관련 유틸리티 함수들
"""
import io
import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from .helpers import safe_mean

def create_bom_table(detections: List[Dict[str, Any]], pricing_data: Dict[str, Any]) -> pd.DataFrame:
    """검출 결과로부터 BOM 테이블 생성"""
    # 동일 부품별로 집계
    component_counts = {}
    for detection in detections:
        class_name = detection['class_name']
        if class_name in component_counts:
            component_counts[class_name]['수량'] += 1
            component_counts[class_name]['신뢰도들'].append(detection['confidence'])
        else:
            component_counts[class_name] = {
                '수량': 1,
                '신뢰도들': [detection['confidence']],
                '모델': detection['model']
            }

    # BOM 테이블 생성
    bom_rows = []
    for i, (class_name, info) in enumerate(component_counts.items(), 1):
        # 가격 정보 조회
        price_info = pricing_data.get(class_name, {})
        unit_price = price_info.get('unit_price', 10000)  # 기본값

        avg_confidence = safe_mean(info['신뢰도들'])
        total_price = unit_price * info['수량']

        bom_rows.append({
            '번호': i,
            '부품명': class_name,
            '수량': info['수량'],
            '단가': unit_price,
            '총 가격': total_price,
            '평균 신뢰도': round(avg_confidence, 3),
            '검출 모델': info['모델'],
            '비고': price_info.get('description', '')
        })

    return pd.DataFrame(bom_rows)

def create_excel_export(bom_data: pd.DataFrame) -> bytes:
    """Excel 파일 생성"""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        bom_data.to_excel(writer, sheet_name='BOM', index=False)

        # 추가 정보 시트
        info_data = pd.DataFrame([
            ['도면 파일', st.session_state.current_image['filename']],
            ['생성 일시', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['사용 모델', ', '.join(st.session_state.selected_models) if 'selected_models' in st.session_state else 'N/A'],
            ['총 부품 수', len(bom_data)],
            ['총 예상 비용', f"{bom_data['총 가격'].sum():,}원"]
        ], columns=['항목', '값'])

        info_data.to_excel(writer, sheet_name='정보', index=False)

    return output.getvalue()

def create_pdf_report(bom_data: pd.DataFrame, detections: List[Dict[str, Any]]) -> bytes:
    """PDF 보고서 생성"""
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # 제목
    title = Paragraph("AI 기반 BOM 분석 보고서", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # 기본 정보
    info_data = [
        ['도면 파일', st.session_state.current_image['filename']],
        ['분석 일시', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['사용 모델', ', '.join(st.session_state.selected_models) if 'selected_models' in st.session_state else 'N/A'],
        ['총 검출 수', str(len(detections))],
        ['부품 종류', str(len(bom_data))],
        ['총 예상 비용', f"{bom_data['총 가격'].sum():,}원"]
    ]

    info_table = Table(info_data)
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(info_table)
    story.append(Spacer(1, 12))

    # BOM 테이블
    bom_title = Paragraph("부품 목록 (BOM)", styles['Heading2'])
    story.append(bom_title)
    story.append(Spacer(1, 12))

    # BOM 데이터를 테이블로 변환
    bom_table_data = [bom_data.columns.tolist()]
    for _, row in bom_data.iterrows():
        bom_table_data.append(row.tolist())

    bom_table = Table(bom_table_data)
    bom_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(bom_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()