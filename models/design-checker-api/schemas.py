"""
Design Checker API - Pydantic Schemas
설계 검증 API의 요청/응답 스키마 정의
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    service: str
    version: str
    timestamp: str


class ViolationLocation(BaseModel):
    """위반 위치 정보"""
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    elements: Optional[List[str]] = None


class RuleViolation(BaseModel):
    """규칙 위반 정보"""
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
    """검사 요약"""
    total_violations: int
    errors: int
    warnings: int
    info: int
    by_category: Dict[str, int]
    compliance_score: float  # 0-100%


class DesignCheckResult(BaseModel):
    """설계 검사 결과"""
    violations: List[RuleViolation]
    summary: CheckSummary
    rules_checked: int
    checked_at: str


class ProcessResponse(BaseModel):
    """API 처리 응답"""
    success: bool
    data: Dict[str, Any]
    processing_time: float = 0.0
    error: Optional[str] = None


class RuleInfo(BaseModel):
    """규칙 정보"""
    id: str
    name: str
    name_en: str
    description: str
    category: str
    severity: str
    standard: str


class RulesListResponse(BaseModel):
    """규칙 목록 응답"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
