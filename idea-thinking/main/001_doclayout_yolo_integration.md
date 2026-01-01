# DocLayout-YOLO를 Blueprint AI BOM에 통합

> **상태**: ✅ 승인 (검증 완료)
> **생성일**: 2025-12-31
> **우선순위**: P1
> **예상 공수**: 1-2일

---

## 배경

### 현재 문제점

Blueprint AI BOM의 영역 세분화(Region Segmentation)는 **휴리스틱 + VLM 하이브리드** 방식:

```
현재 파이프라인:
이미지 → VLM(GPT-4o-mini) 분류 → 휴리스틱 영역 분할 → 개별 처리
```

**문제점**:
1. VLM 호출 비용 (API 요금)
2. 휴리스틱 한계 (고정된 규칙)
3. 처리 속도 (VLM 응답 대기)

### 왜 DocLayout-YOLO인가?

| 항목 | 현재 (VLM) | DocLayout-YOLO |
|------|-----------|----------------|
| 속도 | 3-5초 | **40ms** |
| 비용 | API 요금 | **무료 (로컬)** |
| GPU | 불필요 | ~4GB |
| 정확도 | 높음 | 중간 (Fine-tuning 필요) |

---

## 핵심 아이디어

### 하이브리드 파이프라인

```
개선된 파이프라인:
이미지 → DocLayout-YOLO(빠른 영역 검출) → 신뢰도 확인
                                          ↓
                              ┌──────────────────────┐
                              │  신뢰도 > 0.8       │
                              │  → 즉시 사용        │
                              │                    │
                              │  신뢰도 < 0.8       │
                              │  → VLM 검증 폴백   │
                              └──────────────────────┘
```

### 통합 포인트

Blueprint AI BOM의 영역 세분화 모듈에 통합:

```python
# blueprint-ai-bom/backend/services/layout_analyzer.py (신규)

class LayoutAnalyzer:
    def __init__(self):
        self.doclayout = DocLayoutYOLO()  # 빠른 1차 검출
        self.vlm = VLMClient()            # 폴백 검증

    def analyze(self, image) -> List[Region]:
        # 1차: DocLayout-YOLO (40ms)
        regions = self.doclayout.detect(image)

        # 2차: 신뢰도 낮은 영역만 VLM 검증
        for region in regions:
            if region.confidence < 0.8:
                region = self.vlm.verify(image, region)

        return regions
```

---

## 예상 효과

### 정량적

| 지표 | 현재 | 개선 후 | 향상 |
|------|------|---------|------|
| 영역 검출 속도 | 3-5초 | 0.04초 | **75-125x** |
| API 호출 비용 | 100% | ~20% | **80% 절감** |
| 배치 처리량 | ~12/분 | ~300/분 | **25x** |

### 정성적

- 오프라인 동작 가능 (VLM 의존성 감소)
- 배치 처리 효율 향상
- 사용자 응답 시간 단축

---

## 구현 방안

### Phase 1: 서비스 모듈 추가 (1일)

```
blueprint-ai-bom/backend/
├── services/
│   ├── layout_analyzer.py     # 신규: DocLayout-YOLO 래퍼
│   └── ...
└── routers/
    └── analysis/
        └── region_router.py   # 수정: 새 분석기 연동
```

### Phase 2: 라우터 통합 (0.5일)

```python
# region_router.py 수정
from services.layout_analyzer import LayoutAnalyzer

analyzer = LayoutAnalyzer()

@router.post("/{session_id}/regions/detect")
async def detect_regions(session_id: str, file: UploadFile):
    image = await load_image(file)
    regions = analyzer.analyze(image)
    return {"regions": regions}
```

### Phase 3: 프론트엔드 연동 (0.5일)

기존 영역 세분화 UI에 결과 표시 (변경 최소화)

---

## 리스크 & 대안

### 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| DocLayout-YOLO 정확도 | 중 | VLM 폴백으로 보완 |
| 도면 전용 클래스 부재 | 중 | 클래스 매핑 또는 Fine-tuning |
| GPU 메모리 충돌 | 낮 | 다른 YOLO와 공유 가능 |

### 대안

1. **Plan B**: DocLayout-YOLO만 사용 (VLM 제거)
   - 장점: 비용 0
   - 단점: 정확도 하락

2. **Plan C**: Fine-tuning 후 적용
   - 장점: 최고 정확도
   - 단점: 데이터 라벨링 필요 (500+ 이미지)

---

## 검증 결과 ✅

### 테스트 완료 (2025-12-31)

```
테스트 환경: RTX 3080 8GB
테스트 이미지: 6개 (기계도면 2, P&ID 2, 청사진 2)
```

| 이미지 | 검출 결과 | 평가 |
|--------|----------|------|
| 기계 도면 | figure 3, table 1 | ✅ 뷰 분리 정확 |
| P&ID | figure 1 | ⚠️ 전체를 하나로 검출 |
| 청사진 | figure 2, abandon 3 | ⚠️ 부분 검출 |

**결론**: 기계 도면에서 효과적, P&ID는 Fine-tuning 필요

상세 결과: `rnd/experiments/doclayout_yolo/REPORT.md`

---

## 다음 단계

### 즉시 실행 (승인됨) ✅ 완료 (2025-12-31)

- [x] `layout_analyzer.py` 서비스 모듈 생성
- [x] `region_segmenter.py`에 DocLayout-YOLO 통합
- [x] 통합 테스트 실행 (10 passed)

### 향후 개선

- [ ] 도면 전용 클래스로 Fine-tuning (500+ 이미지)
- [ ] 신뢰도 임계값 최적화
- [ ] 배치 처리 최적화

---

## 참조

- DocLayout-YOLO 테스트 리포트: `rnd/experiments/doclayout_yolo/REPORT.md`
- Blueprint AI BOM 문서: `blueprint-ai-bom/docs/README.md`
- SOTA Gap 분석: `rnd/SOTA_GAP_ANALYSIS.md`

---

*작성자*: Claude Code (Opus 4.5)
*승인일*: 2025-12-31
