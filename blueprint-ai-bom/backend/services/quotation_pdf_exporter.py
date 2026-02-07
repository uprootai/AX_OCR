"""Quotation PDF Exporter - 견적서 PDF 생성

reportlab 기반 PDF 견적서 내보내기 (프로젝트 전체 / 어셈블리 단위)
QuotationService에서 분리된 독립 모듈
"""

import os
import logging
from pathlib import Path
from typing import Optional

from schemas.quotation import ProjectQuotationResponse, AssemblyQuotationGroup

logger = logging.getLogger(__name__)


# 한글 폰트 경로 후보 목록
_FONT_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/nanum/NanumGothic.ttf",
    "/app/fonts/NanumGothic.ttf",
    "NanumGothic.ttf",
]


def _register_korean_font() -> None:
    """한글 폰트 등록 (NanumGothic)"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for font_path in _FONT_PATHS:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
            except Exception:
                pass
            break


def export_pdf(
    quotation_data: ProjectQuotationResponse,
    output_dir: Path,
    customer_name: Optional[str] = None,
    include_material_breakdown: bool = True,
    notes: Optional[str] = None,
) -> Path:
    """reportlab 기반 견적서 PDF

    Args:
        quotation_data: 프로젝트 견적 집계 데이터
        output_dir: 출력 디렉토리
        customer_name: 고객명 (없으면 quotation_data.customer 사용)
        include_material_breakdown: 재질별 분류 포함 여부
        notes: 비고

    Returns:
        생성된 PDF 파일 경로
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm
    except ImportError:
        raise NotImplementedError(
            "PDF 내보내기를 위해 reportlab 패키지를 설치해주세요: pip install reportlab"
        )

    output_path = output_dir / f"quotation_{quotation_data.project_id}.pdf"

    _register_korean_font()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=1,
    )

    # 제목
    elements.append(Paragraph("견적서 (Quotation)", title_style))
    elements.append(Spacer(1, 10))

    # 메타 정보
    effective_customer = customer_name or quotation_data.customer
    meta_data = [
        ["프로젝트", quotation_data.project_name],
        ["고객", effective_customer],
        ["생성일", quotation_data.created_at[:10]],
        ["세션 수", f"{quotation_data.summary.total_sessions}개"],
        ["완료", f"{quotation_data.summary.completed_sessions}개"],
    ]
    meta_table = Table(meta_data, colWidths=[80, 200])
    meta_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))

    # 세션별 견적 테이블
    table_data = [["No.", "도면번호", "재질", "수량", "소계", "상태"]]
    for idx, item in enumerate(quotation_data.items, 1):
        status = "완료" if item.bom_generated else "대기"
        table_data.append([
            str(idx),
            item.drawing_number[:25] or "-",
            item.material or "-",
            str(item.bom_quantity),
            f"₩{item.subtotal:,.0f}" if item.subtotal > 0 else "-",
            status,
        ])

    col_widths = [30, 120, 60, 40, 80, 40]
    main_table = Table(table_data, colWidths=col_widths)
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
        ('ALIGN', (5, 1), (5, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#F0F0F0')]),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 15))

    # 재질별 분류 (선택)
    if include_material_breakdown and quotation_data.material_groups:
        elements.append(Spacer(1, 10))
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
        )
        elements.append(Paragraph("재질별 분류", subtitle_style))

        mat_data = [["재질", "품목수", "총 수량", "소계"]]
        for mg in quotation_data.material_groups:
            mat_data.append([
                mg.material,
                str(mg.item_count),
                str(mg.total_quantity),
                f"₩{mg.subtotal:,.0f}" if mg.subtotal > 0 else "-",
            ])

        mat_table = Table(mat_data, colWidths=[100, 60, 60, 100])
        mat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B9BD5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(mat_table)
        elements.append(Spacer(1, 15))

    # 요약 테이블
    summary = quotation_data.summary
    summary_data = [
        ["", "소계", f"₩{summary.subtotal:,.0f}"],
        ["", "부가세 (10%)", f"₩{summary.vat:,.0f}"],
        ["", "합계", f"₩{summary.total:,.0f}"],
    ]
    summary_table = Table(summary_data, colWidths=[200, 80, 100])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (1, -1), (-1, -1), colors.HexColor('#E6F3FF')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)

    # 비고
    if notes:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"비고: {notes}", styles['Normal']))

    doc.build(elements)
    return output_path


def export_assembly_pdf(
    quotation_data: ProjectQuotationResponse,
    assembly_drawing_number: str,
    output_dir: Path,
    customer_name: Optional[str] = None,
    notes: Optional[str] = None,
) -> Path:
    """특정 어셈블리만 포함한 PDF 견적서

    Args:
        quotation_data: 프로젝트 견적 집계 데이터
        assembly_drawing_number: 대상 어셈블리 도면번호
        output_dir: 출력 디렉토리
        customer_name: 고객명 (없으면 quotation_data.customer 사용)
        notes: 비고

    Returns:
        생성된 PDF 파일 경로
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm
    except ImportError:
        raise NotImplementedError(
            "PDF 내보내기를 위해 reportlab 패키지를 설치해주세요"
        )

    # 어셈블리 그룹 찾기
    assy_group = next(
        (g for g in quotation_data.assembly_groups
         if g.assembly_drawing_number == assembly_drawing_number),
        None
    )
    if not assy_group:
        raise ValueError(f"어셈블리를 찾을 수 없습니다: {assembly_drawing_number}")

    # 파일명에서 특수문자 제거
    safe_assy = assembly_drawing_number.replace("/", "_").replace(" ", "_")
    output_path = output_dir / f"quotation_{quotation_data.project_id}_{safe_assy}.pdf"

    _register_korean_font()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=15,
        alignment=1,
    )

    # 제목 (어셈블리명 포함)
    title_text = f"견적서 - {assy_group.assembly_description or assembly_drawing_number}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 10))

    # 메타 정보
    effective_customer = customer_name or quotation_data.customer
    meta_data = [
        ["프로젝트", quotation_data.project_name],
        ["고객", effective_customer],
        ["어셈블리", assembly_drawing_number],
        ["품명", assy_group.assembly_description or "-"],
        ["생성일", quotation_data.created_at[:10]],
        ["부품 수", f"{assy_group.total_parts}개"],
    ]
    meta_table = Table(meta_data, colWidths=[80, 220])
    meta_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))

    # 부품 목록 테이블
    table_data = [["No.", "도면번호", "품명", "재질", "수량", "소계"]]
    for idx, item in enumerate(assy_group.items, 1):
        table_data.append([
            str(idx),
            (item.drawing_number or "-")[:20],
            (item.description or "-")[:15],
            item.material or "-",
            str(item.bom_quantity),
            f"₩{item.subtotal:,.0f}" if item.subtotal > 0 else "-",
        ])

    col_widths = [25, 100, 80, 50, 35, 80]
    main_table = Table(table_data, colWidths=col_widths)
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E91E8C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (4, 1), (5, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#FFF0F5')]),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 15))

    # 요약 테이블
    summary_data = [
        ["", "소계", f"₩{assy_group.subtotal:,.0f}"],
        ["", "부가세 (10%)", f"₩{assy_group.vat:,.0f}"],
        ["", "합계", f"₩{assy_group.total:,.0f}"],
    ]
    summary_table = Table(summary_data, colWidths=[200, 80, 100])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (1, -1), (-1, -1), colors.HexColor('#FCE4EC')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)

    if notes:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"비고: {notes}", styles['Normal']))

    doc.build(elements)
    logger.info(f"어셈블리 PDF 생성: {output_path}")
    return output_path
