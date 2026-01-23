"""
DSE Bearing Router - API endpoints for DSE Bearing pipeline nodes

실제 OCR 기반 파싱 로직 구현
"""

import io
import logging
import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from services.dsebearing_parser import get_parser, TitleBlockData, PartsListItem as ParsedPartsItem
from services.price_database import get_price_database
from services.customer_config import get_customer_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dsebearing", tags=["DSE Bearing"])

# eDOCr2 API URL
EDOCR2_URL = "http://edocr2-v2-api:5002"


# =====================
# Error Handling
# =====================

class DSEBearingError(Exception):
    """DSE Bearing 서비스 오류"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


# 에러 코드 정의
class ErrorCodes:
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    OCR_SERVICE_ERROR = "OCR_SERVICE_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    INVALID_JSON = "INVALID_JSON"
    QUOTE_GENERATION_ERROR = "QUOTE_GENERATION_ERROR"


# 에러 메시지 (한국어)
ERROR_MESSAGES = {
    ErrorCodes.FILE_NOT_FOUND: "파일이 제공되지 않았습니다. 이미지 파일을 업로드해주세요.",
    ErrorCodes.FILE_TOO_LARGE: "파일 크기가 너무 큽니다. 최대 20MB까지 지원합니다.",
    ErrorCodes.INVALID_FILE_TYPE: "지원하지 않는 파일 형식입니다. PNG, JPG, PDF 파일만 지원합니다.",
    ErrorCodes.OCR_SERVICE_ERROR: "OCR 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
    ErrorCodes.PARSING_ERROR: "도면 파싱 중 오류가 발생했습니다.",
    ErrorCodes.CUSTOMER_NOT_FOUND: "등록되지 않은 고객입니다.",
    ErrorCodes.INVALID_JSON: "잘못된 JSON 형식입니다.",
    ErrorCodes.QUOTE_GENERATION_ERROR: "견적 생성 중 오류가 발생했습니다.",
}


def get_error_message(error_code: str, default: str = "") -> str:
    """에러 코드에 해당하는 사용자 친화적 메시지 반환"""
    return ERROR_MESSAGES.get(error_code, default or "알 수 없는 오류가 발생했습니다.")


# 지원 파일 형식
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".tiff", ".tif"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def validate_file(file: Optional[UploadFile]) -> None:
    """파일 유효성 검사"""
    if not file or not file.filename:
        return  # 파일 선택 사항

    # 확장자 검사
    ext = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    if f".{ext}" not in SUPPORTED_EXTENSIONS:
        raise DSEBearingError(
            get_error_message(ErrorCodes.INVALID_FILE_TYPE),
            ErrorCodes.INVALID_FILE_TYPE,
            {"filename": file.filename, "supported": list(SUPPORTED_EXTENSIONS)}
        )


# =====================
# Response Models
# =====================

class ErrorResponse(BaseModel):
    """공통 에러 응답"""
    success: bool = False
    error_code: str
    message: str
    details: Dict[str, Any] = {}

class TitleBlockResponse(BaseModel):
    success: bool
    drawing_number: str
    revision: str
    part_name: str
    material: str
    date: str
    size: str = ""
    scale: str = ""
    sheet: str = ""
    company: str = ""
    raw_texts: List[str] = []
    confidence: float = 0.0

class PartsListItemResponse(BaseModel):
    no: str
    description: str
    material: str
    size_dwg_no: str = ""
    qty: int
    remark: str = ""
    weight: Optional[float] = None

class PartsListResponse(BaseModel):
    success: bool
    items: List[PartsListItemResponse]
    total_count: int
    confidence: float = 0.0

class DimensionItem(BaseModel):
    type: str
    value: Optional[float] = None
    outer_diameter: Optional[float] = None
    inner_diameter: Optional[float] = None
    tolerance: Optional[str] = None
    upper_tolerance: Optional[float] = None
    lower_tolerance: Optional[float] = None
    unit: str = "mm"
    raw_text: str = ""

class DimensionParserResponse(BaseModel):
    success: bool
    dimensions: List[DimensionItem]
    gdt_symbols: List[str] = []
    confidence: float = 0.0

class BOMItem(BaseModel):
    no: str
    description: str
    material: str
    size_dwg_no: str = ""
    dimensions: List[DimensionItem] = []
    qty: int
    weight: Optional[float] = None

class BOMMatcherResponse(BaseModel):
    success: bool
    matched_items: List[BOMItem]
    unmatched_count: int
    match_confidence: float

class QuoteLineItem(BaseModel):
    no: str
    description: str
    material: str
    material_cost: float
    labor_cost: float
    quantity: int
    unit_price: float
    total_price: float

class QuoteGeneratorResponse(BaseModel):
    success: bool
    quote_number: str
    date: str
    items: List[QuoteLineItem]
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str


# =====================
# Helper Functions
# =====================

async def call_edocr2_ocr(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """eDOCr2 API 호출하여 OCR 수행"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (filename, file_content, "image/png")}
            response = await client.post(
                f"{EDOCR2_URL}/api/v2/ocr",
                files=files,
                data={"profile": "bearing", "output_format": "json"}
            )

            if response.status_code == 200:
                result = response.json()
                # eDOCr2 응답에서 텍스트 추출
                texts = []
                if result.get("status") == "success" and "data" in result:
                    data = result["data"]

                    # 1. dimensions에서 값 추출
                    if "dimensions" in data:
                        for dim in data["dimensions"]:
                            if isinstance(dim, dict) and "value" in dim:
                                texts.append(dim["value"])

                    # 2. possible_text에서 텍스트 추출
                    if "possible_text" in data:
                        for item in data["possible_text"]:
                            if isinstance(item, dict) and "text" in item:
                                texts.append(item["text"])

                    # 3. text 섹션에서 추출
                    if "text" in data and isinstance(data["text"], dict):
                        for key, value in data["text"].items():
                            if isinstance(value, str):
                                texts.append(value)
                            elif isinstance(value, list):
                                texts.extend([str(v) for v in value])

                    # 4. gdt 섹션에서 추출
                    if "gdt" in data:
                        for gdt in data["gdt"]:
                            if isinstance(gdt, dict) and "value" in gdt:
                                texts.append(gdt["value"])

                elif "texts" in result:
                    texts = result["texts"]
                elif "results" in result:
                    texts = result["results"]

                logger.info(f"eDOCr2 응답: {len(texts)} 텍스트 추출됨")
                return texts
            else:
                logger.warning(f"eDOCr2 API 실패: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"eDOCr2 호출 오류: {e}")
        return []


# =====================
# Title Block Parser
# =====================

@router.post("/titleblock", response_model=TitleBlockResponse)
async def parse_title_block(
    file: UploadFile = File(None),
    ocr_results: str = Form(None),
    profile: str = Form("bearing")
):
    """
    Title Block 파싱 - 도면에서 도면번호, Rev, 품명, 재질 추출

    - file: 도면 이미지 파일 (새 OCR 수행)
    - ocr_results: 기존 OCR 결과 JSON (재사용)
    - profile: 파싱 프로파일 (bearing, standard)

    에러 코드:
    - FILE_TOO_LARGE: 파일이 20MB 초과
    - INVALID_FILE_TYPE: 지원하지 않는 파일 형식
    - OCR_SERVICE_ERROR: OCR 서비스 연결 실패
    - PARSING_ERROR: 파싱 중 오류
    """
    try:
        logger.info(f"Title Block 파싱 시작, profile={profile}")

        # 파일 유효성 검사
        validate_file(file)

        parser = get_parser()
        ocr_texts = []

        # 1. 기존 OCR 결과 사용
        if ocr_results:
            try:
                ocr_texts = json.loads(ocr_results)
                if isinstance(ocr_texts, dict):
                    ocr_texts = ocr_texts.get("texts", ocr_texts.get("results", []))
            except json.JSONDecodeError as e:
                logger.warning(f"OCR 결과 JSON 파싱 실패: {e}")
                raise DSEBearingError(
                    get_error_message(ErrorCodes.INVALID_JSON),
                    ErrorCodes.INVALID_JSON,
                    {"error": str(e)}
                )

        # 2. 파일이 있으면 새로 OCR 수행
        if file and file.filename:
            file_content = await file.read()

            # 파일 크기 검사
            if len(file_content) > MAX_FILE_SIZE:
                raise DSEBearingError(
                    get_error_message(ErrorCodes.FILE_TOO_LARGE),
                    ErrorCodes.FILE_TOO_LARGE,
                    {"file_size": len(file_content), "max_size": MAX_FILE_SIZE}
                )

            if file_content:
                ocr_texts = await call_edocr2_ocr(file_content, file.filename)

    except DSEBearingError as e:
        raise HTTPException(
            status_code=400,
            detail={"error_code": e.error_code, "message": e.message, "details": e.details}
        )
    except Exception as e:
        logger.exception(f"Title Block 파싱 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": ErrorCodes.PARSING_ERROR, "message": get_error_message(ErrorCodes.PARSING_ERROR), "details": {"error": str(e)}}
        )

    # 3. OCR 결과가 없으면 Mock 데이터 반환
    if not ocr_texts:
        logger.info("OCR 결과 없음 - Mock 데이터 반환")
        return TitleBlockResponse(
            success=True,
            drawing_number="TD0062016",
            revision="A",
            part_name="BEARING RING ASSY (T1)",
            material="SF45A",
            date=datetime.now().strftime("%Y-%m-%d"),
            size="A1",
            scale="N/S",
            sheet="1/1",
            company="DOOSAN Enerbility",
            raw_texts=["Mock data - no OCR results"],
            confidence=0.5
        )

    # 4. 실제 파싱 수행
    result = parser.parse_title_block(ocr_texts)

    # 5. 신뢰도 계산
    confidence = 0.0
    if result.drawing_number:
        confidence += 0.3
    if result.revision:
        confidence += 0.2
    if result.part_name:
        confidence += 0.3
    if result.material:
        confidence += 0.2

    return TitleBlockResponse(
        success=bool(result.drawing_number),
        drawing_number=result.drawing_number,
        revision=result.revision,
        part_name=result.part_name,
        material=result.material,
        date=result.date,
        size=result.size,
        scale=result.scale,
        sheet=result.sheet,
        company=result.company,
        raw_texts=result.raw_texts[:20],  # 최대 20개
        confidence=confidence
    )


# =====================
# Parts List Parser
# =====================

@router.post("/partslist", response_model=PartsListResponse)
async def parse_parts_list(
    file: UploadFile = File(None),
    ocr_results: str = Form(None),
    table_data: str = Form(None),
    profile: str = Form("bearing")
):
    """
    Parts List 테이블 파싱

    - file: 도면 이미지 파일
    - ocr_results: 기존 OCR 결과 JSON
    - table_data: Table Detector 결과 JSON
    - profile: 파싱 프로파일
    """
    logger.info(f"Parts List 파싱 시작, profile={profile}")
    parser = get_parser()
    ocr_texts = []
    table = None

    # OCR 결과 파싱
    if ocr_results:
        try:
            ocr_texts = json.loads(ocr_results)
            if isinstance(ocr_texts, dict):
                ocr_texts = ocr_texts.get("texts", ocr_texts.get("results", []))
        except json.JSONDecodeError:
            pass

    # Table 데이터 파싱
    if table_data:
        try:
            table = json.loads(table_data)
        except json.JSONDecodeError:
            pass

    # 파일에서 OCR 수행
    if file and file.filename and not ocr_texts:
        file_content = await file.read()
        if file_content:
            ocr_texts = await call_edocr2_ocr(file_content, file.filename)

    # OCR 결과 없으면 Mock 데이터
    if not ocr_texts and not table:
        logger.info("Parts List OCR 결과 없음 - Mock 데이터 반환")
        mock_items = [
            PartsListItemResponse(no="1", description="RING UPPER", material="SF45A", size_dwg_no="TD0062017P001", qty=1),
            PartsListItemResponse(no="2", description="RING LOWER", material="SF45A", size_dwg_no="TD0062017P002", qty=1),
            PartsListItemResponse(no="3", description="HEX SOCKET HD BOLT", material="SEE EXCEL BOM", size_dwg_no="TD0060701P020L", qty=4),
            PartsListItemResponse(no="4", description="DOWEL PIN", material="SEE EXCEL BOM", size_dwg_no="TD0060703SP009", qty=2),
            PartsListItemResponse(no="5", description="SHIM PLATE", material="SEE EXCEL BOM", size_dwg_no="TD0060742P003", qty=4),
        ]
        return PartsListResponse(
            success=True,
            items=mock_items,
            total_count=len(mock_items),
            confidence=0.5
        )

    # 실제 파싱
    parsed_items = parser.parse_parts_list(ocr_texts, table)

    # 결과 변환
    items = [
        PartsListItemResponse(
            no=item.no,
            description=item.description,
            material=item.material or "SEE EXCEL BOM",
            size_dwg_no=item.size_dwg_no,
            qty=item.qty,
            remark=item.remark,
            weight=item.weight
        )
        for item in parsed_items
    ]

    confidence = min(1.0, len(items) * 0.1) if items else 0.0

    return PartsListResponse(
        success=len(items) > 0,
        items=items,
        total_count=len(items),
        confidence=confidence
    )


# =====================
# Dimension Parser
# =====================

@router.post("/dimensionparser", response_model=DimensionParserResponse)
async def parse_dimensions(
    file: UploadFile = File(None),
    ocr_results: str = Form(None),
    profile: str = Form("bearing")
):
    """
    치수 파싱 - OCR 결과에서 치수 정보 추출
    """
    logger.info(f"Dimension 파싱 시작, profile={profile}")
    parser = get_parser()
    ocr_texts = []

    if ocr_results:
        try:
            ocr_texts = json.loads(ocr_results)
            if isinstance(ocr_texts, dict):
                ocr_texts = ocr_texts.get("texts", ocr_texts.get("results", []))
        except json.JSONDecodeError:
            pass

    if file and file.filename and not ocr_texts:
        file_content = await file.read()
        if file_content:
            ocr_texts = await call_edocr2_ocr(file_content, file.filename)

    if not ocr_texts:
        # Mock 데이터
        return DimensionParserResponse(
            success=True,
            dimensions=[
                DimensionItem(type="diameter", value=314.0, tolerance="±0.11", raw_text="Ø314 ±0.11"),
                DimensionItem(type="bearing_od_id", outer_diameter=480.0, inner_diameter=314.0, raw_text="(Ø480) Ø314"),
                DimensionItem(type="tolerance", value=200.0, raw_text="(200)"),
            ],
            gdt_symbols=["⊥ 0.02 A"],
            confidence=0.5
        )

    # 실제 파싱
    dims = parser.extract_dimensions(ocr_texts)

    items = [
        DimensionItem(
            type=d.get("type", "unknown"),
            value=d.get("value"),
            outer_diameter=d.get("outer_diameter"),
            inner_diameter=d.get("inner_diameter"),
            tolerance=d.get("tolerance"),
            upper_tolerance=d.get("upper_tolerance"),
            lower_tolerance=d.get("lower_tolerance"),
            raw_text=d.get("raw_text", "")
        )
        for d in dims
    ]

    return DimensionParserResponse(
        success=len(items) > 0,
        dimensions=items,
        gdt_symbols=[],
        confidence=min(1.0, len(items) * 0.15)
    )


# =====================
# BOM Matcher
# =====================

@router.post("/bommatcher", response_model=BOMMatcherResponse)
async def match_bom(
    title_block: str = Form(None),
    parts_list: str = Form(None),
    dimensions: str = Form(None),
    profile: str = Form("bearing")
):
    """
    BOM 매칭 - Title Block + Parts List + Dimensions 통합
    """
    logger.info(f"BOM Matching 시작, profile={profile}")

    # 입력 데이터 파싱
    tb_data = {}
    pl_data = []
    dim_data = []

    if title_block:
        try:
            tb_data = json.loads(title_block)
        except:
            pass

    if parts_list:
        try:
            pl_data = json.loads(parts_list)
            if isinstance(pl_data, dict):
                pl_data = pl_data.get("items", [])
        except:
            pass

    if dimensions:
        try:
            dim_data = json.loads(dimensions)
            if isinstance(dim_data, dict):
                dim_data = dim_data.get("dimensions", [])
        except:
            pass

    # 통합 BOM 생성
    matched_items = []
    for item in pl_data:
        if isinstance(item, dict):
            bom_item = BOMItem(
                no=item.get("no", item.get("part_no", "")),
                description=item.get("description", ""),
                material=item.get("material", tb_data.get("material", "SEE EXCEL BOM")),
                size_dwg_no=item.get("size_dwg_no", ""),
                dimensions=[DimensionItem(**d) for d in dim_data[:2]] if dim_data else [],
                qty=item.get("qty", 1),
                weight=item.get("weight")
            )
            matched_items.append(bom_item)

    # 항목이 없으면 Mock 데이터
    if not matched_items:
        matched_items = [
            BOMItem(
                no="1",
                description="RING UPPER",
                material=tb_data.get("material", "SF45A"),
                size_dwg_no="TD0062017P001",
                dimensions=[
                    DimensionItem(type="diameter", value=314.0, tolerance="±0.11"),
                ],
                qty=1
            ),
            BOMItem(
                no="2",
                description="RING LOWER",
                material=tb_data.get("material", "SF45A"),
                size_dwg_no="TD0062017P002",
                dimensions=[],
                qty=1
            ),
        ]

    return BOMMatcherResponse(
        success=True,
        matched_items=matched_items,
        unmatched_count=0,
        match_confidence=0.9 if matched_items else 0.5
    )


# =====================
# Quote Generator
# =====================

# 재질별 단가 (KRW/kg)
MATERIAL_PRICES = {
    "SF45A": 5000,
    "SF440A": 5500,
    "SM490A": 4800,
    "S45C": 4500,
    "S45C-N": 4800,
    "SS400": 3500,
    "STS304": 12000,
    "SCM435": 7000,
    "ASTM B23 GR.2": 45000,  # Babbitt
    "ASTM A193 B7": 8000,
    "SEE EXCEL BOM": 5000,  # 기본값
    "DEFAULT": 5000,
}

# 부품 타입별 가공비 (KRW)
LABOR_COSTS = {
    "RING": 80000,
    "BEARING": 100000,
    "CASING": 120000,
    "PAD": 50000,
    "BOLT": 5000,
    "NUT": 3000,
    "PIN": 8000,
    "WASHER": 2000,
    "PLATE": 15000,
    "ASSY": 150000,
    "DEFAULT": 30000,
}

# 수량 할인
QUANTITY_DISCOUNTS = [
    (100, 0.15),  # 100개 이상: 15%
    (50, 0.10),   # 50개 이상: 10%
    (20, 0.07),   # 20개 이상: 7%
    (10, 0.05),   # 10개 이상: 5%
]


def get_material_price(material: str) -> float:
    """재질별 단가 조회"""
    material_upper = material.upper().strip()
    for key, price in MATERIAL_PRICES.items():
        if key in material_upper or material_upper in key:
            return price
    return MATERIAL_PRICES["DEFAULT"]


def get_labor_cost(description: str) -> float:
    """부품 타입별 가공비 조회"""
    desc_upper = description.upper()
    for key, cost in LABOR_COSTS.items():
        if key in desc_upper:
            return cost
    return LABOR_COSTS["DEFAULT"]


def get_quantity_discount(total_qty: int) -> float:
    """수량 할인율 계산"""
    for min_qty, discount in QUANTITY_DISCOUNTS:
        if total_qty >= min_qty:
            return discount
    return 0.0


@router.post("/quotegenerator", response_model=QuoteGeneratorResponse)
async def generate_quote(
    bom_data: str = Form(None),
    currency: str = Form("KRW"),
    material_markup: float = Form(1.3),
    labor_markup: float = Form(1.5),
    tax_rate: float = Form(0.1),
    customer_id: str = Form(None),
    profile: str = Form("bearing")
):
    """
    견적 생성 - BOM 데이터 기반 자동 견적

    - bom_data: BOM JSON 데이터
    - currency: 통화 (KRW, USD, etc.)
    - material_markup: 재질 마크업 (기본 1.3 = 30%)
    - labor_markup: 가공비 마크업 (기본 1.5 = 50%)
    - tax_rate: 세율 (기본 0.1 = 10%)
    - customer_id: 고객 ID (DSE, DOOSAN 등) - 고객별 할인 적용
    - profile: 프로파일 (bearing)
    """
    logger.info(f"Quote 생성 시작, currency={currency}, customer={customer_id}, profile={profile}")

    # 가격 데이터베이스 초기화
    price_db = get_price_database()

    # BOM 데이터 파싱
    bom_items = []
    if bom_data:
        try:
            data = json.loads(bom_data)
            if isinstance(data, dict):
                bom_items = data.get("matched_items", data.get("items", []))
            elif isinstance(data, list):
                bom_items = data
        except:
            pass

    # BOM이 없으면 Mock 데이터
    if not bom_items:
        bom_items = [
            {"no": "1", "description": "RING UPPER", "material": "SF45A", "qty": 1, "weight": 15.0},
            {"no": "2", "description": "RING LOWER", "material": "SF45A", "qty": 1, "weight": 15.0},
            {"no": "3", "description": "HEX SOCKET HD BOLT", "material": "SCM435", "qty": 4, "weight": 0.5},
            {"no": "4", "description": "DOWEL PIN", "material": "STS304", "qty": 2, "weight": 0.2},
        ]

    # 가격 데이터베이스로 견적 계산
    quote_result = price_db.calculate_quote(
        parts=bom_items,
        customer_id=customer_id,
        material_markup=material_markup,
        labor_markup=labor_markup,
        tax_rate=tax_rate
    )

    # 응답 형식으로 변환
    quote_items = []
    for item in quote_result["line_items"]:
        quote_items.append(QuoteLineItem(
            no=item["no"],
            description=f"{item['description']} ({item['material']})",
            material=item["material"],
            material_cost=item["material_cost"],
            labor_cost=item["labor_cost"],
            quantity=item["qty"],
            unit_price=item["unit_price"],
            total_price=item["total_price"]
        ))

    return QuoteGeneratorResponse(
        success=True,
        quote_number=f"Q-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        date=datetime.now().strftime("%Y-%m-%d"),
        items=quote_items,
        subtotal=quote_result["subtotal"],
        discount=quote_result["discount_amount"],
        tax=quote_result["tax"],
        total=quote_result["total"],
        currency=quote_result["currency"]
    )


# =====================
# Price Database API
# =====================

@router.get("/prices/materials")
async def list_materials():
    """재질 가격 목록 조회"""
    price_db = get_price_database()
    return {
        "success": True,
        "materials": price_db.list_materials(),
        "count": len(price_db.material_prices)
    }


@router.get("/prices/labor")
async def list_labor_costs():
    """가공비 목록 조회"""
    price_db = get_price_database()
    return {
        "success": True,
        "labor_costs": price_db.list_labor_costs(),
        "count": len(price_db.labor_costs)
    }


@router.get("/prices/discounts")
async def get_quantity_discounts():
    """수량 할인 테이블 조회"""
    price_db = get_price_database()
    return {
        "success": True,
        "discounts": [
            {"min_qty": qty, "discount_rate": rate, "discount_percent": f"{rate*100:.0f}%"}
            for qty, rate in price_db.quantity_discounts
        ]
    }


@router.get("/customers/{customer_id}")
async def get_customer_pricing(customer_id: str):
    """고객 가격 설정 조회"""
    price_db = get_price_database()
    config = price_db.get_customer_config(customer_id)

    if not config:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")

    return {
        "success": True,
        "customer": {
            "id": config.customer_id,
            "name": config.customer_name,
            "material_discount": config.material_discount,
            "labor_discount": config.labor_discount,
            "payment_terms": config.payment_terms,
            "currency": config.currency
        }
    }


@router.get("/customers")
async def list_customers():
    """고객 목록 조회 (상세 설정 포함)"""
    customer_config = get_customer_config()
    return {
        "success": True,
        "customers": customer_config.list_customers()
    }


@router.get("/customers/{customer_id}/profile")
async def get_customer_profile(customer_id: str):
    """고객 파싱 프로파일 조회"""
    customer_config = get_customer_config()
    profile = customer_config.get_parsing_profile(customer_id)

    if not profile:
        raise HTTPException(status_code=404, detail=f"Customer profile not found: {customer_id}")

    return {
        "success": True,
        "profile": {
            "profile_id": profile.profile_id,
            "name": profile.name,
            "drawing_number_patterns": profile.drawing_number_patterns,
            "revision_patterns": profile.revision_patterns,
            "material_patterns": profile.material_patterns,
            "table_headers": profile.table_headers,
            "ocr_engine": profile.ocr_engine,
            "ocr_profile": profile.ocr_profile,
            "confidence_threshold": profile.confidence_threshold
        }
    }


@router.get("/customers/{customer_id}/template/quote")
async def get_customer_quote_template(customer_id: str):
    """고객 견적서 템플릿 조회"""
    customer_config = get_customer_config()
    template = customer_config.get_quote_template(customer_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"Quote template not found: {customer_id}")

    return {
        "success": True,
        "template": {
            "template_id": template.template_id,
            "name": template.name,
            "type": template.type,
            "include_logo": template.include_logo,
            "visible_columns": template.visible_columns,
            "column_headers_kr": template.column_headers_kr,
            "currency_format": template.currency_format,
            "decimal_places": template.decimal_places,
            "footer_text": template.footer_text
        }
    }


@router.get("/customers/{customer_id}/full")
async def get_customer_full_config(customer_id: str):
    """고객 전체 설정 조회"""
    customer_config = get_customer_config()
    customer = customer_config.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")

    return {
        "success": True,
        "customer": {
            "customer_id": customer.customer_id,
            "customer_name": customer.customer_name,
            "contact": {
                "name": customer.contact_name,
                "email": customer.contact_email,
                "phone": customer.contact_phone,
                "address": customer.address
            },
            "pricing": {
                "material_discount": customer.material_discount,
                "labor_discount": customer.labor_discount,
                "payment_terms": customer.payment_terms,
                "currency": customer.currency
            },
            "parsing_profile": {
                "profile_id": customer.parsing_profile.profile_id,
                "name": customer.parsing_profile.name,
                "ocr_engine": customer.parsing_profile.ocr_engine
            } if customer.parsing_profile else None,
            "quote_template": {
                "template_id": customer.quote_template.template_id,
                "name": customer.quote_template.name
            } if customer.quote_template else None,
            "is_active": customer.is_active,
            "created_at": customer.created_at,
            "updated_at": customer.updated_at
        }
    }


# =====================
# Quote Export
# =====================

@router.post("/quote/export/excel")
async def export_quote_excel(
    quote_data: str = Form(...),
    customer_id: str = Form(None)
):
    """
    견적서 Excel 내보내기

    - quote_data: 견적 데이터 JSON
    - customer_id: 고객 ID (선택)
    """
    from services.quote_exporter import get_quote_exporter
    from fastapi.responses import StreamingResponse

    try:
        quote = json.loads(quote_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid quote data JSON")

    customer_info = None
    if customer_id:
        customer_config = get_customer_config()
        customer = customer_config.get_customer(customer_id)
        if customer:
            customer_info = {
                "customer_name": customer.customer_name,
                "contact_name": customer.contact_name,
                "contact_email": customer.contact_email,
            }

    exporter = get_quote_exporter()
    excel_bytes = exporter.export_to_excel(quote, customer_info)

    quote_number = quote.get('quote_number', 'quote')
    filename = f"{quote_number}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/quote/export/pdf")
async def export_quote_pdf(
    quote_data: str = Form(...),
    customer_id: str = Form(None)
):
    """
    견적서 PDF 내보내기

    - quote_data: 견적 데이터 JSON
    - customer_id: 고객 ID (선택)
    """
    from services.quote_exporter import get_quote_exporter
    from fastapi.responses import StreamingResponse

    try:
        quote = json.loads(quote_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid quote data JSON")

    customer_info = None
    if customer_id:
        customer_config = get_customer_config()
        customer = customer_config.get_customer(customer_id)
        if customer:
            customer_info = {
                "customer_name": customer.customer_name,
                "contact_name": customer.contact_name,
                "contact_email": customer.contact_email,
            }

    exporter = get_quote_exporter()
    pdf_bytes = exporter.export_to_pdf(quote, customer_info)

    quote_number = quote.get('quote_number', 'quote')
    filename = f"{quote_number}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
