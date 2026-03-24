# S01: Arrowhead Detection — 화살촉 모폴로지 검출

> 치수선 화살촉을 모폴로지 연산으로 검출하여 "치수선 → 텍스트" 직접 매핑을 구현한다.

## 왜 이 방법인가

현재 K방법은 원 검출 → 스케일 추정 → 크기순 분류로 OD/ID/W를 간접 추론한다.
화살촉을 직접 찾으면 "이 치수 텍스트가 어디를 가리키는지"를 알 수 있다:
- 화살촉 2개 → 치수선 → 양 끝의 위치 = 측정 대상
- 치수선 근처 텍스트 = 해당 치수값
- 치수선이 원 직경 방향 → OD/ID, 수직 방향 → W

## 핵심 참고 자료

- [Dimensional Arrow Detection from CAD Drawings](https://sciresol.s3.us-east-2.amazonaws.com/IJST/Articles/2016/Issue-21/Article35.pdf) — Black Hat(실선 화살촉) + White Hat(열린 화살촉) 모폴로지. 96.65% 정확도.
- [A new approach for detection of dimensions set in mechanical drawings](https://www.sciencedirect.com/science/article/abs/pii/S0167865597000251) — 화살촉-선-텍스트 세트 검출.
- [Dimension sets detection (Habed & Boufama)](http://w3.gel.ulaval.ca/~parizeau/vi99/PDF-files/S8/paper53.pdf)

## 구현 계획

### Step 1: 화살촉 검출 (2h)

```
입력: 이진화된 도면 이미지
  → Black Hat (closing - original): 실선 삼각형 화살촉 검출
  → 면적 + 종횡비 필터: 50~500px², aspect 0.3~3.0
  → 화살촉 중심점 + 방향(각도) 추출
출력: List[(x, y, angle, type)]
```

### Step 2: 화살촉 쌍 매칭 → 치수선 복원 (2h)

```
입력: 화살촉 리스트
  → 동일 직선 위의 화살촉 쌍 찾기 (방향 ±10°, 거리 기준)
  → 쌍의 중점 + 방향 + 길이 = 치수선
  → LSD 결과와 교차 검증
출력: List[DimensionLine(start, end, midpoint, direction)]
```

### Step 3: 치수선-텍스트 매칭 (1h)

```
입력: 치수선 리스트 + OCR 텍스트 리스트
  → 각 치수선의 중점에서 가장 가까운 텍스트 bbox 찾기
  → 거리 < 치수선 길이 × 0.5 이내
출력: List[(dim_line, text_value, distance)]
```

### Step 4: OD/ID/W 분류 (1h)

```
입력: 매칭된 (치수선, 텍스트) 쌍 + 원 검출 결과
  → 치수선 방향이 원 중심을 관통 → 직경(OD/ID 후보)
  → 치수선 방향이 수직(축 방향) → W 후보
  → 직경 후보 중 최대 = OD, 차대 = ID
출력: {od, id, w}
```

### Step 5: 통합 + 배치 테스트 (1h)

- `geometry_guided_extractor.py`에 새 방법 `O` (arrowhead)로 등록
- 87개 도면 배치 평가
- K방법과 결과 비교

## 예상 소요: 7시간

## 리스크

- 도면 스캔 품질이 낮으면 화살촉이 모폴로지로 검출 안 될 수 있음
- 열린 화살촉(>---<)과 닫힌 화살촉(▶---◀)이 혼재하면 둘 다 처리 필요
- 참조선(leader line)의 화살촉과 치수선 화살촉 구분 필요

## 성공 기준

- GT가 있는 도면에서 화살촉 검출률 > 80%
- 치수선-텍스트 매칭 정확도 > 70%
- OD/ID 분류에서 K방법보다 동등 또는 향상
