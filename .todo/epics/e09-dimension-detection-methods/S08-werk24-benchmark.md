# S08: Werk24 API 벤치마크 — 상용 솔루션 기준선

> Werk24 상용 API로 DSE 도면을 분석하여 자체 방법론의 벤치마크 기준선을 확보한다.

## 왜 이 방법인가

자체 방법(K~Q)의 정확도를 평가하려면 신뢰할 수 있는 기준이 필요하다.
Werk24는 engineering drawing AI 분야의 상용 리더로, >95% 정확도를 주장한다.

이 벤치마크의 목적:
1. GT 라벨이 없는 도면에서 Werk24 결과를 준 GT로 활용
2. 자체 방법의 상대적 성능 파악
3. Werk24가 못 맞추는 케이스 = 근본적으로 어려운 도면 식별

## 핵심 참고 자료

- [Werk24 API](https://werk24.io/) — AI Feature Extraction for Engineering Drawings
- [werk24-python SDK](https://github.com/W24-Service-GmbH/werk24-python) — Python async client
- [Werk24 API Docs](https://werk24.io/docs/)

## 구현 계획

### Step 1: API 키 확보 + SDK 설치 (1h)

```bash
pip install werk24
# Free tier: 월 50건 (충분)
# 또는 trial 요청
```

### Step 2: 배치 분석 스크립트 (2h)

```python
import werk24
from werk24.models.ask import W24AskVariantDimensions

async def analyze_drawing(filepath):
    async with werk24.Client() as client:
        drawing = await client.read_drawing(filepath)
        asks = [W24AskVariantDimensions()]
        result = await client.ask(drawing, asks)
        return {
            "dimensions": result.dimensions,
            "tolerances": result.tolerances,
            "threads": result.threads,
        }
```

### Step 3: 결과 비교 매트릭스 (2h)

```
87개 도면 중 50건 분석 (무료 제한 또는 비용 고려)
각 도면에서:
  - Werk24 결과: OD, ID, W + 기타 치수
  - 자체 K방법 결과
  - 일치 여부 + 불일치 원인 분석
```

### Step 4: GT 보강 (1h)

```
GT가 없는 도면에서 Werk24 + K방법이 일치하는 경우:
  → 높은 신뢰도 준 GT로 등록
Werk24 ≠ K방법:
  → 수동 검증 후 GT 확정
```

## 예상 소요: 6시간

## 비용 추정

| 항목 | 비용 |
|------|------|
| Free tier | 50건/월 무료 |
| Pay-as-you-go | ~€0.5/도면 |
| 87개 전체 | ~€44 (1회성) |

## 리스크

- **API 접근**: Free tier 제한, 결제 필요할 수 있음
- **도면 포맷**: Werk24가 한국 도면 표준(KS)을 잘 처리하는지 미확인
- **결과 포맷**: Werk24 출력 스키마와 자체 OD/ID/W 매핑이 직접적이지 않을 수 있음
- **네트워크 의존**: 외부 API → 네트워크 지연, 보안 검토 필요

## 성공 기준

- 50개 이상 도면 분석 완료
- Werk24 vs K방법 일치율 측정
- GT 미등록 도면 20개 이상에 준 GT 확보
