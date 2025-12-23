"""Active Learning 서비스

검증 효율 향상을 위한 우선순위 기반 검증 큐 관리
- 저신뢰 항목 우선 검증
- 고신뢰 항목 일괄 승인
- 검증 결과 로깅 (모델 재학습용)
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 환경 변수에서 설정 로드
VERIFICATION_LOG_PATH = os.getenv("VERIFICATION_LOG_PATH", "/data/logs/verification")
AUTO_APPROVE_THRESHOLD = float(os.getenv("AUTO_APPROVE_THRESHOLD", "0.9"))
CRITICAL_THRESHOLD = float(os.getenv("CRITICAL_THRESHOLD", "0.7"))


class Priority(str, Enum):
    """검증 우선순위"""
    CRITICAL = "critical"  # 신뢰도 < 0.7
    HIGH = "high"          # 관계 연결 실패
    MEDIUM = "medium"      # 신뢰도 0.7-0.9
    LOW = "low"            # 신뢰도 > 0.9 (자동 승인 후보)


@dataclass
class VerificationItem:
    """검증 대상 항목"""
    id: str
    item_type: str  # 'dimension', 'symbol', 'relation'
    data: Dict[str, Any]
    confidence: float
    priority: Priority
    has_relation: bool = True
    reason: str = ""  # 우선순위 결정 이유

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "item_type": self.item_type,
            "data": self.data,
            "confidence": self.confidence,
            "priority": self.priority.value,
            "has_relation": self.has_relation,
            "reason": self.reason
        }


@dataclass
class VerificationLog:
    """검증 결과 로그 (모델 재학습용)"""
    item_id: str
    item_type: str
    original_data: Dict[str, Any]
    user_action: str  # 'approved', 'rejected', 'modified'
    modified_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    review_time_seconds: Optional[float] = None


class ActiveLearningService:
    """
    Active Learning 기반 검증 관리

    - 저신뢰 항목 우선 검증
    - 검증 결과 로깅
    - 모델 개선 데이터 수집
    """

    def __init__(
        self,
        auto_approve_threshold: float = AUTO_APPROVE_THRESHOLD,
        critical_threshold: float = CRITICAL_THRESHOLD,
        log_path: str = VERIFICATION_LOG_PATH
    ):
        self.thresholds = {
            'critical': critical_threshold,
            'auto_approve': auto_approve_threshold
        }
        self.log_path = Path(log_path)
        self.verification_logs: List[VerificationLog] = []

        # 로그 디렉토리 생성
        self.log_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"ActiveLearningService 초기화: "
            f"critical<{critical_threshold}, auto_approve>{auto_approve_threshold}"
        )

    def prioritize_items(
        self,
        items: List[Dict[str, Any]],
        item_type: str = 'dimension'
    ) -> Dict[Priority, List[VerificationItem]]:
        """
        항목들을 우선순위별로 분류

        Args:
            items: 검증 대상 항목들
            item_type: 항목 유형 ('dimension', 'symbol')

        Returns:
            우선순위별 분류된 항목 딕셔너리
        """
        prioritized: Dict[Priority, List[VerificationItem]] = {
            Priority.CRITICAL: [],
            Priority.HIGH: [],
            Priority.MEDIUM: [],
            Priority.LOW: []
        }

        for item in items:
            confidence = item.get('confidence', 0)

            # 관계 연결 확인
            if item_type == 'dimension':
                has_relation = item.get('linked_to') is not None
            else:  # symbol
                has_relation = True  # 심볼은 항상 관계 있음으로 처리

            # 우선순위 결정
            priority, reason = self._determine_priority(
                confidence, has_relation, item
            )

            verification_item = VerificationItem(
                id=item.get('id', ''),
                item_type=item_type,
                data=item,
                confidence=confidence,
                priority=priority,
                has_relation=has_relation,
                reason=reason
            )
            prioritized[priority].append(verification_item)

        return prioritized

    def _determine_priority(
        self,
        confidence: float,
        has_relation: bool,
        item: Dict[str, Any]
    ) -> tuple[Priority, str]:
        """우선순위 결정 로직"""

        # 1. 매우 낮은 신뢰도 → CRITICAL
        if confidence < self.thresholds['critical']:
            return Priority.CRITICAL, f"낮은 신뢰도 ({confidence:.2f})"

        # 2. 관계 연결 실패 → HIGH
        if not has_relation:
            return Priority.HIGH, "심볼 연결 없음"

        # 3. 중간 신뢰도 → MEDIUM
        if confidence < self.thresholds['auto_approve']:
            return Priority.MEDIUM, f"중간 신뢰도 ({confidence:.2f})"

        # 4. 높은 신뢰도 → LOW (자동 승인 후보)
        return Priority.LOW, f"높은 신뢰도 ({confidence:.2f})"

    def get_verification_queue(
        self,
        items: List[Dict[str, Any]],
        item_type: str = 'dimension'
    ) -> List[VerificationItem]:
        """
        검증 큐 생성 (우선순위 순)

        Returns:
            우선순위 순으로 정렬된 검증 항목 목록
        """
        prioritized = self.prioritize_items(items, item_type)

        queue = []
        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            # 각 우선순위 내에서 신뢰도 낮은 순 정렬
            sorted_items = sorted(
                prioritized[priority],
                key=lambda x: x.confidence
            )
            queue.extend(sorted_items)

        return queue

    def get_auto_approve_candidates(
        self,
        items: List[Dict[str, Any]]
    ) -> List[str]:
        """
        자동 승인 후보 ID 목록

        신뢰도 >= auto_approve_threshold인 항목들
        """
        return [
            item['id'] for item in items
            if item.get('confidence', 0) >= self.thresholds['auto_approve']
            and item.get('verification_status', 'pending') == 'pending'
        ]

    def log_verification(
        self,
        item_id: str,
        item_type: str,
        original_data: Dict[str, Any],
        user_action: str,
        modified_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        review_time_seconds: Optional[float] = None
    ):
        """
        검증 결과 로깅

        이 데이터는 모델 재학습에 활용
        """
        log = VerificationLog(
            item_id=item_id,
            item_type=item_type,
            original_data=original_data,
            user_action=user_action,
            modified_data=modified_data,
            timestamp=datetime.now(),
            session_id=session_id,
            review_time_seconds=review_time_seconds
        )
        self.verification_logs.append(log)

        # 파일에 저장
        self._save_log_to_file(log)

        logger.info(
            f"Verification logged: {item_type}/{item_id} -> {user_action}"
        )

    def _save_log_to_file(self, log: VerificationLog):
        """로그 파일 저장"""
        log_entry = {
            'item_id': log.item_id,
            'item_type': log.item_type,
            'original_data': log.original_data,
            'user_action': log.user_action,
            'modified_data': log.modified_data,
            'timestamp': log.timestamp.isoformat(),
            'session_id': log.session_id,
            'review_time_seconds': log.review_time_seconds
        }

        # 일별 로그 파일
        date_str = log.timestamp.strftime("%Y-%m-%d")
        log_file = self.log_path / f"verification_{date_str}.jsonl"

        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"로그 저장 실패: {e}")

    def get_verification_stats(
        self,
        items: List[Dict[str, Any]],
        item_type: str = 'dimension'
    ) -> Dict[str, Any]:
        """
        검증 통계
        """
        prioritized = self.prioritize_items(items, item_type)

        # 이미 검증된 항목 수
        verified_count = sum(
            1 for item in items
            if item.get('verification_status', 'pending') != 'pending'
        )

        return {
            'total': len(items),
            'verified': verified_count,
            'pending': len(items) - verified_count,
            'critical': len(prioritized[Priority.CRITICAL]),
            'high': len(prioritized[Priority.HIGH]),
            'medium': len(prioritized[Priority.MEDIUM]),
            'low': len(prioritized[Priority.LOW]),
            'auto_approve_candidates': len(self.get_auto_approve_candidates(items)),
            'estimated_review_time_minutes': self._estimate_review_time(prioritized)
        }

    def _estimate_review_time(
        self,
        prioritized: Dict[Priority, List[VerificationItem]]
    ) -> float:
        """예상 검토 시간 (분)"""
        # 항목당 예상 시간 (초)
        time_per_item = {
            Priority.CRITICAL: 30,  # 저신뢰 = 꼼꼼히 확인
            Priority.HIGH: 20,      # 연결 없음 = 관계 확인 필요
            Priority.MEDIUM: 10,    # 중간 = 빠른 검토
            Priority.LOW: 2         # 대부분 자동 승인
        }

        total_seconds = sum(
            len(items) * time_per_item[priority]
            for priority, items in prioritized.items()
        )

        return round(total_seconds / 60, 1)

    def get_training_data(
        self,
        session_id: Optional[str] = None,
        action_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        모델 재학습용 데이터 조회

        Args:
            session_id: 특정 세션만 조회 (선택)
            action_filter: 특정 액션만 조회 (선택)

        Returns:
            학습용 데이터 목록
        """
        logs = self.verification_logs

        if session_id:
            logs = [l for l in logs if l.session_id == session_id]

        if action_filter:
            logs = [l for l in logs if l.user_action == action_filter]

        return [
            {
                'item_id': log.item_id,
                'item_type': log.item_type,
                'original': log.original_data,
                'action': log.user_action,
                'modified': log.modified_data,
            }
            for log in logs
        ]


# 싱글톤 인스턴스
active_learning_service = ActiveLearningService()
