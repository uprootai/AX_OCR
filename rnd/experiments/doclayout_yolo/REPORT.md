# DocLayout-YOLO 테스트 리포트

> **테스트 일시**: 2025-12-31
> **모델**: doclayout_yolo_docstructbench_imgsz1024.pt
> **GPU**: NVIDIA RTX 3080 8GB

---

## 1. 테스트 요약

| 항목 | 결과 |
|------|------|
| **설치** | ✅ 성공 (`pip install doclayout-yolo`) |
| **모델 로드** | ✅ Hugging Face에서 자동 다운로드 |
| **GPU 사용량** | ~4GB VRAM |
| **추론 속도** | 36-162ms/이미지 (1024px) |
| **테스트 이미지** | 6개 (기계도면 2, P&ID 2, 청사진 2) |

---

## 2. 검출 결과

### 2.1 기본 클래스 (DocStructBench 모델)

```
{
  0: 'title',
  1: 'plain text',
  2: 'abandon',      # 무시 영역
  3: 'figure',       # 그림/다이어그램
  4: 'figure_caption',
  5: 'table',
  6: 'table_caption',
  7: 'table_footnote',
  8: 'isolate_formula',
  9: 'formula_caption'
}
```

### 2.2 이미지별 검출 결과

| 이미지 | figure | table | abandon | 추론 시간 |
|--------|--------|-------|---------|----------|
| sample2_interm_shaft.jpg | 3 | 1 | 0 | 1.90s (초기 로드) |
| sample3_s60me_shaft.jpg | 3 | 1 | 0 | 0.07s |
| sample6_pid_diagram.png | 1 | 0 | 0 | 0.22s |
| bwms_pid_sample.png | 1 | 0 | 1 | 0.09s |
| sample8_blueprint_31.jpg | 2 | 0 | 3 | 0.06s |
| img_00031.jpg | 2 | 0 | 3 | 0.05s |

### 2.3 검출 분석

**기계 도면 (sample2, sample3)**:
- ✅ 여러 뷰를 개별 figure로 정확하게 분리
- ✅ 타이틀 블록을 table로 검출
- 메인 뷰, 단면도, 상세도를 구분

**P&ID 도면 (sample6, bwms_pid)**:
- P&ID 전체를 하나의 figure로 검출
- 타이틀 블록은 abandon으로 분류 (개선 필요)

**청사진 (sample8, img_00031)**:
- 심볼 영역을 abandon으로 검출
- 메인 다이어그램을 figure로 검출

---

## 3. 성능 분석

### 3.1 GPU 메모리 사용량

```
테스트 전: ~2.5GB
테스트 중: ~4.0GB
최대 사용: ~4.5GB (1024px 이미지)
```

**결론**: RTX 3080 8GB에서 **충분히 사용 가능** ✅

### 3.2 추론 속도

| 해상도 | 속도 |
|--------|------|
| 736x1024 | 36-44ms |
| 768x1024 | 100ms |
| 1024x1024 | 43-47ms |

**결론**: 실시간 처리 가능 (~20-30 FPS)

---

## 4. 한계점 및 개선 방안

### 4.1 현재 한계점

1. **문서 기반 학습**: 기존 모델은 논문/책 레이아웃 학습
2. **클래스 불일치**: 도면 전용 클래스 없음 (title_block, bom_table, main_view 등)
3. **P&ID 특화 부족**: P&ID 영역 세분화 어려움

### 4.2 개선 방안

#### Option A: Fine-tuning (권장) ⭐

```python
# 도면 전용 클래스로 fine-tuning
names:
  0: title_block       # 타이틀 블록
  1: revision_table    # 리비전 표
  2: bom_table         # BOM 표
  3: main_view         # 메인 뷰
  4: section_view      # 단면도
  5: detail_view       # 상세도
  6: notes_area        # 노트 영역
  7: dimension_area    # 치수 영역
  8: tolerance_block   # 공차 블록
  9: stamp_area        # 승인 영역
```

**예상 작업량**:
- 어노테이션: 500-1000 이미지
- 학습 시간: 3-6시간 (RTX 3080)
- 예상 정확도: mAP 85%+

#### Option B: 현재 모델 + 후처리

```python
# 클래스 매핑으로 활용
CLASS_MAP = {
    'figure': ['main_view', 'section_view', 'detail_view'],
    'table': ['title_block', 'bom_table', 'revision_table'],
    'abandon': ['noise', 'border'],
}
```

**장점**: 즉시 사용 가능
**단점**: 세분화 불가

---

## 5. 시스템 통합 방안

### 5.1 Blueprint AI BOM 통합

```
현재 파이프라인:
  이미지 → YOLO(심볼) → OCR(치수) → BOM

개선된 파이프라인:
  이미지 → DocLayout-YOLO(영역분할) → 영역별 처리
           ↓
    ┌──────┴──────┐
    │             │
  main_view    bom_table
    ↓             ↓
  YOLO+OCR     Table OCR
```

### 5.2 VLM 영역 세분화와 비교

| 방식 | 속도 | 정확도 | 비용 |
|------|------|--------|------|
| VLM (GPT-4o) | ~3-5초 | 높음 | 유료 API |
| DocLayout-YOLO | ~0.1초 | 중간 | 무료/로컬 |
| **하이브리드** | ~0.5초 | 높음 | 최적 |

**하이브리드 전략**:
1. DocLayout-YOLO로 빠른 초기 분할
2. 신뢰도 낮은 영역만 VLM으로 검증

---

## 6. 결론 및 권장 사항

### 6.1 현재 상태 평가

| 항목 | 점수 | 비고 |
|------|------|------|
| 설치 용이성 | ⭐⭐⭐⭐⭐ | pip install 한 줄 |
| GPU 효율성 | ⭐⭐⭐⭐⭐ | 4GB로 충분 |
| 추론 속도 | ⭐⭐⭐⭐⭐ | 실시간 가능 |
| 기계도면 적합성 | ⭐⭐⭐⭐ | Fine-tuning 필요 |
| P&ID 적합성 | ⭐⭐⭐ | 추가 학습 필요 |

### 6.2 권장 다음 단계

1. **즉시 적용 가능**:
   - 기계 도면의 뷰 분리 (figure 기준)
   - 타이틀 블록 검출 (table → title_block)

2. **중기 과제** (2-4주):
   - 도면 전용 데이터셋 구축 (500+ 이미지)
   - DocLayout-YOLO Fine-tuning
   - Blueprint AI BOM 통합

3. **장기 참조**:
   - DocLayout-YOLO 2501 업데이트 모니터링
   - P&ID 전용 레이아웃 모델 검토

---

## 7. 참조

- [DocLayout-YOLO GitHub](https://github.com/opendatalab/DocLayout-YOLO)
- [PyPI: doclayout-yolo](https://pypi.org/project/doclayout-yolo/)
- [Hugging Face: juliozhao/DocLayout-YOLO-DocStructBench](https://huggingface.co/juliozhao/DocLayout-YOLO-DocStructBench)

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2025-12-31
