"""
PDF Report Service - TECHCROSS 체크리스트 형식 PDF 리포트 생성
"""
import io
import logging
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# 색상 정의
HEADER_BG = colors.HexColor("#1F4E79")
PASS_BG = colors.HexColor("#C6EFCE")
FAIL_BG = colors.HexColor("#FFC7CE")
SKIP_BG = colors.HexColor("#FFEB9C")
LIGHT_GRAY = colors.HexColor("#F5F5F5")


class PDFReportService:
    """TECHCROSS 체크리스트 PDF 리포트 생성"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """커스텀 스타일 설정"""
        # 제목 스타일
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=1,  # center
        ))

        # 부제목 스타일
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=1,
            textColor=colors.gray,
        ))

        # 섹션 헤더
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor=HEADER_BG,
        ))

        # 테이블 셀 텍스트
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
        ))

    def generate_validation_report(
        self,
        validation_data: dict[str, Any],
        project_info: dict[str, Any] = None,
    ) -> bytes:
        """
        검증 결과를 PDF 리포트로 생성

        Args:
            validation_data: validate-with-mapping 엔드포인트 응답 데이터
            project_info: 프로젝트 정보 (선명, 도면번호 등)

        Returns:
            PDF 파일 바이트
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
        )

        elements = []

        # 1. 제목
        elements.append(Paragraph(
            "TECHCROSS BWMS P&ID Validation Report",
            self.styles['ReportTitle']
        ))

        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['ReportSubtitle']
        ))

        elements.append(Spacer(1, 10*mm))

        # 2. 프로젝트 정보
        if project_info:
            elements.append(Paragraph("Project Information", self.styles['SectionHeader']))
            project_table_data = [
                ["Ship Name", project_info.get("ship_name", "-")],
                ["Drawing No.", project_info.get("drawing_no", "-")],
                ["Product Type", project_info.get("product_type", "-")],
                ["Ship Type", project_info.get("ship_type", "-")],
                ["Class Society", project_info.get("class_society", "-")],
            ]
            project_table = Table(project_table_data, colWidths=[50*mm, 100*mm])
            project_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(project_table)
            elements.append(Spacer(1, 8*mm))

        # 3. 필터 정보
        filters = validation_data.get("filters", {})
        elements.append(Paragraph("Applied Filters", self.styles['SectionHeader']))
        filter_table_data = [
            ["Product Type", filters.get("product_type", "-")],
            ["Ship Type", filters.get("ship_type") or "-"],
            ["Class Society", filters.get("class_society") or "-"],
            ["Project Type", filters.get("project_type") or "-"],
        ]
        filter_table = Table(filter_table_data, colWidths=[50*mm, 100*mm])
        filter_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(filter_table)
        elements.append(Spacer(1, 8*mm))

        # 4. 검증 결과 요약
        summary = validation_data.get("summary", {})
        elements.append(Paragraph("Validation Summary", self.styles['SectionHeader']))

        total = summary.get("existence_checked", 0)
        passed = summary.get("passed", 0)
        violations = summary.get("violations", 0)
        pass_rate = summary.get("pass_rate", 0)

        summary_table_data = [
            ["Item", "Count", "Ratio"],
            ["Total Rules", str(summary.get("total_rules", 0)), "-"],
            ["Checked", str(total), "-"],
            ["Passed", str(passed), f"{passed/total*100:.1f}%" if total > 0 else "-"],
            ["Violations", str(violations), f"{violations/total*100:.1f}%" if total > 0 else "-"],
            ["Skipped", str(summary.get("skipped", 0)), "-"],
        ]

        summary_table = Table(summary_table_data, colWidths=[60*mm, 40*mm, 40*mm])
        summary_style = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 3), (-1, 3), PASS_BG),  # Passed row
            ('BACKGROUND', (0, 4), (-1, 4), FAIL_BG),  # Violations row
            ('BACKGROUND', (0, 5), (-1, 5), SKIP_BG),  # Skipped row
        ]
        summary_table.setStyle(TableStyle(summary_style))
        elements.append(summary_table)

        # 통과율 강조
        elements.append(Spacer(1, 5*mm))
        pass_rate_color = PASS_BG if pass_rate >= 90 else (SKIP_BG if pass_rate >= 70 else FAIL_BG)
        pass_rate_table = Table([[f"Pass Rate: {pass_rate:.1f}%"]], colWidths=[140*mm])
        pass_rate_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), pass_rate_color),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(pass_rate_table)
        elements.append(Spacer(1, 10*mm))

        # 5. 통과 항목 (간략)
        passed_items = validation_data.get("passed", [])
        if passed_items:
            elements.append(Paragraph(f"Passed Items ({len(passed_items)})", self.styles['SectionHeader']))
            passed_table_data = [["No", "Rule ID", "Equipment", "Match Type"]]
            for i, item in enumerate(passed_items[:20], 1):  # 최대 20개
                passed_table_data.append([
                    str(i),
                    item.get("rule_id", ""),
                    item.get("equipment", "")[:25],
                    item.get("match_type", ""),
                ])

            if len(passed_items) > 20:
                passed_table_data.append(["...", f"+ {len(passed_items) - 20} more", "", ""])

            passed_table = Table(passed_table_data, colWidths=[15*mm, 40*mm, 55*mm, 40*mm])
            passed_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 1), (-1, -1), PASS_BG),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(passed_table)
            elements.append(Spacer(1, 8*mm))

        # 6. 위반 항목
        violations_items = validation_data.get("violations", [])
        elements.append(Paragraph(f"Violations ({len(violations_items)})", self.styles['SectionHeader']))

        if violations_items:
            violations_table_data = [["No", "Rule ID", "Equipment", "Severity", "Suggestion"]]
            for i, item in enumerate(violations_items, 1):
                violations_table_data.append([
                    str(i),
                    item.get("rule_id", ""),
                    item.get("equipment", "")[:20],
                    item.get("severity", "warning"),
                    item.get("suggestion", "")[:40],
                ])

            violations_table = Table(
                violations_table_data,
                colWidths=[12*mm, 35*mm, 35*mm, 20*mm, 65*mm]
            )
            violations_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 1), (-1, -1), FAIL_BG),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(violations_table)
        else:
            no_violations_table = Table([["No violations found"]], colWidths=[140*mm])
            no_violations_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), PASS_BG),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(no_violations_table)

        # 7. 푸터
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph(
            "Generated by TECHCROSS BWMS Design Checker API",
            self.styles['ReportSubtitle']
        ))

        # PDF 생성
        doc.build(elements)
        buffer.seek(0)

        return buffer.getvalue()

    def generate_checklist_report(
        self,
        validation_data: dict[str, Any],
        all_rules: list[dict],
        project_info: dict[str, Any] = None,
    ) -> bytes:
        """
        전체 체크리스트 형식 PDF 생성

        Args:
            validation_data: 검증 결과 데이터
            all_rules: 모든 규칙 목록
            project_info: 프로젝트 정보

        Returns:
            PDF 파일 바이트
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
        )

        elements = []

        # 제목
        elements.append(Paragraph(
            "TECHCROSS BWMS P&ID Checklist",
            self.styles['ReportTitle']
        ))

        if project_info:
            info_text = f"Ship: {project_info.get('ship_name', '-')} | "
            info_text += f"Drawing: {project_info.get('drawing_no', '-')} | "
            info_text += f"Product: {project_info.get('product_type', '-')}"
            elements.append(Paragraph(info_text, self.styles['ReportSubtitle']))

        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['ReportSubtitle']
        ))

        elements.append(Spacer(1, 8*mm))

        # 결과 맵 생성
        passed_map = {p.get("rule_id"): p for p in validation_data.get("passed", [])}
        violation_map = {v.get("rule_id"): v for v in validation_data.get("violations", [])}
        skipped_map = {s.get("rule_id"): s for s in validation_data.get("skipped", [])}

        # 체크리스트 테이블
        table_data = [["No", "Rule ID", "Check Item", "Status", "Result"]]

        for i, rule in enumerate(all_rules, 1):
            rule_id = rule.get("rule_id", "")
            rule_name = rule.get("name", "")[:35]

            if rule_id in passed_map:
                status = "Checked"
                result = "PASS"
                bg_color = PASS_BG
            elif rule_id in violation_map:
                status = "Checked"
                result = "FAIL"
                bg_color = FAIL_BG
            elif rule_id in skipped_map:
                status = "Skipped"
                result = "-"
                bg_color = SKIP_BG
            else:
                status = "N/A"
                result = "-"
                bg_color = LIGHT_GRAY

            table_data.append([str(i), rule_id, rule_name, status, result])

        # 테이블 생성 (페이지당 40행)
        rows_per_page = 40
        for start_idx in range(0, len(table_data) - 1, rows_per_page):
            if start_idx > 0:
                elements.append(PageBreak())
                elements.append(Paragraph(
                    "TECHCROSS BWMS P&ID Checklist (Continued)",
                    self.styles['SectionHeader']
                ))
                elements.append(Spacer(1, 3*mm))

            end_idx = min(start_idx + rows_per_page, len(table_data) - 1)
            page_data = [table_data[0]] + table_data[start_idx + 1:end_idx + 1]

            table = Table(page_data, colWidths=[12*mm, 35*mm, 80*mm, 25*mm, 20*mm])

            # 스타일 구성
            style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]

            # 행별 배경색
            for row_idx, row in enumerate(page_data[1:], 1):
                rule_id = row[1]
                if rule_id in passed_map:
                    style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), PASS_BG))
                elif rule_id in violation_map:
                    style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), FAIL_BG))
                elif rule_id in skipped_map:
                    style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), SKIP_BG))
                else:
                    style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), LIGHT_GRAY))

            table.setStyle(TableStyle(style_commands))
            elements.append(table)

        # 요약
        elements.append(Spacer(1, 10*mm))
        summary = validation_data.get("summary", {})
        summary_text = f"Total: {summary.get('total_rules', 0)} | "
        summary_text += f"Passed: {summary.get('passed', 0)} | "
        summary_text += f"Violations: {summary.get('violations', 0)} | "
        summary_text += f"Pass Rate: {summary.get('pass_rate', 0):.1f}%"
        elements.append(Paragraph(summary_text, self.styles['ReportSubtitle']))

        # PDF 생성
        doc.build(elements)
        buffer.seek(0)

        return buffer.getvalue()


# 싱글톤 인스턴스
pdf_report_service = PDFReportService()
