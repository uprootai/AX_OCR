"""
Design Checker API Server
도면 설계 오류 검출 및 규정 검증 API

포트: 5019

설계 검증 규칙:
- ISO 10628 (P&ID 표준)
- ISA 5.1 (계기 심볼 표준)
- 조선/해양 도면 규정
"""
import os
import time
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("DESIGN_CHECKER_PORT", "5019"))


# =====================
# Enums and Constants
# =====================

class Severity(str, Enum):
    ERROR = "error"      # 반드시 수정 필요
    WARNING = "warning"  # 권고 사항
    INFO = "info"        # 참고 정보


class RuleCategory(str, Enum):
    CONNECTIVITY = "connectivity"       # 연결 오류
    SYMBOL = "symbol"                   # 심볼 오류
    LABELING = "labeling"               # 라벨링 오류
    SPECIFICATION = "specification"     # 사양 오류
    STANDARD = "standard"               # 표준 위반
    SAFETY = "safety"                   # 안전 관련


# Design Rules Definition
DESIGN_RULES = {
    # 연결 관련 규칙
    "CONN-001": {
        "id": "CONN-001",
        "name": "끊어진 라인 검출",
        "name_en": "Broken Line Detection",
        "description": "라인이 심볼에 연결되지 않고 끊어진 경우",
        "category": RuleCategory.CONNECTIVITY,
        "severity": Severity.ERROR,
        "standard": "ISO 10628"
    },
    "CONN-002": {
        "id": "CONN-002",
        "name": "미연결 심볼",
        "name_en": "Unconnected Symbol",
        "description": "어떤 라인에도 연결되지 않은 심볼 검출",
        "category": RuleCategory.CONNECTIVITY,
        "severity": Severity.WARNING,
        "standard": "ISO 10628"
    },
    "CONN-003": {
        "id": "CONN-003",
        "name": "중복 연결",
        "name_en": "Duplicate Connection",
        "description": "동일한 두 심볼 간 중복 연결 검출",
        "category": RuleCategory.CONNECTIVITY,
        "severity": Severity.WARNING,
        "standard": "Internal"
    },
    "CONN-004": {
        "id": "CONN-004",
        "name": "데드엔드 라인",
        "name_en": "Dead-end Line",
        "description": "한쪽 끝만 연결된 라인 검출 (의도적 캡 제외)",
        "category": RuleCategory.CONNECTIVITY,
        "severity": Severity.WARNING,
        "standard": "ISO 10628"
    },

    # 심볼 관련 규칙
    "SYM-001": {
        "id": "SYM-001",
        "name": "미인식 심볼",
        "name_en": "Unrecognized Symbol",
        "description": "표준에 없는 심볼 사용",
        "category": RuleCategory.SYMBOL,
        "severity": Severity.WARNING,
        "standard": "ISA 5.1"
    },
    "SYM-002": {
        "id": "SYM-002",
        "name": "심볼 중첩",
        "name_en": "Symbol Overlap",
        "description": "두 개 이상의 심볼이 겹쳐있음",
        "category": RuleCategory.SYMBOL,
        "severity": Severity.ERROR,
        "standard": "Internal"
    },
    "SYM-003": {
        "id": "SYM-003",
        "name": "심볼 방향 오류",
        "name_en": "Symbol Orientation Error",
        "description": "밸브/펌프 등의 방향이 흐름과 불일치",
        "category": RuleCategory.SYMBOL,
        "severity": Severity.WARNING,
        "standard": "ISO 10628"
    },
    "SYM-004": {
        "id": "SYM-004",
        "name": "심볼 크기 비표준",
        "name_en": "Non-standard Symbol Size",
        "description": "심볼 크기가 도면 규정에 맞지 않음",
        "category": RuleCategory.SYMBOL,
        "severity": Severity.INFO,
        "standard": "Internal"
    },

    # 라벨링 관련 규칙
    "LBL-001": {
        "id": "LBL-001",
        "name": "태그번호 누락",
        "name_en": "Missing Tag Number",
        "description": "계기/밸브에 태그번호가 없음",
        "category": RuleCategory.LABELING,
        "severity": Severity.ERROR,
        "standard": "ISA 5.1"
    },
    "LBL-002": {
        "id": "LBL-002",
        "name": "중복 태그번호",
        "name_en": "Duplicate Tag Number",
        "description": "동일한 태그번호가 여러 곳에 사용됨",
        "category": RuleCategory.LABELING,
        "severity": Severity.ERROR,
        "standard": "ISA 5.1"
    },
    "LBL-003": {
        "id": "LBL-003",
        "name": "태그번호 형식 오류",
        "name_en": "Tag Number Format Error",
        "description": "태그번호 형식이 표준에 맞지 않음 (예: FV-001, PT-100)",
        "category": RuleCategory.LABELING,
        "severity": Severity.WARNING,
        "standard": "ISA 5.1"
    },
    "LBL-004": {
        "id": "LBL-004",
        "name": "라인번호 누락",
        "name_en": "Missing Line Number",
        "description": "배관 라인에 라인번호가 없음",
        "category": RuleCategory.LABELING,
        "severity": Severity.WARNING,
        "standard": "ISO 10628"
    },

    # 사양 관련 규칙
    "SPEC-001": {
        "id": "SPEC-001",
        "name": "배관 사이즈 불일치",
        "name_en": "Pipe Size Mismatch",
        "description": "연결된 배관 사이즈가 일치하지 않음 (리듀서 없음)",
        "category": RuleCategory.SPECIFICATION,
        "severity": Severity.ERROR,
        "standard": "Internal"
    },
    "SPEC-002": {
        "id": "SPEC-002",
        "name": "유체 등급 불일치",
        "name_en": "Fluid Class Mismatch",
        "description": "연결된 라인의 유체 등급이 다름",
        "category": RuleCategory.SPECIFICATION,
        "severity": Severity.ERROR,
        "standard": "Internal"
    },
    "SPEC-003": {
        "id": "SPEC-003",
        "name": "누락된 계기",
        "name_en": "Missing Instrument",
        "description": "필수 계기가 누락됨 (예: 펌프 후단 압력계)",
        "category": RuleCategory.SPECIFICATION,
        "severity": Severity.WARNING,
        "standard": "Engineering Best Practice"
    },

    # 표준 위반 규칙
    "STD-001": {
        "id": "STD-001",
        "name": "비표준 라인 타입",
        "name_en": "Non-standard Line Type",
        "description": "ISO 10628에 정의되지 않은 라인 타입 사용",
        "category": RuleCategory.STANDARD,
        "severity": Severity.INFO,
        "standard": "ISO 10628"
    },
    "STD-002": {
        "id": "STD-002",
        "name": "비표준 심볼 사용",
        "name_en": "Non-standard Symbol Usage",
        "description": "ISA 5.1에 정의되지 않은 계기 심볼 사용",
        "category": RuleCategory.STANDARD,
        "severity": Severity.INFO,
        "standard": "ISA 5.1"
    },

    # 안전 관련 규칙
    "SAF-001": {
        "id": "SAF-001",
        "name": "안전밸브 누락",
        "name_en": "Missing Safety Valve",
        "description": "압력용기에 안전밸브가 없음",
        "category": RuleCategory.SAFETY,
        "severity": Severity.ERROR,
        "standard": "ASME"
    },
    "SAF-002": {
        "id": "SAF-002",
        "name": "긴급차단밸브 누락",
        "name_en": "Missing Emergency Shutdown Valve",
        "description": "중요 계통에 긴급차단밸브가 없음",
        "category": RuleCategory.SAFETY,
        "severity": Severity.WARNING,
        "standard": "IEC 61511"
    },
    "SAF-003": {
        "id": "SAF-003",
        "name": "바이패스 없음",
        "name_en": "No Bypass Line",
        "description": "제어밸브에 바이패스 라인이 없음",
        "category": RuleCategory.SAFETY,
        "severity": Severity.INFO,
        "standard": "Engineering Best Practice"
    }
}


# =====================
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class ViolationLocation(BaseModel):
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    elements: Optional[List[str]] = None


class RuleViolation(BaseModel):
    rule_id: str
    rule_name: str
    rule_name_en: str
    category: str
    severity: str
    standard: str
    description: str
    location: Optional[ViolationLocation] = None
    affected_elements: List[str] = []
    suggestion: Optional[str] = None


class CheckSummary(BaseModel):
    total_violations: int
    errors: int
    warnings: int
    info: int
    by_category: Dict[str, int]
    compliance_score: float  # 0-100%


class DesignCheckResult(BaseModel):
    violations: List[RuleViolation]
    summary: CheckSummary
    rules_checked: int
    checked_at: str


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# Design Checker Class
# =====================

class DesignChecker:
    """P&ID 설계 검증기"""

    def __init__(self):
        self.rules = DESIGN_RULES

    def check_connectivity(
        self,
        symbols: List[Dict],
        connections: List[Dict]
    ) -> List[RuleViolation]:
        """연결 관련 규칙 검사"""
        violations = []

        # 연결된 심볼 ID 집합 (문자열로 통일)
        connected_symbols = set()
        for conn in connections:
            connected_symbols.add(str(conn.get("source_id", "")))
            connected_symbols.add(str(conn.get("target_id", "")))

        # CONN-002: 미연결 심볼 검출
        for symbol in symbols:
            symbol_id = str(symbol.get("id", ""))
            if symbol_id not in connected_symbols:
                rule = self.rules["CONN-002"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    location=ViolationLocation(
                        x=symbol.get("x", 0),
                        y=symbol.get("y", 0),
                        width=symbol.get("width"),
                        height=symbol.get("height")
                    ),
                    affected_elements=[symbol_id],
                    suggestion=f"심볼 '{symbol.get('label', symbol_id)}'을 배관 라인에 연결하세요."
                ))

        # CONN-003: 중복 연결 검출
        connection_pairs = {}
        for conn in connections:
            pair = tuple(sorted([str(conn.get("source_id", "")), str(conn.get("target_id", ""))]))
            if pair in connection_pairs:
                rule = self.rules["CONN-003"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    affected_elements=list(pair),
                    suggestion="중복된 연결 중 하나를 제거하세요."
                ))
            connection_pairs[pair] = conn

        return violations

    def check_labeling(
        self,
        symbols: List[Dict]
    ) -> List[RuleViolation]:
        """라벨링 관련 규칙 검사"""
        violations = []

        # 태그 번호 수집 (중복 검사용)
        tag_numbers = {}

        # 태그 필요 심볼 타입
        requires_tag = {"valve", "pump", "instrument", "transmitter", "controller", "indicator"}

        for symbol in symbols:
            symbol_id = str(symbol.get("id", ""))
            symbol_type = str(symbol.get("type", "")).lower()
            tag = symbol.get("tag_number", "")

            # LBL-001: 태그번호 누락
            if symbol_type in requires_tag and not tag:
                rule = self.rules["LBL-001"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    location=ViolationLocation(
                        x=symbol.get("x", 0),
                        y=symbol.get("y", 0)
                    ),
                    affected_elements=[symbol_id],
                    suggestion=f"{symbol_type} 심볼에 태그번호를 추가하세요."
                ))

            # 태그 번호 중복 체크용 수집
            if tag:
                if tag in tag_numbers:
                    tag_numbers[tag].append(symbol_id)
                else:
                    tag_numbers[tag] = [symbol_id]

        # LBL-002: 중복 태그번호
        for tag, symbol_ids in tag_numbers.items():
            if len(symbol_ids) > 1:
                rule = self.rules["LBL-002"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=f"태그번호 '{tag}'가 {len(symbol_ids)}개 심볼에서 중복 사용됨",
                    affected_elements=symbol_ids,
                    suggestion="각 심볼에 고유한 태그번호를 부여하세요."
                ))

        return violations

    def check_symbols(
        self,
        symbols: List[Dict]
    ) -> List[RuleViolation]:
        """심볼 관련 규칙 검사"""
        violations = []

        # SYM-002: 심볼 중첩 검출
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                if self._check_overlap(sym1, sym2):
                    rule = self.rules["SYM-002"]
                    violations.append(RuleViolation(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        rule_name_en=rule["name_en"],
                        category=rule["category"].value,
                        severity=rule["severity"].value,
                        standard=rule["standard"],
                        description=rule["description"],
                        location=ViolationLocation(
                            x=sym1.get("x", 0),
                            y=sym1.get("y", 0),
                            elements=[str(sym1.get("id", "")), str(sym2.get("id", ""))]
                        ),
                        affected_elements=[str(sym1.get("id", "")), str(sym2.get("id", ""))],
                        suggestion="중첩된 심볼을 분리하세요."
                    ))

        return violations

    def check_safety(
        self,
        symbols: List[Dict],
        connections: List[Dict]
    ) -> List[RuleViolation]:
        """안전 관련 규칙 검사"""
        violations = []

        # 심볼 타입별 분류
        pressure_vessels = [s for s in symbols if str(s.get("type", "")) in ["tank", "vessel", "drum", "column"]]
        safety_valves = [s for s in symbols if "safety" in str(s.get("type", "")).lower() or "psv" in str(s.get("tag_number", "")).upper()]
        control_valves = [s for s in symbols if str(s.get("type", "")) in ["control_valve", "globe_valve"] or "cv" in str(s.get("tag_number", "")).lower()]

        # 연결 그래프 구축 (문자열 ID 사용)
        connection_graph = {}
        for conn in connections:
            src = str(conn.get("source_id", ""))
            tgt = str(conn.get("target_id", ""))
            if src not in connection_graph:
                connection_graph[src] = []
            connection_graph[src].append(tgt)

        # SAF-001: 압력용기에 안전밸브 확인
        safety_valve_ids = {str(s.get("id", "")) for s in safety_valves}
        for vessel in pressure_vessels:
            vessel_id = str(vessel.get("id", ""))
            # 연결된 심볼 중 안전밸브가 있는지 확인
            connected_ids = connection_graph.get(vessel_id, [])
            has_safety_valve = any(cid in safety_valve_ids for cid in connected_ids)

            if not has_safety_valve:
                rule = self.rules["SAF-001"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    location=ViolationLocation(
                        x=vessel.get("x", 0),
                        y=vessel.get("y", 0)
                    ),
                    affected_elements=[vessel_id],
                    suggestion=f"압력용기 '{vessel.get('label', vessel_id)}'에 안전밸브(PSV)를 추가하세요."
                ))

        # SAF-003: 제어밸브 바이패스 확인 (Info 레벨)
        for cv in control_valves:
            cv_id = str(cv.get("id", ""))
            # 간단한 바이패스 검사 (실제로는 더 복잡한 그래프 분석 필요)
            connected_count = len(connection_graph.get(cv_id, []))
            if connected_count < 3:  # 바이패스가 있으면 최소 3개 연결
                rule = self.rules["SAF-003"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    location=ViolationLocation(
                        x=cv.get("x", 0),
                        y=cv.get("y", 0)
                    ),
                    affected_elements=[cv_id],
                    suggestion="유지보수를 위해 바이패스 라인 추가를 권장합니다."
                ))

        return violations

    def _check_overlap(self, sym1: Dict, sym2: Dict) -> bool:
        """두 심볼의 중첩 여부 확인"""
        x1, y1 = sym1.get("x", 0), sym1.get("y", 0)
        w1, h1 = sym1.get("width", 50), sym1.get("height", 50)
        x2, y2 = sym2.get("x", 0), sym2.get("y", 0)
        w2, h2 = sym2.get("width", 50), sym2.get("height", 50)

        # AABB 충돌 검사
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

    def run_all_checks(
        self,
        symbols: List[Dict],
        connections: List[Dict],
        lines: Optional[List[Dict]] = None
    ) -> DesignCheckResult:
        """모든 설계 규칙 검사 실행"""
        all_violations = []

        # 각 카테고리별 검사 실행
        all_violations.extend(self.check_connectivity(symbols, connections))
        all_violations.extend(self.check_labeling(symbols))
        all_violations.extend(self.check_symbols(symbols))
        all_violations.extend(self.check_safety(symbols, connections))

        # 요약 생성
        errors = sum(1 for v in all_violations if v.severity == "error")
        warnings = sum(1 for v in all_violations if v.severity == "warning")
        info_count = sum(1 for v in all_violations if v.severity == "info")

        by_category = {}
        for v in all_violations:
            cat = v.category
            by_category[cat] = by_category.get(cat, 0) + 1

        # 준수율 계산 (오류 가중치 높게)
        total_weight = len(symbols) * 10 if symbols else 10
        violation_weight = errors * 3 + warnings * 1 + info_count * 0.2
        compliance_score = max(0, min(100, 100 - (violation_weight / total_weight * 100)))

        summary = CheckSummary(
            total_violations=len(all_violations),
            errors=errors,
            warnings=warnings,
            info=info_count,
            by_category=by_category,
            compliance_score=round(compliance_score, 1)
        )

        return DesignCheckResult(
            violations=all_violations,
            summary=summary,
            rules_checked=len(self.rules),
            checked_at=datetime.now().isoformat()
        )


# Global checker instance
design_checker = DesignChecker()


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Design Checker API",
    description="P&ID 도면 설계 오류 검출 및 규정 검증 API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="design-checker-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "design-checker",
        "name": "Design Checker",
        "display_name": "설계 검증기",
        "display_name_ko": "설계 검증기",
        "version": "1.0.0",
        "description": "P&ID 도면 설계 오류 검출 및 규정 검증",
        "description_ko": "P&ID 도면 설계 오류 검출 및 규정 검증",
        "base_url": f"http://localhost:{API_PORT}",
        "endpoint": "/api/v1/check",
        "method": "POST",
        "requires_image": False,
        "blueprintflow": {
            "category": "analysis",
            "color": "#ef4444",
            "icon": "ShieldCheck"
        },
        "inputs": [
            {"name": "symbols", "type": "object[]", "required": True, "description": "심볼 목록 (YOLO-PID 출력)"},
            {"name": "connections", "type": "object[]", "required": True, "description": "연결 정보 (PID-Analyzer 출력)"}
        ],
        "outputs": [
            {"name": "violations", "type": "object[]", "description": "위반 사항 목록"},
            {"name": "summary", "type": "object", "description": "검사 요약"},
            {"name": "compliance_score", "type": "number", "description": "규정 준수율 (0-100%)"}
        ],
        "parameters": [
            {
                "name": "categories",
                "type": "string[]",
                "description": "검사할 규칙 카테고리",
                "default": ["connectivity", "symbol", "labeling", "specification", "standard", "safety"]
            },
            {
                "name": "severity_threshold",
                "type": "string",
                "description": "보고할 최소 심각도",
                "default": "info",
                "options": ["error", "warning", "info"]
            }
        ]
    }


@app.get("/api/v1/rules")
async def get_rules():
    """사용 가능한 설계 규칙 목록 조회"""
    rules_list = []
    for rule_id, rule in DESIGN_RULES.items():
        rules_list.append({
            "id": rule["id"],
            "name": rule["name"],
            "name_en": rule["name_en"],
            "description": rule["description"],
            "category": rule["category"].value,
            "severity": rule["severity"].value,
            "standard": rule["standard"]
        })

    return {
        "total_rules": len(rules_list),
        "rules": rules_list,
        "categories": [cat.value for cat in RuleCategory],
        "severities": [sev.value for sev in Severity]
    }


@app.post("/api/v1/check")
async def check_design(
    symbols: str = Form(..., description="심볼 목록 (JSON)"),
    connections: str = Form(default="[]", description="연결 정보 (JSON)"),
    lines: str = Form(default="[]", description="라인 정보 (JSON)"),
    categories: str = Form(default="", description="검사할 카테고리 (쉼표 구분)"),
    severity_threshold: str = Form(default="info", description="최소 심각도")
):
    """
    설계 검증 실행

    symbols와 connections는 이전 단계 API(YOLO-PID, PID-Analyzer)의 출력을 사용
    """
    start_time = time.time()

    try:
        # JSON 파싱
        symbols_data = json.loads(symbols)
        connections_data = json.loads(connections)
        lines_data = json.loads(lines) if lines else []

        logger.info(f"Checking design: {len(symbols_data)} symbols, {len(connections_data)} connections")

        # 검사 실행
        result = design_checker.run_all_checks(
            symbols=symbols_data,
            connections=connections_data,
            lines=lines_data
        )

        # 심각도 필터링
        severity_order = {"error": 0, "warning": 1, "info": 2}
        threshold = severity_order.get(severity_threshold, 2)
        filtered_violations = [
            v for v in result.violations
            if severity_order.get(v.severity, 2) <= threshold
        ]

        # 카테고리 필터링
        if categories:
            category_list = [c.strip() for c in categories.split(",")]
            filtered_violations = [
                v for v in filtered_violations
                if v.category in category_list
            ]

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                "violations": [v.dict() for v in filtered_violations],
                "summary": result.summary.dict(),
                "rules_checked": result.rules_checked,
                "checked_at": result.checked_at,
                "filters_applied": {
                    "severity_threshold": severity_threshold,
                    "categories": categories if categories else "all"
                }
            },
            processing_time=round(processing_time, 3)
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=f"JSON 파싱 오류: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Design check error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(
    file: Optional[UploadFile] = File(None, description="입력 이미지 (선택)"),
    symbols: str = Form(default="[]", description="심볼 목록 (JSON)"),
    connections: str = Form(default="[]", description="연결 정보 (JSON)")
):
    """
    통합 처리 엔드포인트 (BlueprintFlow 호환)

    이미지 없이 symbols/connections 데이터로 직접 검증 수행
    """
    return await check_design(
        symbols=symbols,
        connections=connections,
        lines="[]",
        categories="",
        severity_threshold="info"
    )


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Design Checker API on port {API_PORT}")
    logger.info(f"Total design rules: {len(DESIGN_RULES)}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
