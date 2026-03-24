# S04: Ellipse Decomposition — 컨투어 분해 후 호 그룹핑

> 컨투어를 호(arc)와 직선(line)으로 분해한 뒤, 동일 원에 속하는 호를 그룹핑하여 끊긴 원을 복원한다.

## 왜 이 방법인가

베어링 ASSY 도면에서 부착 부품(클램프, 브래킷)이 원 윤곽을 끊는다.
기존 `cv2.findContours`는 끊긴 윤곽을 별개 컨투어로 인식 → 원 피팅 실패.

이 방법은:
1. 컨투어를 곡률로 분석 → 호(곡선) vs 직선 세그먼트로 분해
2. 호 세그먼트의 곡률 반지름과 중심을 추정
3. 유사 반지름+중심의 호를 그룹핑 → 완전 원 복원

## 핵심 참고 자료

- [Ellipse Detection through Decomposition of Circular Arcs and Line Segments (Springer)](https://link.springer.com/chapter/10.1007/978-3-642-24085-0_57)
- [Edge curvature and convexity based ellipse detection](https://www.sciencedirect.com/science/article/abs/pii/S0031320312000763)
- 기존 `cluster_arcs_to_circles` (circle_ransac.py) — fitEllipse 기반, 이것의 고급 버전

## 구현 계획

### Step 1: 컨투어 곡률 분석 + 분해 (3h)

```python
def decompose_contour(contour, curvature_threshold=0.01):
    """
    1. 컨투어를 N점 윈도우로 슬라이딩하면서 곡률(curvature) 계산
       curvature = |d²y/dx²| / (1 + (dy/dx)²)^(3/2)
    2. 곡률 변화가 급격한 점에서 세그먼트 분할
    3. 각 세그먼트를 호(arc) 또는 직선(line)으로 분류
       - 평균 곡률 > threshold → 호
       - 평균 곡률 ≈ 0 → 직선
    4. 호 세그먼트에 원 피팅 → (cx, cy, r, arc_angle)
    """
```

### Step 2: 호 그룹핑 (2h)

```python
def group_arcs_by_circle(arcs, center_tol=0.15, radius_tol=0.10):
    """
    1. 모든 호 쌍의 (중심 거리, 반지름 차) 계산
    2. 유사한 호 → 같은 원 그룹
    3. 그룹 내 호의 총 커버 각도(arc_coverage) 계산
    4. 그룹 포인트 전체로 최종 원 피팅 (Kasa method)
    """
```

기존 `cluster_arcs_to_circles`와의 차이:
- 기존: fitEllipse → aspect ratio 필터 → greedy merge
- 개선: 곡률 분해 → 호 세그먼트 단위 → 정밀 그룹핑

### Step 3: 기존 파이프라인 통합 (1h)

```
- _detect_circles 내에서 5차 패스로 추가
- 또는 기존 cluster_arcs_to_circles를 이 방법으로 대체
- 앙상블 결과에 통합
```

### Step 4: 배치 테스트 (1h)

- 끊긴 원 복원 성공률 측정
- 원 검출 정확도(중심, 반지름) 비교

## 예상 소요: 7시간

## 리스크

- 곡률 계산이 컨투어 해상도에 민감 (포인트가 적으면 부정확)
- 타원형 형상(SECTION 단면도)을 원으로 오분류할 수 있음
- 직선-호 경계 판정 임계값 튜닝 필요

## 성공 기준

- 부착 부품이 있는 도면에서 원 복원 성공률 > 70%
- 기존 cluster_arcs_to_circles 대비 원 정확도 향상
- 처리 시간 < 3초/도면
