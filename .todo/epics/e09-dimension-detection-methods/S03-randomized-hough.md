# S03: Randomized Hough Transform — 부분 호 기반 원/호 검출

> HoughCircles 대신 Randomized Hough Transform(RHT)으로 부분 호에서도 원을 검출한다.

## 왜 이 방법인가

HoughCircles는 파라미터(dp, minDist, param1, param2)가 민감하고, 부분 호(arc)를 직접 다루지 못한다.
RHT는 점 쌍 + 기울기 방향으로 원 중심을 투표하여 O(N²)에 동작하며, 부분 호를 명시적으로 처리할 수 있다.

이미 RANSAC을 3차 보강으로 추가했지만, RHT는 RANSAC과 다른 투표 기반 접근으로 상호 보완적.

## 핵심 참고 자료

- [A Fast Randomized Hough Transform for Circle/Circular Arc Recognition](https://www.researchgate.net/publication/220359931)
- [Circular arc detection based on Hough transform](https://www.sciencedirect.com/science/article/abs/pii/016786559580007G)
- OpenCV `HoughCircles`의 내부 구현 대비 차이점

## 구현 계획

### Step 1: RHT 원 검출 구현 (3h)

```python
def rht_circle_detect(edge_points, max_iter=500, accumulator_threshold=5):
    """
    1. 에지 포인트에서 2점 랜덤 샘플링
    2. 두 점의 접선 방향(Sobel gradient)으로 원 중심 후보 계산
    3. 어큐뮬레이터에 (cx, cy, r) 투표
    4. 임계값 이상 투표를 받은 원 추출
    """
    # Sobel로 각 에지 점의 gradient 방향 계산
    # 2점의 수직 이등분선 교차점 = 원 중심 후보
    # 어큐뮬레이터 (cx, cy 공간)에 투표
    # 피크 추출 → 원 후보
```

### Step 2: 부분 호 지원 (1h)

```
- 검출된 원 후보에 대해 호 커버리지 계산
- 360° 중 몇 도를 에지가 커버하는지 → arc_coverage
- arc_coverage > 30%이면 유효 (부분 호도 허용)
- 복수 부분 호가 같은 원을 가리키면 병합
```

### Step 3: 기존 원 검출과 앙상블 (1h)

```
- Contour + fitEllipse (1차)
- HoughCircles (2차)
- RANSAC (3차)
- RHT (4차) ← 추가
- 4가지 결과 중복 제거 후 앙상블
```

### Step 4: 배치 테스트 (1h)

- RHT 단독 vs 기존 원 검출 비교
- RHT + 기존 앙상블 vs 기존 단독 비교
- 원 검출 정확도(중심 편차, 반지름 오차) 측정

## 예상 소요: 6시간

## RANSAC과의 차이

| 항목 | RANSAC | RHT |
|------|--------|-----|
| 접근 | 3점 샘플 → 모델 → inlier 검증 | 2점 + gradient → 투표 |
| 복잡도 | O(N) per iteration | O(1) per iteration |
| 부분 호 | 간접 (inlier ratio) | 직접 (arc coverage) |
| 다중 원 | 순차 제거 필요 | 어큐뮬레이터에서 피크 추출 |

## 리스크

- gradient 계산이 스캔 노이즈에 민감
- 어큐뮬레이터 해상도(bin size) 튜닝 필요
- 기존 3차 보강과 중복될 수 있음

## 성공 기준

- 원 중심 편차: T5에서 194px → 100px 이하로 개선
- 부분 호(arc_coverage < 50%)에서도 원 검출 성공
- 기존 대비 처리 시간 증가 < 2초
