"""
견적서 PDF 자동 생성

ReportLab을 사용하여 전문적인 견적서 PDF 생성
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image as RLImage
)
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


class QuotePDFGenerator:
    """견적서 PDF 생성기"""

    def __init__(self, company_name: str = "AX Manufacturing Solutions"):
        self.company_name = company_name
        self.styles = getSampleStyleSheet()

        # 커스텀 스타일 추가
        self.styles.add(ParagraphStyle(
            name='Title',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            spaceBefore=12
        ))

        self.styles.add(ParagraphStyle(
            name='Normal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333')
        ))

    def generate_quote_pdf(
        self,
        quote_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        견적서 PDF 생성

        Args:
            quote_data: {
                "quote_number": "Q-2025-001",
                "date": "2025-10-31",
                "customer_name": "ABC Manufacturing",
                "part_info": {
                    "name": "Intermediate Shaft",
                    "part_number": "A12-311197-9",
                    "material": "STS304",
                    "quantity": 10
                },
                "cost_breakdown": {
                    "material_cost_per_unit": 25.5,
                    "process_costs": [...],
                    "total_setup_cost": 150.0,
                    "unit_cost": 85.0,
                    "total_cost": 1000.0,
                    "lead_time_days": 5.5
                },
                "qc_checklist": ["Ø21.5 ± 0.1", "Ø38 H12"],
                "manufacturing_processes": {...}
            }
            output_path: PDF 저장 경로 (None이면 bytes 반환만)

        Returns:
            PDF 파일의 bytes
        """
        try:
            # PDF 버퍼
            buffer = io.BytesIO()

            # 문서 생성
            if output_path:
                doc = SimpleDocTemplate(
                    output_path,
                    pagesize=A4,
                    rightMargin=20*mm,
                    leftMargin=20*mm,
                    topMargin=20*mm,
                    bottomMargin=20*mm
                )
            else:
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=A4,
                    rightMargin=20*mm,
                    leftMargin=20*mm,
                    topMargin=20*mm,
                    bottomMargin=20*mm
                )

            # 문서 요소들
            elements = []

            # 헤더
            elements.extend(self._create_header(quote_data))

            # 고객 및 견적 정보
            elements.extend(self._create_quote_info(quote_data))

            # 부품 정보
            elements.extend(self._create_part_info(quote_data))

            # 제조 공정
            if "manufacturing_processes" in quote_data:
                elements.extend(self._create_manufacturing_processes(quote_data))

            # 비용 명세
            elements.extend(self._create_cost_breakdown(quote_data))

            # QC 체크리스트
            if "qc_checklist" in quote_data and quote_data["qc_checklist"]:
                elements.extend(self._create_qc_checklist(quote_data))

            # Footer
            elements.extend(self._create_footer(quote_data))

            # PDF 생성
            doc.build(elements)

            # bytes 반환
            if output_path:
                with open(output_path, 'rb') as f:
                    pdf_bytes = f.read()
            else:
                pdf_bytes = buffer.getvalue()

            logger.info(f"Generated quote PDF: {len(pdf_bytes)} bytes")
            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise ValueError(f"PDF generation error: {str(e)}")

    def _create_header(self, quote_data: Dict[str, Any]) -> List:
        """헤더 생성"""
        elements = []

        # 회사명
        company_para = Paragraph(
            f"<b>{self.company_name}</b>",
            self.styles['Title']
        )
        elements.append(company_para)

        # 견적서 제목
        title_para = Paragraph(
            "MANUFACTURING QUOTATION",
            self.styles['Title']
        )
        elements.append(title_para)
        elements.append(Spacer(1, 12))

        return elements

    def _create_quote_info(self, quote_data: Dict[str, Any]) -> List:
        """견적 정보 섹션"""
        elements = []

        # 섹션 헤더
        elements.append(Paragraph("Quote Information", self.styles['SectionHeader']))

        # 정보 테이블
        quote_number = quote_data.get("quote_number", "N/A")
        date = quote_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        customer = quote_data.get("customer_name", "N/A")
        valid_until = quote_data.get("valid_until", "30 days")

        info_data = [
            ["Quote Number:", quote_number, "Date:", date],
            ["Customer:", customer, "Valid Until:", valid_until],
        ]

        info_table = Table(info_data, colWidths=[35*mm, 55*mm, 30*mm, 50*mm])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
            ('FONT', (2, 0), (2, -1), 'Helvetica-Bold', 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 12))

        return elements

    def _create_part_info(self, quote_data: Dict[str, Any]) -> List:
        """부품 정보 섹션"""
        elements = []

        part_info = quote_data.get("part_info", {})

        # 섹션 헤더
        elements.append(Paragraph("Part Information", self.styles['SectionHeader']))

        # 부품 정보 테이블
        part_data = [
            ["Part Name:", part_info.get("name", "N/A")],
            ["Part Number:", part_info.get("part_number", "N/A")],
            ["Material:", part_info.get("material", "N/A")],
            ["Quantity:", str(part_info.get("quantity", 1))],
        ]

        part_table = Table(part_data, colWidths=[40*mm, 130*mm])
        part_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(part_table)
        elements.append(Spacer(1, 12))

        return elements

    def _create_manufacturing_processes(self, quote_data: Dict[str, Any]) -> List:
        """제조 공정 섹션"""
        elements = []

        processes = quote_data.get("manufacturing_processes", {})

        if not processes:
            return elements

        # 섹션 헤더
        elements.append(Paragraph("Manufacturing Processes", self.styles['SectionHeader']))

        # 공정 테이블
        process_data = [["Process", "Description"]]

        for process_name, description in processes.items():
            process_data.append([process_name, description])

        process_table = Table(process_data, colWidths=[40*mm, 130*mm])
        process_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))

        elements.append(process_table)
        elements.append(Spacer(1, 12))

        return elements

    def _create_cost_breakdown(self, quote_data: Dict[str, Any]) -> List:
        """비용 명세 섹션"""
        elements = []

        cost_data = quote_data.get("cost_breakdown", {})

        # 섹션 헤더
        elements.append(Paragraph("Cost Breakdown", self.styles['SectionHeader']))

        # 비용 테이블
        breakdown_data = [
            ["Item", "Unit Cost (USD)", "Quantity", "Total (USD)"]
        ]

        # 재료비
        material_cost = cost_data.get("material_cost_per_unit", 0)
        quantity = quote_data.get("part_info", {}).get("quantity", 1)
        breakdown_data.append([
            "Material",
            f"${material_cost:.2f}",
            str(quantity),
            f"${material_cost * quantity:.2f}"
        ])

        # 공정별 비용
        process_costs = cost_data.get("process_costs", [])
        for process in process_costs:
            breakdown_data.append([
                process["name"],
                f"${process['unit_cost']:.2f}",
                str(quantity),
                f"${process['unit_cost'] * quantity:.2f}"
            ])

        # Setup 비용
        setup_cost = cost_data.get("total_setup_cost", 0)
        breakdown_data.append([
            "Setup Cost",
            "-",
            "1",
            f"${setup_cost:.2f}"
        ])

        # 구분선
        breakdown_data.append(["", "", "", ""])

        # 총액
        total_cost = cost_data.get("total_cost", 0)
        breakdown_data.append([
            "TOTAL",
            "",
            "",
            f"${total_cost:.2f}"
        ])

        # 리드타임
        lead_time = cost_data.get("lead_time_days", 0)
        breakdown_data.append([
            "Lead Time",
            "",
            "",
            f"{lead_time:.1f} days"
        ])

        cost_table = Table(breakdown_data, colWidths=[60*mm, 35*mm, 35*mm, 40*mm])
        cost_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('FONT', (0, 1), (-1, -3), 'Helvetica', 9),
            ('FONT', (0, -2), (-1, -1), 'Helvetica-Bold', 11),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -3), 0.5, colors.grey),
            ('LINEABOVE', (0, -2), (-1, -2), 2, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -3), [colors.white, colors.HexColor('#f8f9fa')]),
            ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#e8f5e9')),
        ]))

        elements.append(cost_table)
        elements.append(Spacer(1, 12))

        return elements

    def _create_qc_checklist(self, quote_data: Dict[str, Any]) -> List:
        """QC 체크리스트 섹션"""
        elements = []

        qc_items = quote_data.get("qc_checklist", [])

        if not qc_items:
            return elements

        # 섹션 헤더
        elements.append(Paragraph("Quality Control Checklist", self.styles['SectionHeader']))

        # QC 테이블
        qc_data = [["Critical Measurements to Verify"]]

        for item in qc_items:
            qc_data.append([item])

        qc_table = Table(qc_data, colWidths=[170*mm])
        qc_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))

        elements.append(qc_table)
        elements.append(Spacer(1, 12))

        return elements

    def _create_footer(self, quote_data: Dict[str, Any]) -> List:
        """Footer 생성"""
        elements = []

        elements.append(Spacer(1, 20))

        # Terms and Conditions
        terms_para = Paragraph(
            "<b>Terms and Conditions:</b><br/>"
            "• Payment terms: Net 30 days<br/>"
            "• This quotation is valid for 30 days from the date of issue<br/>"
            "• Prices are in USD and exclude taxes<br/>"
            "• Lead time may vary based on material availability",
            self.styles['Normal']
        )
        elements.append(terms_para)

        elements.append(Spacer(1, 20))

        # Generated by
        generated_para = Paragraph(
            f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by AX Manufacturing Solutions AI System</i>",
            ParagraphStyle(
                name='Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
        )
        elements.append(generated_para)

        return elements


# 싱글톤 인스턴스
_pdf_generator_instance = None


def get_pdf_generator() -> QuotePDFGenerator:
    """QuotePDFGenerator 싱글톤 인스턴스 반환"""
    global _pdf_generator_instance
    if _pdf_generator_instance is None:
        _pdf_generator_instance = QuotePDFGenerator()
    return _pdf_generator_instance
