# DocLayout-YOLO Fine-tuning: 도면 전용 클래스 학습

> **상태**: ⏸️ 보류 (Colab 학습 예정)
> **생성일**: 2025-12-31
> **우선순위**: P1
> **예상 공수**: 1-2주 (데이터 라벨링 포함)
> **GPU 요구**: ❌ RTX 3080 8GB 불가 → **Google Colab T4 16GB 필요**

---

## 배경

### 현재 DocLayout-YOLO 테스트 결과 (2025-12-31)

| 도면 유형 | 검출 성능 | 신뢰도 | 문제점 |
|----------|----------|--------|--------|
| 기계 도면 | ✅ 양호 | 0.19~0.36 | 낮은 신뢰도 |
| P&ID | ⚠️ 제한적 | 0.94 | 전체를 하나의 figure로 검출 |
| 제어 패널 | ✅ 양호 | 0.51~0.72 | 분리 정확 |

### 문제점

1. **낮은 신뢰도**: 기계 도면에서 0.19~0.36 수준
2. **부적합한 클래스**: 일반 문서용 클래스(figure, table, title)가 도면에 최적화되지 않음
3. **P&ID 한계**: P&ID 도면 특성 미반영 (전체를 하나의 figure로 인식)

### 현재 클래스 vs 필요 클래스

| 현재 (DocStructBench) | 필요 (도면 전용) |
|----------------------|-----------------|
| figure | **main_view** (주 도면 뷰) |
| table | **bom_table** (BOM 테이블) |
| title | **title_block** (표제란) |
| abandon | **notes** (주기/노트) |
| - | **detail_view** (상세도) |
| - | **section_view** (단면도) |
| - | **legend** (범례) |
| - | **revision_block** (리비전 블록) |

---

## 핵심 아이디어

### 도면 전용 클래스 정의 (8개)

```python
DRAWING_CLASSES = {
    0: "title_block",      # 표제란 (우하단)
    1: "main_view",        # 주 도면 뷰
    2: "detail_view",      # 상세도 (Detail A, B...)
    3: "section_view",     # 단면도 (Section A-A...)
    4: "bom_table",        # BOM 테이블 / 부품 목록
    5: "notes",            # 주기 / 노트 영역
    6: "legend",           # 범례
    7: "revision_block",   # 리비전 블록 (상단)
}
```

### Fine-tuning 전략

```
┌─────────────────────────────────────────────────────────────────────┐
│  2단계 Fine-tuning 전략                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Stage 1: 클래스 매핑 학습 (소규모 데이터)                            │
│  ─────────────────────────────────────────                          │
│  • 데이터: 100-200장                                                 │
│  • 목표: 기존 클래스 → 도면 클래스 매핑                               │
│  • 방법: Transfer Learning (Head만 학습)                            │
│  • 예상 시간: 2-4시간                                                │
│                                                                     │
│  Stage 2: 전체 Fine-tuning (대규모 데이터)                           │
│  ─────────────────────────────────────────                          │
│  • 데이터: 500+ 장                                                   │
│  • 목표: 도면 특화 성능 최적화                                        │
│  • 방법: Full Fine-tuning (Backbone 포함)                           │
│  • 예상 시간: 8-16시간                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 예상 효과

### 정량적

| 지표 | 현재 | 목표 | 향상 |
|------|------|------|------|
| 신뢰도 (기계 도면) | 0.19~0.36 | **0.70+** | **2-3배** |
| 신뢰도 (P&ID) | 0.94 (단일) | **0.80+ (다중)** | 세분화 |
| Title Block 검출 | 간접 매핑 | **직접 검출** | 정확도↑ |
| VLM 폴백 필요 | ~40% | **~10%** | API 비용↓ |

### 정성적

- **도면 전문성**: 일반 문서가 아닌 기술 도면에 특화
- **세분화**: main_view → detail_view, section_view 구분 가능
- **일관성**: 도면 유형별 일관된 영역 검출
- **확장성**: 새로운 도면 유형 추가 용이

---

## 구현 방안

### Phase 1: 데이터 준비 (3-5일)

#### 1.1 라벨링 도구 선정

| 도구 | 장점 | 단점 |
|------|------|------|
| **Label Studio** | 웹 기반, 협업 가능 | 설정 복잡 |
| **CVAT** | YOLO 포맷 지원 | 무거움 |
| **Roboflow** | 자동 라벨링, 증강 | 유료 (무료 한도) |
| **LabelImg** | 간단, 오프라인 | 기능 제한 |

**추천**: Roboflow (자동 라벨링 + 데이터 증강 + YOLO 포맷 내보내기)

#### 1.2 데이터 수집 계획

| 도면 유형 | 목표 수량 | 소스 |
|----------|----------|------|
| 기계 도면 | 200장 | 기존 샘플 + 공개 데이터셋 |
| P&ID | 150장 | TECHCROSS + 공개 데이터셋 |
| 조립도 | 100장 | 기존 샘플 |
| 전기 도면 | 50장 | 기존 샘플 |
| **총계** | **500장** | |

#### 1.3 라벨링 가이드라인

```yaml
title_block:
  위치: 우하단 (일반적)
  포함: 도면번호, 제목, 척도, 날짜, 승인란

main_view:
  정의: 가장 큰/주요 도면 뷰
  특징: 치수, 주석 포함

detail_view:
  식별: "DETAIL A", "상세도 1" 텍스트
  특징: 확대된 부분 뷰

section_view:
  식별: "SECTION A-A", "단면 A-A" 텍스트
  특징: 절단면 표시

bom_table:
  위치: 우측 또는 상단
  특징: 품번, 품명, 수량 컬럼

notes:
  위치: 좌하단 (일반적)
  포함: 주기, 공차, 재료 정보

legend:
  위치: 다양
  포함: 심볼 설명, 약어 정의

revision_block:
  위치: 우상단 또는 title_block 상단
  포함: 리비전 번호, 날짜, 설명
```

### Phase 2: Fine-tuning (2-3일)

#### 2.1 환경 설정

```bash
# DocLayout-YOLO Fine-tuning 환경
pip install doclayout-yolo
pip install albumentations  # 데이터 증강

# 데이터 구조
data/
├── train/
│   ├── images/
│   └── labels/  # YOLO 포맷
├── val/
│   ├── images/
│   └── labels/
└── data.yaml
```

#### 2.2 학습 설정

```python
# fine_tune_config.py
CONFIG = {
    # 모델
    "base_model": "juliozhao/DocLayout-YOLO-DocStructBench",
    "model_size": "doclayout_yolo_docstructbench_imgsz1024.pt",

    # 학습
    "epochs": 100,
    "batch_size": 8,  # RTX 3080 8GB 기준
    "imgsz": 1024,
    "patience": 20,  # Early stopping

    # 최적화
    "optimizer": "AdamW",
    "lr0": 0.001,
    "lrf": 0.01,
    "weight_decay": 0.0005,

    # 증강
    "augment": True,
    "mosaic": 0.5,
    "mixup": 0.1,
    "degrees": 5,  # 도면은 회전 적게
    "scale": 0.3,

    # 클래스
    "nc": 8,  # 8개 도면 전용 클래스
    "names": [
        "title_block", "main_view", "detail_view", "section_view",
        "bom_table", "notes", "legend", "revision_block"
    ],
}
```

#### 2.3 학습 스크립트

```python
# train_doclayout.py
from doclayout_yolo import YOLOv10

def train():
    # 베이스 모델 로드
    model = YOLOv10.from_pretrained(
        "juliozhao/DocLayout-YOLO-DocStructBench"
    )

    # Fine-tuning
    results = model.train(
        data="data/data.yaml",
        epochs=100,
        imgsz=1024,
        batch=8,
        device=0,
        project="runs/doclayout",
        name="drawing_v1",

        # 전이 학습: 초기 레이어 고정
        freeze=10,  # 처음 10개 레이어 고정
    )

    return results

if __name__ == "__main__":
    train()
```

### Phase 3: 통합 및 검증 (1-2일)

#### 3.1 모델 교체

```python
# services/layout_analyzer.py 수정
DOCLAYOUT_MODEL = os.environ.get(
    "DOCLAYOUT_MODEL",
    "runs/doclayout/drawing_v1/weights/best.pt"  # Fine-tuned 모델
)

# 클래스 매핑 업데이트
DOCLAYOUT_TO_REGION_MAP = {
    "title_block": "TITLE_BLOCK",
    "main_view": "MAIN_VIEW",
    "detail_view": "DETAIL_VIEW",
    "section_view": "SECTION_VIEW",
    "bom_table": "BOM_TABLE",
    "notes": "NOTES",
    "legend": "LEGEND",
    "revision_block": "TITLE_BLOCK",  # revision_block은 title_block에 포함
}
```

#### 3.2 검증 테스트

```python
# tests/test_finetuned_layout.py
def test_finetuned_model():
    """Fine-tuned 모델 성능 테스트"""
    analyzer = get_layout_analyzer()

    # 테스트 이미지
    test_images = [
        "samples/mechanical_drawing.jpg",
        "samples/pid_diagram.jpg",
        "samples/assembly_drawing.jpg",
    ]

    for img in test_images:
        detections = analyzer.detect(img)

        # 신뢰도 검증
        for det in detections:
            assert det.confidence >= 0.5, f"Low confidence: {det.confidence}"

        # 필수 영역 검출 확인
        region_types = [det.region_type for det in detections]
        assert "MAIN_VIEW" in region_types
        assert "TITLE_BLOCK" in region_types
```

---

## 리스크 & 대안

### 리스크

| 리스크 | 영향 | 확률 | 대응 |
|--------|------|------|------|
| 데이터 부족 | 과적합 | 중 | 데이터 증강, 공개 데이터셋 활용 |
| 클래스 불균형 | 일부 클래스 성능↓ | 중 | 가중치 조정, 오버샘플링 |
| GPU 메모리 부족 | 학습 실패 | 낮 | batch_size 축소, gradient accumulation |
| 기존 성능 저하 | 회귀 | 낮 | A/B 테스트, 롤백 계획 |

### 대안

1. **Plan B: 클래스 매핑만 개선**
   - Fine-tuning 없이 후처리로 클래스 매핑
   - 장점: 빠른 적용
   - 단점: 근본적 개선 어려움

2. **Plan C: 다른 모델 사용**
   - LayoutLMv3, DiT 등 Transformer 기반
   - 장점: 더 정확한 레이아웃 이해
   - 단점: GPU 요구량 높음 (16GB+)

3. **Plan D: 휴리스틱 강화**
   - Fine-tuning 대신 규칙 기반 후처리 개선
   - 장점: 즉시 적용 가능
   - 단점: 일반화 어려움

---

## 검증 결과

### 사전 테스트 (2025-12-31)

기존 DocLayout-YOLO (DocStructBench) 테스트 결과:

| 도면 | 검출 | 신뢰도 | 판정 |
|------|------|--------|------|
| 기계 도면 A | main_view × 2, bom_table × 1 | 0.19~0.36 | ⚠️ 낮음 |
| 기계 도면 B | main_view × 2, bom_table × 1 | 0.21~0.33 | ⚠️ 낮음 |
| BWMS P&ID | main_view × 1 | 0.94 | ⚠️ 세분화 필요 |
| Control Panel | main_view × 2 | 0.51~0.72 | ✅ 양호 |

**결론**: Fine-tuning으로 신뢰도 0.70+ 달성 시 VLM 폴백 90% 감소 예상

---

## 다음 단계

### 즉시 실행 가능

- [ ] 라벨링 도구 선정 및 설정 (Roboflow 추천)
- [ ] 기존 샘플 이미지 수집 (web-ui/public/samples/)
- [ ] 라벨링 가이드라인 문서화

### 데이터 확보 후

- [ ] 500장 라벨링 (목표: 1주)
- [ ] Stage 1 Fine-tuning (Head만, 100장)
- [ ] Stage 2 Fine-tuning (Full, 500장)
- [ ] 성능 벤치마크 및 비교

### 검증 완료 후

- [ ] `layout_analyzer.py` 모델 교체
- [ ] 테스트 케이스 추가
- [ ] main/ 으로 승격 및 구현

---

## 참조

- DocLayout-YOLO 테스트 리포트: `rnd/experiments/doclayout_yolo/REPORT.md`
- DocLayout-YOLO 통합: `idea-thinking/main/001_doclayout_yolo_integration.md`
- SOTA Gap 분석: `rnd/SOTA_GAP_ANALYSIS.md`
- 학습 가이드: `rnd/TRAINING_GUIDES.md`

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2025-12-31
