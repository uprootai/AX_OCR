"""검증(Validation) 스키마 — 분석 결과 품질 평가

에이전트 하네스의 핵심: 기계적 Pass/Fail 판정을 위한 데이터 모델.
모든 도메인(베어링, P&ID, GD&T 등)에서 공통 사용.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """검증 결과 심각도"""
    ERROR = "error"      # 물리적 불가능 — 자동 보정 시도
    WARNING = "warning"  # 의심스러움 — 플래그만
    INFO = "info"        # 참고 정보


class QualityGrade(str, Enum):
    """최종 품질 등급"""
    PASS = "pass"    # 모든 검증 통과
    WARN = "warn"    # warning만 있음 (error 없음)
    FAIL = "fail"    # error 1개 이상


class ValidationVerdict(BaseModel):
    """개별 검증 규칙의 판정 결과"""
    rule_id: str = Field(..., description="규칙 ID (예: bearing.od_gt_id)")
    severity: Severity
    message: str = Field(..., description="사람이 읽을 수 있는 설명")
    field: Optional[str] = Field(None, description="관련 필드 (od, id, width 등)")
    actual_value: Optional[Any] = Field(None, description="실제 값")
    expected_range: Optional[str] = Field(None, description="기대 범위")
    correction_hint: Optional[Dict[str, Any]] = Field(
        None, description="자동 보정 힌트 (예: {action: swap, fields: [od, id]})"
    )


class CorrectionRecord(BaseModel):
    """자동 보정 이력"""
    rule_id: str
    strategy: str = Field(..., description="적용된 보정 전략 이름")
    before: Dict[str, Any]
    after: Dict[str, Any]
    success: bool = True


class ValidationReport(BaseModel):
    """분석 결과 전체 검증 리포트"""
    grade: QualityGrade = QualityGrade.PASS
    verdicts: List[ValidationVerdict] = Field(default_factory=list)
    corrections: List[CorrectionRecord] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    iteration_count: int = Field(
        default=1, description="자기수정 루프 반복 횟수"
    )

    def add_verdict(self, verdict: ValidationVerdict):
        self.verdicts.append(verdict)
        if verdict.severity == Severity.ERROR:
            self.error_count += 1
            self.grade = QualityGrade.FAIL
        elif verdict.severity == Severity.WARNING:
            self.warning_count += 1
            if self.grade == QualityGrade.PASS:
                self.grade = QualityGrade.WARN

    @property
    def is_pass(self) -> bool:
        return self.grade == QualityGrade.PASS

    @property
    def summary(self) -> str:
        parts = []
        if self.error_count:
            parts.append(f"{self.error_count}E")
        if self.warning_count:
            parts.append(f"{self.warning_count}W")
        if self.corrections:
            parts.append(f"{len(self.corrections)}C")
        return "/".join(parts) if parts else "OK"


class BatchQualitySummary(BaseModel):
    """배치 분석 품질 요약"""
    total_images: int = 0
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    correction_count: int = 0
    common_errors: Dict[str, int] = Field(
        default_factory=dict, description="rule_id별 에러 빈도"
    )

    @property
    def pass_rate(self) -> float:
        if self.total_images == 0:
            return 0.0
        return round(self.pass_count / self.total_images * 100, 1)

    def record(self, report: ValidationReport):
        self.total_images += 1
        if report.grade == QualityGrade.PASS:
            self.pass_count += 1
        elif report.grade == QualityGrade.WARN:
            self.warn_count += 1
        else:
            self.fail_count += 1
        self.correction_count += len(report.corrections)
        for v in report.verdicts:
            if v.severity == Severity.ERROR:
                self.common_errors[v.rule_id] = (
                    self.common_errors.get(v.rule_id, 0) + 1
                )
