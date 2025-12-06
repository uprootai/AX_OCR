# OCR Ensemble: Multi-Engine Voting Methods

## 관련 논문

### 1. LMV-RPA: Large Model Voting-based RPA
- **arXiv**: [2412.17965](https://arxiv.org/abs/2412.17965)
- **제목**: LMV-RPA: Large Model Voting-based Robotic Process Automation
- **게재일**: 2024년 12월

#### 핵심 내용
단일 OCR 엔진의 한계를 해결하기 위해 다중 OCR 엔진의 출력을 통합하는 다수결 투표 메커니즘 제안.

#### 사용 OCR 엔진
- PaddleOCR
- Tesseract OCR
- EasyOCR
- DocTR

#### 성능
- 텍스트 추출 정확도: 최대 99%
- 처리 속도: 기존 대비 80% 빠름

---

### 2. Post-OCR Document Correction
- **arXiv**: [2109.06264](https://arxiv.org/abs/2109.06264)
- **제목**: Post-OCR Document Correction with Large Ensembles of Character Sequence-to-Sequence Models
- **게재**: AAAI 2022

#### 핵심 내용
문자 n-gram으로 입력 문서를 분할하고, 개별 수정을 투표 방식으로 결합하여 최종 출력 생성.

#### 성능
ICDAR 2019 post-OCR 텍스트 수정 대회 9개 언어 중 5개에서 SOTA 달성.

---

## OCR 앙상블 방법론

### 가중 투표 (Weighted Voting)
```python
def weighted_vote(results, weights):
    """
    results: 각 OCR 엔진의 결과 리스트
    weights: 각 엔진의 가중치
    """
    # 신뢰도 기반 가중 투표
    weighted_scores = {}
    for result, weight in zip(results, weights):
        for char, confidence in result:
            weighted_scores[char] = weighted_scores.get(char, 0) + confidence * weight
    return max(weighted_scores, key=weighted_scores.get)
```

### 다수결 투표 (Majority Voting)
- 가장 많이 등장한 결과 선택
- 동률 시 신뢰도가 높은 결과 선택

### 신뢰도 기반 선택
- 각 엔진의 신뢰도 점수 비교
- 가장 높은 신뢰도의 결과 선택

## AX 시스템 적용

### OCR Ensemble API (Port 5011)
4개 OCR 엔진의 가중 투표 앙상블:

| 엔진 | 가중치 | 특성 |
|------|--------|------|
| eDOCr2 | 0.35 | 도면 전문 |
| PaddleOCR | 0.30 | 다국어 |
| Tesseract | 0.20 | 안정성 |
| TrOCR | 0.15 | 손글씨 |

### 장점
- 단일 엔진 대비 높은 정확도
- 엔진별 강점 활용
- 오류 보정 효과

## 참고 자료
- LMV-RPA: https://arxiv.org/abs/2412.17965
- Post-OCR Correction: https://arxiv.org/abs/2109.06264

---
*AX OCR Ensemble은 위 연구들을 참고하여 도면 OCR에 최적화된 가중 투표 방식을 구현합니다.*
