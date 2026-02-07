"""Quotation Service - 견적 집계 서비스

Phase 3: 프로젝트 내 모든 세션 BOM → 재질별 그룹 집계 → PDF/Excel 견적서 내보내기
Phase 4: 원가 계산 엔진 통합 (치수 → 여유치 → 중량 → 단가 → 가공비)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import defaultdict

from schemas.quotation import (
    SessionQuotationItem,
    MaterialGroup,
    AssemblyQuotationGroup,
    QuotationSummary,
    ProjectQuotationResponse,
    QuotationExportFormat,
    QuotationExportResponse,
)
from schemas.pricing_config import PricingConfig, DEFAULT_PRICING_CONFIG
from services.cost_calculator import calculate_item_cost
from services.quotation_pdf_exporter import export_pdf, export_assembly_pdf
from services.quotation_excel_exporter import export_excel, export_assembly_excel

logger = logging.getLogger(__name__)


class QuotationService:
    """견적 집계 서비스"""

    def __init__(self, data_dir: Path, output_dir: Path):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def aggregate_quotation(
        self,
        project_id: str,
        project_service,
        session_service,
    ) -> ProjectQuotationResponse:
        """프로젝트 견적 집계

        1. 프로젝트 정보 조회
        2. 단가 설정 로드
        3. 세션 목록 조회
        4. 각 세션에서 견적 항목 구성 (원가 계산 포함)
        5. ASSY 합산
        6. 재질별 그룹핑
        7. 요약 계산
        8. quotation.json 저장
        """
        # 1. 프로젝트 정보
        project = project_service.get_project(project_id)
        if not project:
            raise ValueError(f"프로젝트를 찾을 수 없습니다: {project_id}")

        # 2. 단가 설정 로드
        pricing_config = self._load_pricing_config(project_id, project_service)

        # 3. 세션 목록
        sessions = session_service.list_sessions_by_project(project_id)

        # 4. 각 세션에서 견적 항목 구성 (원가 계산 포함)
        items: List[SessionQuotationItem] = []
        for session in sessions:
            item = self._build_session_item(session, pricing_config)
            items.append(item)

        # 5. ASSY 합산 (BOM 계층 기반)
        items = self._apply_assembly_rollup(items, project_id, project_service)

        # 6. 재질별 그룹핑
        material_groups = self._group_by_material(items)

        # 7. 요약 계산
        summary = self._calculate_summary(items, len(sessions))

        # 8. 어셈블리 단위 그룹핑
        assembly_groups = self._build_assembly_groups(
            items, project_id, project_service
        )

        # 9. 응답 구성
        response = ProjectQuotationResponse(
            project_id=project_id,
            project_name=project.get("name", ""),
            customer=project.get("customer", ""),
            created_at=project.get("created_at", datetime.now().isoformat()),
            summary=summary,
            items=items,
            material_groups=material_groups,
            assembly_groups=assembly_groups,
        )

        # 10. quotation.json 저장 + 프로젝트 통계 갱신
        self._save_quotation(project_id, response, project_service)

        return response

    def _build_session_item(
        self,
        session: Dict[str, Any],
        pricing_config: Optional[PricingConfig] = None,
    ) -> SessionQuotationItem:
        """세션 → SessionQuotationItem 변환 (원가 계산 포함)"""
        metadata = session.get("metadata") or {}
        bom_data = session.get("bom_data") or {}
        bom_summary = bom_data.get("summary") or {}

        # 어셈블리 귀속 정보 (assembly_refs에서 첫 번째)
        assembly_refs = metadata.get("assembly_refs") or []
        primary_assy = assembly_refs[0]["assembly"] if assembly_refs else None

        # 기본 필드
        item = SessionQuotationItem(
            session_id=session.get("session_id", ""),
            drawing_number=metadata.get("drawing_number", ""),
            bom_item_no=metadata.get("bom_item_no", ""),
            description=metadata.get("bom_description", ""),
            material=metadata.get("material", ""),
            bom_quantity=metadata.get("bom_quantity", 1),
            quote_status=metadata.get("quote_status", "pending"),
            bom_item_count=len(bom_data.get("items", [])),
            subtotal=bom_summary.get("subtotal", 0.0),
            vat=bom_summary.get("vat", 0.0),
            total=bom_summary.get("total", 0.0),
            session_status=session.get("status", "uploaded"),
            bom_generated=session.get("bom_generated", False),
            # 어셈블리 귀속 및 개정
            assembly_drawing_number=primary_assy,
            doc_revision=metadata.get("doc_revision"),
            bom_revision=metadata.get("bom_revision"),
            part_no=metadata.get("part_no"),
            size=metadata.get("size"),
            remark=metadata.get("remark"),
        )

        # Phase 4: 원가 계산
        if pricing_config:
            session_features = session.get("features")  # None if not set → backward compat
            breakdown = calculate_item_cost(session, pricing_config, features=session_features)
            item.material_cost = breakdown.material_cost
            item.machining_cost = breakdown.machining_cost
            item.treatment_cost = breakdown.treatment_cost
            item.scrap_cost = breakdown.scrap_cost
            item.setup_cost = breakdown.setup_cost
            item.inspection_cost = breakdown.inspection_cost
            item.transport_cost = breakdown.transport_cost
            item.weight_kg = breakdown.weight_kg
            item.difficulty_factor = breakdown.difficulty_factor
            item.treatments = breakdown.treatments
            item.quantity_discount = breakdown.quantity_discount
            item.raw_dimensions = breakdown.raw_dimensions
            item.original_dimensions = breakdown.original_dimensions
            item.allowance_applied = breakdown.allowance_applied
            item.cost_source = breakdown.cost_source
            # 원가 계산 결과가 있으면 항상 소계 오버라이드
            # (BOM 심볼 카운팅 합계 대신 재료비+가공비 사용)
            if breakdown.subtotal > 0:
                item.subtotal = breakdown.subtotal
                item.vat = breakdown.subtotal * (pricing_config.tax_rate / 100.0)
                item.total = item.subtotal + item.vat

        return item

    def _group_by_material(
        self, items: List[SessionQuotationItem]
    ) -> List[MaterialGroup]:
        """재질별 defaultdict 그룹핑"""
        groups: Dict[str, List[SessionQuotationItem]] = defaultdict(list)

        for item in items:
            material = item.material or "미지정"
            groups[material].append(item)

        result = []
        for material, group_items in sorted(groups.items()):
            result.append(MaterialGroup(
                material=material,
                item_count=len(group_items),
                total_quantity=sum(i.bom_quantity for i in group_items),
                subtotal=sum(i.subtotal for i in group_items),
                total_weight=sum(i.weight_kg for i in group_items),
                material_cost_sum=sum(i.material_cost for i in group_items),
                items=group_items,
            ))

        return result

    def _calculate_summary(
        self, items: List[SessionQuotationItem], total_sessions: int
    ) -> QuotationSummary:
        """합계/진행률 계산"""
        completed = sum(1 for i in items if i.bom_generated)
        pending = total_sessions - completed
        quoted = sum(1 for i in items if i.quote_status == "quoted")
        subtotal = sum(i.subtotal for i in items)
        vat = subtotal * 0.1
        total = subtotal + vat
        progress = (completed / total_sessions * 100) if total_sessions > 0 else 0.0

        return QuotationSummary(
            total_sessions=total_sessions,
            completed_sessions=completed,
            pending_sessions=pending,
            quoted_sessions=quoted,
            total_items=len(items),
            subtotal=subtotal,
            vat=vat,
            total=total,
            progress_percent=round(progress, 1),
        )

    def _load_pricing_config(
        self, project_id: str, project_service
    ) -> PricingConfig:
        """프로젝트 pricing_config.json 로드 (없으면 기본값)"""
        project_dir = project_service.projects_dir / project_id
        config_file = project_dir / "pricing_config.json"

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = PricingConfig(**data)
                logger.info(f"단가 설정 로드: {project_id} → {config_file}")
                return config
            except Exception as e:
                logger.warning(f"단가 설정 로드 실패, 기본값 사용: {e}")

        return DEFAULT_PRICING_CONFIG

    def _apply_assembly_rollup(
        self,
        items: List[SessionQuotationItem],
        project_id: str,
        project_service,
    ) -> List[SessionQuotationItem]:
        """BOM 계층에서 ASSY/SUB 총합 = 하위 PART 견적 합산

        bom_items.json → parent_item_no 관계로 트리 구성
        WHITE(part) 견적 합산 → 상위 BLUE(sub) → 상위 PINK(assy) 전파
        """
        from services.bom_pdf_parser import BOMPDFParser

        project_dir = project_service.projects_dir / project_id
        parser = BOMPDFParser()
        bom_data = parser.load_bom_items(project_dir)

        if not bom_data:
            return items

        # bom_items.json이 리스트(직접 아이템 배열)이거나 dict({"items": [...]}) 형태 모두 지원
        if isinstance(bom_data, list):
            bom_items = bom_data
        elif isinstance(bom_data, dict) and bom_data.get("items"):
            bom_items = bom_data["items"]
        else:
            return items

        # session_id → item 맵
        session_item_map = {i.session_id: i for i in items if i.session_id}

        # item_no → bom_item 맵
        bom_map = {bi.get("item_no"): bi for bi in bom_items}

        # item_no → session_id 맵 (bom_items에서)
        item_session_map = {}
        for bi in bom_items:
            sid = bi.get("session_id")
            if sid:
                item_session_map[bi.get("item_no")] = sid

        # 하위 → 상위 합산: parent_item_no 기반
        # 각 parent의 하위 part 소계 합산
        parent_subtotals: Dict[str, float] = defaultdict(float)
        parent_material_costs: Dict[str, float] = defaultdict(float)
        parent_machining_costs: Dict[str, float] = defaultdict(float)
        parent_weights: Dict[str, float] = defaultdict(float)

        for bi in bom_items:
            parent_no = bi.get("parent_item_no")
            session_id = bi.get("session_id")
            if parent_no and session_id and session_id in session_item_map:
                child = session_item_map[session_id]
                parent_subtotals[parent_no] += child.subtotal
                parent_material_costs[parent_no] += child.material_cost
                parent_machining_costs[parent_no] += child.machining_cost
                parent_weights[parent_no] += child.weight_kg

        # 상위 항목에 합산 반영 (ASSY/SUB 세션이 있는 경우)
        for item_no, session_id in item_session_map.items():
            if item_no in parent_subtotals and session_id in session_item_map:
                parent_item = session_item_map[session_id]
                bom_entry = bom_map.get(item_no, {})
                level = bom_entry.get("level", "")
                if level in ("assembly", "subassembly"):
                    # ASSY/SUB의 소계 = 자체 + 하위 합산
                    parent_item.subtotal += parent_subtotals[item_no]
                    parent_item.material_cost += parent_material_costs[item_no]
                    parent_item.machining_cost += parent_machining_costs[item_no]
                    parent_item.weight_kg += parent_weights[item_no]
                    parent_item.vat = parent_item.subtotal * 0.1
                    parent_item.total = parent_item.subtotal + parent_item.vat

        return items

    def _build_assembly_groups(
        self,
        items: List[SessionQuotationItem],
        project_id: str,
        project_service,
    ) -> List[AssemblyQuotationGroup]:
        """어셈블리 단위로 견적 항목 그룹핑

        각 SessionQuotationItem의 assembly_drawing_number로 그룹핑하고,
        bom_items.json에서 어셈블리 품명/중량 정보를 로드합니다.
        기존 세션에 assembly_drawing_number가 없으면 bom_items.json에서 룩업합니다.
        """
        from services.bom_pdf_parser import BOMPDFParser

        # bom_items.json 로드
        project_dir = project_service.projects_dir / project_id
        parser = BOMPDFParser()
        bom_data = parser.load_bom_items(project_dir)

        bom_items_list: list = []
        assy_info: Dict[str, Dict[str, Any]] = {}
        dwg_to_assy: Dict[str, str] = {}

        if bom_data:
            bom_items_list = (
                bom_data if isinstance(bom_data, list)
                else bom_data.get("items", [])
            )
            for bi in bom_items_list:
                if bi.get("level") == "assembly":
                    dwg = bi.get("drawing_number", "")
                    if dwg:
                        assy_info[dwg] = {
                            "description": bi.get("description", ""),
                            "weight_kg": bi.get("weight_kg", 0.0) or 0.0,
                        }
                # drawing_number → assembly_drawing_number 룩업 맵
                adwg = bi.get("assembly_drawing_number")
                ddwg = bi.get("drawing_number", "")
                if adwg and ddwg and ddwg not in dwg_to_assy:
                    dwg_to_assy[ddwg] = adwg

        # 기존 세션에 assembly_drawing_number가 없으면 bom에서 룩업
        for item in items:
            if not item.assembly_drawing_number and item.drawing_number:
                assy_dwg = dwg_to_assy.get(item.drawing_number)
                if assy_dwg:
                    item.assembly_drawing_number = assy_dwg

        # 어셈블리별 아이템 수집
        assy_map: Dict[str, List[SessionQuotationItem]] = defaultdict(list)
        for item in items:
            if item.assembly_drawing_number:
                assy_map[item.assembly_drawing_number].append(item)

        if not assy_map:
            return []

        # 그룹 생성
        groups = []
        for assy_dwg, group_items in sorted(assy_map.items()):
            info = assy_info.get(assy_dwg, {})
            quoted = sum(1 for i in group_items if i.quote_status == "quoted")
            total_parts = len(group_items)
            subtotal = sum(i.subtotal for i in group_items)
            vat = subtotal * 0.1
            progress = (quoted / total_parts * 100) if total_parts > 0 else 0.0

            groups.append(AssemblyQuotationGroup(
                assembly_drawing_number=assy_dwg,
                assembly_description=info.get("description", ""),
                bom_weight_kg=info.get("weight_kg", 0.0),
                total_parts=total_parts,
                quoted_parts=quoted,
                progress_percent=round(progress, 1),
                subtotal=subtotal,
                vat=vat,
                total=subtotal + vat,
                items=group_items,
            ))

        return groups

    def _save_quotation(
        self,
        project_id: str,
        data: ProjectQuotationResponse,
        project_service,
    ):
        """quotation.json 저장, project 통계 갱신"""
        project_dir = project_service.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        quotation_file = project_dir / "quotation.json"
        with open(quotation_file, "w", encoding="utf-8") as f:
            json.dump(data.model_dump(), f, ensure_ascii=False, indent=2, default=str)

        # 프로젝트 통계 업데이트
        project = project_service.get_project(project_id)
        if project:
            project["quoted_count"] = data.summary.quoted_sessions
            project["total_quotation"] = data.summary.total
            project["updated_at"] = datetime.now().isoformat()
            project_service._save_project(project_id)

        logger.info(f"견적 집계 저장: {project_id} → {quotation_file}")

    def _load_quotation(
        self, project_id: str, project_service
    ) -> Optional[ProjectQuotationResponse]:
        """캐시된 quotation.json 로드"""
        project_dir = project_service.projects_dir / project_id
        quotation_file = project_dir / "quotation.json"

        if not quotation_file.exists():
            return None

        try:
            with open(quotation_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ProjectQuotationResponse(**data)
        except Exception as e:
            logger.error(f"견적 데이터 로드 실패: {e}")
            return None

    # --- Export methods: delegate to extracted modules ---

    def export_pdf(
        self,
        quotation_data: ProjectQuotationResponse,
        customer_name: Optional[str] = None,
        include_material_breakdown: bool = True,
        notes: Optional[str] = None,
    ) -> Path:
        """reportlab 기반 견적서 PDF"""
        return export_pdf(
            quotation_data, self.output_dir,
            customer_name, include_material_breakdown, notes,
        )

    def export_excel(
        self,
        quotation_data: ProjectQuotationResponse,
        customer_name: Optional[str] = None,
        include_material_breakdown: bool = True,
        notes: Optional[str] = None,
    ) -> Path:
        """openpyxl 기반 견적서 Excel"""
        return export_excel(
            quotation_data, self.output_dir,
            customer_name, include_material_breakdown, notes,
        )

    def export_assembly_pdf(
        self,
        quotation_data: ProjectQuotationResponse,
        assembly_drawing_number: str,
        customer_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Path:
        """특정 어셈블리만 포함한 PDF 견적서"""
        return export_assembly_pdf(
            quotation_data, assembly_drawing_number, self.output_dir,
            customer_name, notes,
        )

    def export_assembly_excel(
        self,
        quotation_data: ProjectQuotationResponse,
        assembly_drawing_number: str,
        customer_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Path:
        """특정 어셈블리만 포함한 Excel 견적서"""
        return export_assembly_excel(
            quotation_data, assembly_drawing_number, self.output_dir,
            customer_name, notes,
        )

    def export_assembly(
        self,
        quotation_data: ProjectQuotationResponse,
        assembly_drawing_number: str,
        format: QuotationExportFormat,
        customer_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> QuotationExportResponse:
        """어셈블리 단위 견적서 내보내기"""
        if format == QuotationExportFormat.PDF:
            path = self.export_assembly_pdf(
                quotation_data, assembly_drawing_number, customer_name, notes
            )
        elif format == QuotationExportFormat.EXCEL:
            path = self.export_assembly_excel(
                quotation_data, assembly_drawing_number, customer_name, notes
            )
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")

        file_size = path.stat().st_size

        return QuotationExportResponse(
            project_id=quotation_data.project_id,
            format=format,
            filename=path.name,
            file_path=str(path),
            file_size=file_size,
            created_at=datetime.now().isoformat(),
        )

    def export(
        self,
        quotation_data: ProjectQuotationResponse,
        format: QuotationExportFormat,
        customer_name: Optional[str] = None,
        include_material_breakdown: bool = True,
        notes: Optional[str] = None,
    ) -> QuotationExportResponse:
        """format 디스패치"""
        if format == QuotationExportFormat.PDF:
            path = self.export_pdf(
                quotation_data, customer_name, include_material_breakdown, notes
            )
        elif format == QuotationExportFormat.EXCEL:
            path = self.export_excel(
                quotation_data, customer_name, include_material_breakdown, notes
            )
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")

        file_size = path.stat().st_size

        return QuotationExportResponse(
            project_id=quotation_data.project_id,
            format=format,
            filename=path.name,
            file_path=str(path),
            file_size=file_size,
            created_at=datetime.now().isoformat(),
        )


# 싱글톤 인스턴스
_quotation_service: Optional[QuotationService] = None


def get_quotation_service(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> QuotationService:
    """QuotationService 싱글톤 인스턴스 반환"""
    global _quotation_service

    if _quotation_service is None:
        if data_dir is None:
            data_dir = Path("/app/data")
        if output_dir is None:
            output_dir = Path("/app/data/exports")
        _quotation_service = QuotationService(data_dir, output_dir)

    return _quotation_service
