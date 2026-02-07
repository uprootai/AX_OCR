"""
Weighted Voting Library
가중 투표를 통한 다중 소스 결과 병합 공통 라이브러리

사용 사례:
- OCR 앙상블 (여러 OCR 엔진 결과 병합)
- 치수 인식 (여러 치수 인식 엔진 결과 병합)
- 객체 검출 (여러 모델 결과 병합)

패턴:
1. 유사 항목 클러스터링 (IoU 또는 텍스트 유사도)
2. 가중 투표 (weight × confidence)
3. 합의 보너스 (다수 소스 동의 시)
4. 대표 결과 선택
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from collections import defaultdict
import re

T = TypeVar('T')


@dataclass
class VotingCandidate(Generic[T]):
    """투표 후보 아이템"""
    item: T                          # 원본 아이템
    value: str                       # 비교용 정규화 값
    confidence: float                # 신뢰도 (0.0 ~ 1.0)
    source: str                      # 소스 식별자 (엔진명)
    weight: float = 1.0              # 소스별 가중치
    bbox: Optional[Dict[str, int]] = None  # 바운딩 박스 (선택)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 추가 메타데이터


@dataclass
class VotingResult(Generic[T]):
    """투표 결과"""
    value: str                       # 최종 선택된 값
    confidence: float                # 최종 신뢰도 (합의 보너스 포함)
    sources: List[str]               # 이 값을 선택한 소스들
    vote_score: float                # 총 득표 점수
    agreement_bonus: float           # 합의 보너스
    representative: Optional[T]      # 대표 원본 아이템
    candidates: List[VotingCandidate[T]]  # 클러스터 내 모든 후보


class WeightedVoter(Generic[T]):
    """
    가중 투표 수행자

    사용 예:
        voter = WeightedVoter[OCRResult](
            weights={"paddleocr": 0.35, "tesseract": 0.25},
            agreement_bonus_per_source=0.05,
            max_agreement_bonus=0.15
        )

        results = voter.vote(candidates, cluster_fn=text_similarity_cluster)
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        default_weight: float = 0.25,
        agreement_bonus_per_source: float = 0.05,
        max_agreement_bonus: float = 0.15,
    ):
        """
        Args:
            weights: 소스별 가중치 (예: {"paddleocr": 0.35, "tesseract": 0.25})
            default_weight: 가중치가 없는 소스의 기본값
            agreement_bonus_per_source: 소스당 합의 보너스
            max_agreement_bonus: 최대 합의 보너스
        """
        self.weights = weights or {}
        self.default_weight = default_weight
        self.agreement_bonus_per_source = agreement_bonus_per_source
        self.max_agreement_bonus = max_agreement_bonus

    def get_weight(self, source: str, context: Optional[str] = None) -> float:
        """소스별 가중치 조회 (context로 상황별 가중치 지원)"""
        if context:
            key = f"{source}:{context}"
            if key in self.weights:
                return self.weights[key]
        return self.weights.get(source, self.default_weight)

    def vote(
        self,
        candidates: List[VotingCandidate[T]],
        cluster_fn: Optional[Callable[[List[VotingCandidate[T]]], List[List[VotingCandidate[T]]]]] = None,
    ) -> List[VotingResult[T]]:
        """
        가중 투표 수행

        Args:
            candidates: 투표 후보 목록
            cluster_fn: 클러스터링 함수 (기본: 값 기반 그룹화)

        Returns:
            투표 결과 목록 (신뢰도 내림차순)
        """
        if not candidates:
            return []

        # 클러스터링
        if cluster_fn:
            clusters = cluster_fn(candidates)
        else:
            clusters = self._default_cluster(candidates)

        # 각 클러스터에서 투표
        results: List[VotingResult[T]] = []
        for cluster in clusters:
            result = self._vote_in_cluster(cluster)
            if result:
                results.append(result)

        # 신뢰도 내림차순 정렬
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results

    def _default_cluster(
        self, candidates: List[VotingCandidate[T]]
    ) -> List[List[VotingCandidate[T]]]:
        """기본 클러스터링: 정규화 값이 같은 항목끼리 그룹화"""
        groups: Dict[str, List[VotingCandidate[T]]] = defaultdict(list)
        for c in candidates:
            groups[c.value].append(c)
        return list(groups.values())

    def _vote_in_cluster(
        self, cluster: List[VotingCandidate[T]]
    ) -> Optional[VotingResult[T]]:
        """단일 클러스터 내 투표"""
        if not cluster:
            return None

        if len(cluster) == 1:
            c = cluster[0]
            return VotingResult(
                value=c.value,
                confidence=c.confidence,
                sources=[c.source],
                vote_score=c.weight * c.confidence,
                agreement_bonus=0.0,
                representative=c.item,
                candidates=cluster,
            )

        # 값별 투표 집계
        value_votes: Dict[str, float] = {}
        value_sources: Dict[str, List[str]] = {}
        value_candidates: Dict[str, List[VotingCandidate[T]]] = {}

        for c in cluster:
            weight = self.get_weight(c.source, c.metadata.get("context"))
            vote = weight * c.confidence
            value_votes[c.value] = value_votes.get(c.value, 0.0) + vote
            value_sources.setdefault(c.value, []).append(c.source)
            value_candidates.setdefault(c.value, []).append(c)

        # 최고 득표 값 선택
        best_value = max(value_votes, key=lambda v: value_votes[v])
        unique_sources = list(set(value_sources[best_value]))

        # 합의 보너스 계산
        agreement_bonus = min(
            len(unique_sources) * self.agreement_bonus_per_source,
            self.max_agreement_bonus
        )

        # 대표 후보 선택 (최고 신뢰도)
        best_candidates = value_candidates[best_value]
        representative = max(best_candidates, key=lambda c: c.confidence)

        # 최종 신뢰도
        final_confidence = min(representative.confidence + agreement_bonus, 1.0)

        return VotingResult(
            value=best_value,
            confidence=final_confidence,
            sources=unique_sources,
            vote_score=value_votes[best_value],
            agreement_bonus=agreement_bonus,
            representative=representative.item,
            candidates=cluster,
        )


# ========================================
# 클러스터링 헬퍼 함수
# ========================================

def create_iou_cluster_fn(
    iou_threshold: float = 0.5,
    get_bbox: Optional[Callable[[VotingCandidate], Optional[Dict[str, int]]]] = None,
) -> Callable[[List[VotingCandidate]], List[List[VotingCandidate]]]:
    """
    IoU (Intersection over Union) 기반 클러스터링 함수 생성

    Args:
        iou_threshold: IoU 임계값 (0.0 ~ 1.0)
        get_bbox: bbox 추출 함수 (기본: candidate.bbox)

    Returns:
        클러스터링 함수
    """
    def compute_iou(
        bbox1: Optional[Dict[str, int]],
        bbox2: Optional[Dict[str, int]]
    ) -> float:
        """두 bbox의 IoU 계산"""
        if not bbox1 or not bbox2:
            return 0.0

        x1_1, y1_1 = bbox1.get('x', 0), bbox1.get('y', 0)
        x2_1, y2_1 = x1_1 + bbox1.get('width', 0), y1_1 + bbox1.get('height', 0)

        x1_2, y1_2 = bbox2.get('x', 0), bbox2.get('y', 0)
        x2_2, y2_2 = x1_2 + bbox2.get('width', 0), y1_2 + bbox2.get('height', 0)

        # Intersection
        ix1, iy1 = max(x1_1, x1_2), max(y1_1, y1_2)
        ix2, iy2 = min(x2_1, x2_2), min(y2_1, y2_2)

        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0

        intersection = (ix2 - ix1) * (iy2 - iy1)

        # Union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def cluster_fn(candidates: List[VotingCandidate]) -> List[List[VotingCandidate]]:
        if not candidates:
            return []

        used = set()
        clusters: List[List[VotingCandidate]] = []

        for i, c1 in enumerate(candidates):
            if i in used:
                continue

            cluster = [c1]
            used.add(i)
            bbox1 = get_bbox(c1) if get_bbox else c1.bbox

            for j in range(i + 1, len(candidates)):
                if j in used:
                    continue

                c2 = candidates[j]
                bbox2 = get_bbox(c2) if get_bbox else c2.bbox

                if compute_iou(bbox1, bbox2) > iou_threshold:
                    cluster.append(c2)
                    used.add(j)

            clusters.append(cluster)

        return clusters

    return cluster_fn


def create_text_similarity_cluster_fn(
    similarity_threshold: float = 0.7,
    normalize_fn: Optional[Callable[[str], str]] = None,
) -> Callable[[List[VotingCandidate]], List[List[VotingCandidate]]]:
    """
    텍스트 유사도 기반 클러스터링 함수 생성

    Args:
        similarity_threshold: 유사도 임계값 (0.0 ~ 1.0)
        normalize_fn: 텍스트 정규화 함수

    Returns:
        클러스터링 함수
    """
    def default_normalize(text: str) -> str:
        """기본 정규화: 소문자, 공백 정리"""
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        return text

    def jaccard_similarity(t1: str, t2: str) -> float:
        """Jaccard 유사도 계산"""
        if t1 == t2:
            return 1.0

        set1 = set(t1)
        set2 = set(t2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    norm = normalize_fn or default_normalize

    def cluster_fn(candidates: List[VotingCandidate]) -> List[List[VotingCandidate]]:
        if not candidates:
            return []

        used = set()
        clusters: List[List[VotingCandidate]] = []

        for i, c1 in enumerate(candidates):
            if i in used:
                continue

            cluster = [c1]
            used.add(i)
            text1 = norm(c1.value)

            for j in range(i + 1, len(candidates)):
                if j in used:
                    continue

                c2 = candidates[j]
                text2 = norm(c2.value)

                if jaccard_similarity(text1, text2) >= similarity_threshold:
                    cluster.append(c2)
                    used.add(j)

            clusters.append(cluster)

        return clusters

    return cluster_fn


# ========================================
# 텍스트 정규화 헬퍼
# ========================================

def normalize_dimension_value(text: str) -> str:
    """치수 값 정규화 (치수 인식용)"""
    text = text.strip()
    # 소문자 변환 (단위 제외)
    text = re.sub(r'[oO]', '0', text)  # O → 0
    text = re.sub(r'[lI](?=\d)', '1', text)  # l/I → 1 (숫자 앞)
    # 특수 문자 통일
    text = re.sub(r'[×xX]', '×', text)  # 곱셈 기호 통일
    text = re.sub(r'[ØφΦ⌀]', 'Ø', text)  # 직경 기호 통일
    text = re.sub(r'±', '±', text)  # ± 기호 통일
    # 공백 정리
    text = re.sub(r'\s+', '', text)
    return text


def normalize_ocr_text(text: str) -> str:
    """일반 OCR 텍스트 정규화"""
    text = text.strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text
