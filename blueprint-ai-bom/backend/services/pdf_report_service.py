"""PDF Report Service

TECHCROSS P&ID 분석 결과 PDF 리포트 생성
"""

import logging
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

# 색상 정의
TECHCROSS_BLUE = colors.HexColor("#1E3A5F")
TECHCROSS_LIGHT_BLUE = colors.HexColor("#4472C4")
HEADER_BG = colors.HexColor("#E8EEF4")
PASS_GREEN = colors.HexColor("#28A745")
FAIL_RED = colors.HexColor("#DC3545")
WARN_YELLOW = colors.HexColor("#FFC107")
PENDING_GRAY = colors.HexColor("#6C757D")


class PDFReportService:
    """P&ID 분석 결과 PDF 리포트 생성 서비스"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """커스텀 스타일 정의"""
        # 제목 스타일
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Title'],
            fontSize=28,
            textColor=TECHCROSS_BLUE,
            alignment=TA_CENTER,
            spaceAfter=12
        ))

        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=colors.gray,
            alignment=TA_CENTER,
            spaceAfter=6
        ))

        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=TECHCROSS_BLUE,
            spaceBefore=20,
            spaceAfter=12,
            borderWidth=1,
            borderColor=TECHCROSS_LIGHT_BLUE,
            borderPadding=5
        ))

        self.styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=TECHCROSS_LIGHT_BLUE,
            spaceBefore=12,
            spaceAfter=6
        ))

        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT
        ))

        self.styles.add(ParagraphStyle(
            name='FooterStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        ))

    def generate_report(
        self,
        session_data: Dict[str, Any],
        project_name: str = "Unknown Project",
        drawing_no: str = "N/A",
        export_type: str = "all",
        include_rejected: bool = False
    ) -> BytesIO:
        """
        PDF 리포트 생성

        Args:
            session_data: 세션 데이터 (valves, equipment, checklist 등)
            project_name: 프로젝트명
            drawing_no: 도면 번호
            export_type: 내보내기 타입 (valve, equipment, checklist, all)
            include_rejected: 거부된 항목 포함 여부

        Returns:
            BytesIO: PDF 버퍼
        """
        buffer = BytesIO()

        # 가로 A4
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        # 문서 요소 수집
        elements = []

        # 1. 표지
        elements.extend(self._create_cover_page(
            project_name, drawing_no, session_data
        ))

        # 2. 요약 통계
        elements.extend(self._create_summary_section(
            session_data, export_type, include_rejected
        ))

        # 3. Equipment List
        if export_type in ["equipment", "all"]:
            equipment = session_data.get("pid_equipment", [])
            if not include_rejected:
                equipment = [e for e in equipment if e.get("verification_status") != "rejected"]
            if equipment:
                elements.append(PageBreak())
                elements.extend(self._create_equipment_section(equipment))

        # 4. Valve Signal List
        if export_type in ["valve", "all"]:
            valves = session_data.get("pid_valves", [])
            if not include_rejected:
                valves = [v for v in valves if v.get("verification_status") != "rejected"]
            if valves:
                elements.append(PageBreak())
                elements.extend(self._create_valve_section(valves))

        # 5. Design Checklist
        if export_type in ["checklist", "all"]:
            checklist = session_data.get("pid_checklist_items", [])
            if not include_rejected:
                checklist = [c for c in checklist if c.get("verification_status") != "rejected"]
            if checklist:
                elements.append(PageBreak())
                elements.extend(self._create_checklist_section(checklist))

        # 6. Deviations
        if export_type in ["deviation", "all"]:
            deviations = session_data.get("pid_deviations", [])
            if not include_rejected:
                deviations = [d for d in deviations if d.get("verification_status") != "rejected"]
            if deviations:
                elements.append(PageBreak())
                elements.extend(self._create_deviation_section(deviations))

        # PDF 생성
        doc.build(elements, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)

        buffer.seek(0)
        return buffer

    def _create_cover_page(
        self,
        project_name: str,
        drawing_no: str,
        session_data: Dict[str, Any]
    ) -> List:
        """표지 페이지 생성"""
        elements = []

        elements.append(Spacer(1, 60*mm))

        # 타이틀
        elements.append(Paragraph("P&ID Analysis Report", self.styles['CoverTitle']))
        elements.append(Spacer(1, 10*mm))

        # TECHCROSS 로고 텍스트
        elements.append(Paragraph("TECHCROSS BWMS", self.styles['CoverSubtitle']))
        elements.append(Spacer(1, 20*mm))

        # 프로젝트 정보 테이블
        info_data = [
            ["Project Name:", project_name],
            ["Drawing No.:", drawing_no],
            ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Session ID:", session_data.get("session_id", "N/A")[:8] + "..."],
        ]

        info_table = Table(info_data, colWidths=[50*mm, 100*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), TECHCROSS_BLUE),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)

        elements.append(PageBreak())
        return elements

    def _create_summary_section(
        self,
        session_data: Dict[str, Any],
        export_type: str,
        include_rejected: bool
    ) -> List:
        """요약 통계 섹션"""
        elements = []

        elements.append(Paragraph("1. Executive Summary", self.styles['SectionTitle']))

        # 통계 계산
        def count_by_status(items: List[Dict], status_key: str = "verification_status"):
            if not include_rejected:
                items = [i for i in items if i.get(status_key) != "rejected"]
            total = len(items)
            verified = len([i for i in items if i.get(status_key) == "verified"])
            pending = len([i for i in items if i.get(status_key) == "pending"])
            rejected = len([i for i in items if i.get(status_key) == "rejected"])
            return total, verified, pending, rejected

        valves = session_data.get("pid_valves", [])
        equipment = session_data.get("pid_equipment", [])
        checklist = session_data.get("pid_checklist_items", [])
        deviations = session_data.get("pid_deviations", [])

        v_total, v_verified, v_pending, v_rejected = count_by_status(valves)
        e_total, e_verified, e_pending, e_rejected = count_by_status(equipment)
        c_total, c_verified, c_pending, c_rejected = count_by_status(checklist)
        d_total, d_verified, d_pending, d_rejected = count_by_status(deviations)

        # 체크리스트 Pass/Fail 카운트
        c_pass = len([c for c in checklist if c.get("final_status") == "pass"])
        c_fail = len([c for c in checklist if c.get("final_status") == "fail"])
        c_na = len([c for c in checklist if c.get("final_status") == "N/A"])

        # 요약 테이블
        summary_data = [
            ["Category", "Total", "Verified", "Pending", "Rejected", "Status"],
            ["Equipment List", str(e_total), str(e_verified), str(e_pending), str(e_rejected),
             self._status_indicator(e_verified, e_total)],
            ["Valve Signal List", str(v_total), str(v_verified), str(v_pending), str(v_rejected),
             self._status_indicator(v_verified, v_total)],
            ["Design Checklist", str(c_total), f"Pass: {c_pass}", f"Fail: {c_fail}", f"N/A: {c_na}",
             self._checklist_status(c_pass, c_fail, c_total)],
            ["Deviations", str(d_total), str(d_verified), str(d_pending), str(d_rejected),
             self._severity_indicator(deviations)],
        ]

        summary_table = Table(summary_data, colWidths=[50*mm, 25*mm, 30*mm, 30*mm, 30*mm, 50*mm])
        summary_table.setStyle(TableStyle([
            # 헤더
            ('BACKGROUND', (0, 0), (-1, 0), TECHCROSS_LIGHT_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # 데이터
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-2, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            # 그리드
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HEADER_BG]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 10*mm))

        # 분석 결과 요약 텍스트
        total_items = e_total + v_total
        total_verified = e_verified + v_verified

        if total_items > 0:
            verification_rate = (total_verified / total_items) * 100
            elements.append(Paragraph(
                f"<b>Verification Progress:</b> {total_verified}/{total_items} items verified ({verification_rate:.1f}%)",
                self.styles['Normal']
            ))

        if c_fail > 0:
            elements.append(Paragraph(
                f"<b><font color='red'>Warning:</font></b> {c_fail} checklist items failed verification.",
                self.styles['Normal']
            ))

        return elements

    def _status_indicator(self, verified: int, total: int) -> str:
        """검증 상태 표시"""
        if total == 0:
            return "No Data"
        rate = verified / total
        if rate >= 1.0:
            return "Complete"
        elif rate >= 0.8:
            return f"{rate*100:.0f}% Done"
        else:
            return f"{rate*100:.0f}% Pending"

    def _checklist_status(self, passed: int, failed: int, total: int) -> str:
        """체크리스트 상태"""
        if total == 0:
            return "No Data"
        if failed > 0:
            return f"FAIL ({failed} issues)"
        elif passed == total:
            return "ALL PASS"
        else:
            return f"In Progress"

    def _severity_indicator(self, deviations: List[Dict]) -> str:
        """편차 심각도 표시"""
        if not deviations:
            return "None"
        critical = len([d for d in deviations if d.get("severity") == "critical"])
        major = len([d for d in deviations if d.get("severity") == "major"])
        if critical > 0:
            return f"CRITICAL: {critical}"
        elif major > 0:
            return f"Major: {major}"
        return "Minor Only"

    def _create_equipment_section(self, equipment: List[Dict]) -> List:
        """Equipment List 섹션"""
        elements = []

        elements.append(Paragraph("2. Equipment List", self.styles['SectionTitle']))
        elements.append(Paragraph(
            f"Total: {len(equipment)} items detected",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 5*mm))

        # 테이블 데이터
        table_data = [["No", "Tag", "Type", "Description", "Vendor Supply", "Confidence", "Status", "Notes"]]

        for idx, e in enumerate(equipment, 1):
            table_data.append([
                str(idx),
                e.get("tag", ""),
                e.get("equipment_type", "")[:20],
                self._truncate(e.get("description", ""), 30),
                "Yes" if e.get("vendor_supply") else "No",
                f"{e.get('confidence', 0):.2f}",
                self._format_status(e.get("verification_status", "")),
                self._truncate(e.get("notes", ""), 25)
            ])

        table = Table(table_data, colWidths=[12*mm, 30*mm, 35*mm, 55*mm, 22*mm, 22*mm, 22*mm, 50*mm])
        table.setStyle(self._get_table_style())
        elements.append(table)

        return elements

    def _create_valve_section(self, valves: List[Dict]) -> List:
        """Valve Signal List 섹션"""
        elements = []

        elements.append(Paragraph("3. Valve Signal List", self.styles['SectionTitle']))
        elements.append(Paragraph(
            f"Total: {len(valves)} valves detected",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 5*mm))

        # 밸브 유형별 그룹핑
        by_type = {}
        for v in valves:
            vtype = v.get("valve_type", "Unknown")
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(v)

        elements.append(Paragraph(
            f"Types: {', '.join(f'{k} ({len(v)})' for k, v in by_type.items())}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 3*mm))

        # 테이블 데이터
        table_data = [["No", "Valve ID", "Type", "Category", "Region", "Confidence", "Status", "Notes"]]

        for idx, v in enumerate(valves, 1):
            table_data.append([
                str(idx),
                v.get("valve_id", ""),
                v.get("valve_type", ""),
                v.get("category", ""),
                self._truncate(v.get("region_name", ""), 20),
                f"{v.get('confidence', 0):.2f}",
                self._format_status(v.get("verification_status", "")),
                self._truncate(v.get("notes", ""), 25)
            ])

        table = Table(table_data, colWidths=[12*mm, 35*mm, 30*mm, 30*mm, 40*mm, 22*mm, 22*mm, 50*mm])
        table.setStyle(self._get_table_style())
        elements.append(table)

        return elements

    def _create_checklist_section(self, checklist: List[Dict]) -> List:
        """Design Checklist 섹션"""
        elements = []

        elements.append(Paragraph("4. Design Checklist", self.styles['SectionTitle']))

        # 통계
        passed = len([c for c in checklist if c.get("final_status") == "pass"])
        failed = len([c for c in checklist if c.get("final_status") == "fail"])
        na = len([c for c in checklist if c.get("final_status") == "N/A"])

        elements.append(Paragraph(
            f"Total: {len(checklist)} items | Pass: {passed} | Fail: {failed} | N/A: {na}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 5*mm))

        # 테이블 데이터
        table_data = [["No", "Category", "Description", "Auto", "Final", "Evidence", "Notes"]]

        for c in checklist:
            final_status = c.get("final_status", "")
            status_color = ""
            if final_status == "pass":
                status_color = "PASS"
            elif final_status == "fail":
                status_color = "FAIL"
            else:
                status_color = final_status

            table_data.append([
                c.get("item_no", ""),
                c.get("category", "")[:15],
                self._truncate(c.get("description", ""), 50),
                c.get("auto_status", ""),
                status_color,
                self._truncate(c.get("evidence", ""), 30),
                self._truncate(c.get("reviewer_notes", ""), 25)
            ])

        table = Table(table_data, colWidths=[15*mm, 30*mm, 80*mm, 20*mm, 20*mm, 50*mm, 45*mm])
        table.setStyle(self._get_checklist_table_style(checklist))
        elements.append(table)

        return elements

    def _create_deviation_section(self, deviations: List[Dict]) -> List:
        """Deviation List 섹션"""
        elements = []

        elements.append(Paragraph("5. Deviation List", self.styles['SectionTitle']))

        # 심각도별 통계
        critical = len([d for d in deviations if d.get("severity") == "critical"])
        major = len([d for d in deviations if d.get("severity") == "major"])
        minor = len([d for d in deviations if d.get("severity") == "minor"])

        elements.append(Paragraph(
            f"Total: {len(deviations)} | Critical: {critical} | Major: {major} | Minor: {minor}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 5*mm))

        # 테이블 데이터
        table_data = [["No", "Severity", "Category", "Title", "Location", "Action Required", "Status"]]

        for idx, d in enumerate(deviations, 1):
            severity = d.get("severity", "")
            table_data.append([
                str(idx),
                severity.upper() if severity else "",
                d.get("category", ""),
                self._truncate(d.get("title", ""), 35),
                self._truncate(d.get("location", ""), 25),
                self._truncate(d.get("action_required", ""), 40),
                self._format_status(d.get("verification_status", ""))
            ])

        table = Table(table_data, colWidths=[12*mm, 22*mm, 30*mm, 55*mm, 40*mm, 65*mm, 25*mm])
        table.setStyle(self._get_deviation_table_style(deviations))
        elements.append(table)

        return elements

    def _get_table_style(self) -> TableStyle:
        """기본 테이블 스타일"""
        return TableStyle([
            # 헤더
            ('BACKGROUND', (0, 0), (-1, 0), TECHCROSS_LIGHT_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # 데이터
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # No
            ('ALIGN', (5, 1), (6, -1), 'CENTER'),  # Confidence, Status
            # 그리드
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HEADER_BG]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])

    def _get_checklist_table_style(self, checklist: List[Dict]) -> TableStyle:
        """체크리스트 테이블 스타일 (상태별 색상)"""
        style = self._get_table_style()

        # Pass/Fail 색상 적용
        for idx, c in enumerate(checklist, 1):
            final_status = c.get("final_status", "")
            if final_status == "pass":
                style.add('TEXTCOLOR', (4, idx), (4, idx), PASS_GREEN)
                style.add('FONTNAME', (4, idx), (4, idx), 'Helvetica-Bold')
            elif final_status == "fail":
                style.add('TEXTCOLOR', (4, idx), (4, idx), FAIL_RED)
                style.add('FONTNAME', (4, idx), (4, idx), 'Helvetica-Bold')
                style.add('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#FFF0F0"))

        return style

    def _get_deviation_table_style(self, deviations: List[Dict]) -> TableStyle:
        """편차 테이블 스타일 (심각도별 색상)"""
        style = self._get_table_style()

        # Severity 색상 적용
        for idx, d in enumerate(deviations, 1):
            severity = d.get("severity", "")
            if severity == "critical":
                style.add('TEXTCOLOR', (1, idx), (1, idx), FAIL_RED)
                style.add('FONTNAME', (1, idx), (1, idx), 'Helvetica-Bold')
                style.add('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#FFF0F0"))
            elif severity == "major":
                style.add('TEXTCOLOR', (1, idx), (1, idx), WARN_YELLOW)
                style.add('FONTNAME', (1, idx), (1, idx), 'Helvetica-Bold')

        return style

    def _format_status(self, status: str) -> str:
        """상태 포맷팅"""
        status_map = {
            "verified": "Verified",
            "pending": "Pending",
            "rejected": "Rejected",
            "auto_verified": "Auto"
        }
        return status_map.get(status, status)

    def _truncate(self, text: str, max_len: int) -> str:
        """텍스트 잘라내기"""
        if not text:
            return ""
        if len(text) > max_len:
            return text[:max_len-3] + "..."
        return text

    def _add_header_footer(self, canvas, doc):
        """헤더/푸터 추가"""
        canvas.saveState()

        # 헤더
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(15*mm, doc.height + 30*mm, "TECHCROSS BWMS P&ID Analysis Report")
        canvas.drawRightString(doc.width + 15*mm, doc.height + 30*mm,
                               datetime.now().strftime("%Y-%m-%d"))

        # 푸터
        canvas.drawCentredString(doc.width/2 + 15*mm, 10*mm,
                                 f"Page {doc.page}")
        canvas.drawRightString(doc.width + 15*mm, 10*mm,
                               "Generated by Blueprint AI BOM")

        canvas.restoreState()


# 싱글톤 인스턴스
_pdf_service: Optional[PDFReportService] = None


def get_pdf_report_service() -> PDFReportService:
    """PDF 서비스 인스턴스 반환"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFReportService()
    return _pdf_service
