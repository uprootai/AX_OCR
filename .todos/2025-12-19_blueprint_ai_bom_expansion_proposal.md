# Blueprint AI BOM 확장 제안서 (v2 - 전면 재검토)

> 작성일: 2025-12-19 | 상태: 기획 검토 단계 | 버전: 2.0 (재검토 완료)

---

## 0. 재검토 요약

### 0.1 조사 수행 내역

| 조사 영역 | 주요 출처 | 핵심 발견 |
|----------|----------|----------|
| 도면 AI 분석 | [Springer AI Review 2024](https://link.springer.com/article/10.1007/s10462-024-10779-2) | 심볼+텍스트+연결 통합이 표준 |
| P&ID 인식 | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0957417421007661) | 94% 심볼, 97% 텍스트 위치 정확도 |
| VLM 성능 | [Springer AI Review 2025](https://link.springer.com/article/10.1007/s10462-025-11290-y) | 환각율 43-72%, 정밀 분석 부적합 |
| GD&T 자동화 | [J. of Intelligent Manufacturing 2025](https://link.springer.com/article/10.1007/s10845-025-02669-3) | 자동 추출로 검사 시간 50% 단축 가능 |
| Document AI | [ACL 2024 DocLLM](https://aclanthology.org/2024.acl-long.463/) | 레이아웃 인식 LLM이 16개 중 14개 데이터셋에서 SOTA |
| GNN 도면 분석 | [VectorGraphNET 2024](https://arxiv.org/html/2410.01336v1) | 그래프 기반 관계 학습 FloorplanCAD SOTA |
| Active Learning | [Human-in-the-Loop ML](https://link.springer.com/article/10.1007/s10462-022-10246-w) | 라벨링 비용 10x 감소 가능 |

### 0.2 검토된 대안 접근법

| 접근법 | 장점 | 단점 | 결론 |
|--------|------|------|------|
| **End-to-End VLM** | 단일 모델, 구현 단순 | 환각율 43-72%, 정밀도 부족 | 초기 분류에만 활용 |
| **Graph Neural Network** | 관계 학습 최적화 | PDF 필요, 구현 복잡 | 장기 검토 |
| **LayoutLM/DocFormer** | 문서 이해 SOTA | 도면 특화 아님 | OCR 후처리에 참고 |
| **Modular Pipeline** | 검증된 성능, 오프라인 가능 | 오케스트레이션 복잡 | **채택 (개선 포함)** |

### 0.3 핵심 개선 포인트

| 기존 제안 | 문제점 | 개선안 |
|----------|--------|--------|
| 사용자 프리셋 선택 | 선택 오류 가능 | VLM 자동 분류 + 사용자 확인 |
| 단순 근접성 관계 추출 | 정확도 ~60% 예상 | 치수선 추적 기반 관계 추출 |
| 순차 검증 | 비효율적 | Active Learning (저신뢰 우선) |
| 일회성 검증 | 모델 개선 없음 | 검증 → 모델 피드백 루프 |

---

## 1. 현재 상태 분석

### 1.1 현재 Blueprint AI BOM 기능

```
입력: 이미지 + YOLO 검출 결과
처리: Human-in-the-Loop 검증 (승인/거부/수정/추가)
출력: 부품 명세서 (BOM)
```

**한계:**
- 심볼 검출만 지원 (YOLO 기반)
- 치수/공차 OCR 미지원
- 선/연결 분석 미지원
- 텍스트 블록 추출 미지원

### 1.2 문제 정의

파나시아 POC 확장 시 필요한 분석:
- **치수 OCR**: 길이, 직경, 공차 등 수치 추출
- **선 인식**: 배관, 연결선 검출
- **텍스트 블록**: 태그 번호, 주석, 표제란

---

## 2. 업계 최신 동향 분석

### 2.1 P&ID 인식 현황 (산업 적용 수준)

[Microsoft ISE 블로그](https://devblogs.microsoft.com/ise/engineering-document-pid-digitization/) 및 [SymphonyAI](https://www.symphonyai.com/industrial/piping-instrumentation-diagrams-ingestion/) 사례:

```
표준 파이프라인:
  전처리 (정렬, 테두리 제거)
    → 심볼 검출 (YOLOv5 + SE, 94.52%)
    → 텍스트 검출 (CRAFT, 97.26%)
    → 라인 검출 (별도 모델, 92.9%)
    → 연결성 분석
    → Human-in-the-Loop 검증
```

**핵심 수치:**
- 심볼 인식: 94.52% precision, 93.27% recall
- 텍스트 위치: 97.26% precision, 90.27% recall
- 학습 데이터: 75K 심볼, 10K 텍스트, 90K 라인

### 2.2 VLM (Vision Language Model) 한계

[Springer 2025 평가](https://link.springer.com/article/10.1007/s10462-025-11290-y):

| 모델 | 환각율 | 평가 |
|------|--------|------|
| GPT-4o | 43% | 가장 낮음 |
| Claude 3.5 Sonnet | 50% | 중간 |
| Gemini 1.5 Pro | 72% | 높음 |

**결론:** "only models trained with precise alignment between visual and structured data can succeed"
→ VLM은 초기 분류/가이드에만 활용, 정밀 분석은 전문 모델 필요

### 2.3 GD&T 자동 추출 현황

[Journal of Intelligent Manufacturing 2025](https://link.springer.com/article/10.1007/s10845-025-02669-3):

- YOLOv11, Faster R-CNN, RetinaNet 비교 연구
- "자동 GD&T 추출로 검사 시간 50% 단축 가능"
- 현재 한계: 기본 심볼만 인식, Feature Control Frame 파싱 미완성
- 권장: DETR/RT-DETR 모델 검토, 실시간 QMS 연동

### 2.4 Graph Neural Network 접근

[VectorGraphNET (TUM 2024)](https://arxiv.org/html/2410.01336v1):

```
PDF → SVG 변환 → 그래프 구성 (벡터=노드, 관계=엣지)
    → Graph Attention Transformer
    → 라인 레벨 세그멘테이션
```

- FloorplanCAD 데이터셋 SOTA 달성
- 장점: 벡터 간 관계 자동 학습
- 단점: PDF/CAD 원본 필요 (이미지만 있으면 적용 어려움)

---

## 3. 대안 접근법 상세 분석

### 3.1 옵션 A: 기존 제안 유지 (Modular + 휴리스틱 관계)

```
YOLO → OCR → Line → 규칙기반 관계 → HITL
```

| 장점 | 단점 |
|------|------|
| 빠른 구현 | 관계 추출 정확도 한계 (~60%) |
| 검증된 개별 모델 | 복잡한 도면에서 오류 증가 |

### 3.2 옵션 B: VLM 하이브리드 (권장 추가)

```
[이미지] → VLM(GPT-4V/Claude)
         → "기계부품도, 주요 치수 영역: 상단/우측"
         → 해당 영역에 OCR 집중
         → 전문 모델 분석
         → HITL 검증
```

| 장점 | 단점 |
|------|------|
| VLM의 전체 이해력 활용 | VLM API 비용 |
| 전문 모델의 정밀도 유지 | 온라인 의존 (오프라인 모드 별도 필요) |

### 3.3 옵션 C: Two-Stage Detection (P&ID 연구 기반)

```
Stage 1: 영역 분류 (도면영역 / 표제란 / BOM테이블)
Stage 2: 영역별 특화 모델
         - 도면영역 → YOLO + OCR
         - 표제란 → OCR(메타데이터)
         - BOM테이블 → 테이블 파서
```

| 장점 | 단점 |
|------|------|
| 영역별 최적화 | 영역 분류 모델 필요 |
| P&ID 연구에서 검증됨 | 추가 모델 학습 비용 |

### 3.4 옵션 D: 치수선 기반 관계 추출 (핵심 개선)

```
기존: 치수 텍스트와 심볼의 단순 거리 계산
개선: 치수선(dimension line) 검출 → 화살표 방향으로 대상 추론

치수 "Ø50" ─────────────▷ 원형 영역
         (치수선 추적)     (대상 객체)
```

| 장점 | 단점 |
|------|------|
| 관계 정확도 대폭 향상 (60→85%+) | 치수선 검출 모델 필요 |
| 도면 표준 방식 준수 | 손상된 도면에서 성능 저하 |

### 3.5 옵션 E: Active Learning 통합

```
검출 결과 → 신뢰도 점수 부여 → 저신뢰 우선 검증 큐
         → 사용자 검증 → 결과 로깅 → 모델 개선
```

[Human-in-the-Loop ML 연구](https://link.springer.com/article/10.1007/s10462-022-10246-w):
- 라벨링 비용 최대 10x 감소
- 모델 불확실 샘플 집중 → 효율적 개선

---

## 4. 최종 권장 아키텍처 (v2)

### 4.1 수정된 시스템 구조

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Blueprint AI BOM v2 아키텍처                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [이미지 입력]                                                       │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Stage 0: VLM 초기 분석 (선택적, 온라인 시)                    │    │
│  │  • 도면 유형 자동 분류 (기계도면 95% 확률)                    │    │
│  │  • 주요 분석 영역 식별                                       │    │
│  │  • 분석 전략 추천 → 프리셋 자동 적용                         │    │
│  │  • 사용자 확인/변경 가능                                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Stage 1: 영역 분할                                           │    │
│  │  • 도면 영역 (메인 분석 대상)                                 │    │
│  │  • 표제란 (Title Block) → 메타데이터 추출                    │    │
│  │  • BOM 테이블 (있는 경우) → 테이블 파싱                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Stage 2: 병렬 요소 검출                                       │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │    │
│  │  │ YOLO 심볼    │ │ OCR 치수     │ │ Line 검출    │          │    │
│  │  │ (94%+)      │ │ (90%+)       │ │ (92%+)       │          │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘          │    │
│  │  ┌──────────────┐ ┌──────────────┐                           │    │
│  │  │ GD&T 파서   │ │ 텍스트 블록  │                           │    │
│  │  │ (공차 기호) │ │ (태그, 주석) │                           │    │
│  │  └──────────────┘ └──────────────┘                           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Stage 3: 관계 추출 (핵심 개선)                                │    │
│  │  • 치수선 추적 기반 치수-객체 연결 (기존 근접성→치수선)       │    │
│  │  • 연결선 분석 심볼-심볼 연결                                │    │
│  │  • 태그 패턴 매칭 레이블-객체 연결                           │    │
│  │  • 각 관계에 신뢰도 점수 부여                                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Stage 4: Human-in-the-Loop + Active Learning                 │    │
│  │  • 저신뢰 항목 우선 검증 큐 (Active Learning)                │    │
│  │  • 통합 검증 UI (심볼/치수/연결 한 화면)                     │    │
│  │  • 관계 편집 (드래그&드롭)                                   │    │
│  │  • 검증 결과 로깅 → 모델 개선 피드백                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │                                                              │
│       ▼                                                              │
│  [구조화된 출력]                                                     │
│  • BOM (부품 명세서)                                                │
│  • 치수 테이블 (Excel/CSV)                                          │
│  • 연결 다이어그램 (Mermaid/SVG)                                    │
│  • 공차 분석 리포트                                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 기존 제안 대비 개선 요약

| 단계 | 기존 제안 | v2 개선 | 기대 효과 |
|------|----------|---------|----------|
| 도면 분류 | 사용자 수동 선택 | VLM 자동 + 확인 | UX 개선, 오류 방지 |
| 영역 처리 | 전체 이미지 일괄 | 영역 분할 후 특화 | 노이즈 감소 |
| 관계 추출 | 단순 근접성 | 치수선 추적 | 정확도 60→85% |
| 검증 순서 | 순차 처리 | Active Learning | 효율 +30% |
| 피드백 | 일회성 | 모델 개선 루프 | 지속적 향상 |

### 4.3 치수선 기반 관계 추출 상세

**기존 방식 (근접성):**
```python
# 문제: 치수 "Ø50"이 여러 객체와 가까울 때 잘못 연결
for dim in dimensions:
    for sym in symbols:
        if distance(dim.bbox, sym.bbox) < threshold:
            relations.append((sym, dim))  # 오연결 가능
```

**개선 방식 (치수선 추적):**
```python
# 치수선의 화살표 방향으로 대상 객체 추론
for dim in dimensions:
    # 1. 치수선 검출 (치수 텍스트와 연결된 선)
    dim_line = detect_dimension_line(dim.bbox)

    if dim_line:
        # 2. 화살표 방향으로 대상 영역 식별
        target_region = trace_arrow_direction(dim_line)

        # 3. 해당 영역의 객체와 연결
        target_object = find_object_in_region(target_region, symbols)

        if target_object:
            relations.append(Relation(
                source=target_object,
                target=dim,
                type=infer_dimension_type(dim_line.direction),
                confidence=0.95  # 치수선 있으면 높은 신뢰도
            ))
    else:
        # 폴백: 기존 근접성 방식 (낮은 신뢰도)
        nearby = find_nearby(dim.bbox, symbols)
        for sym in nearby:
            relations.append(Relation(
                source=sym,
                target=dim,
                type='unknown',
                confidence=0.60  # 근접성만 사용 시 낮은 신뢰도
            ))
```

### 4.4 Active Learning 검증 큐

```python
class ActiveLearningQueue:
    """저신뢰 항목 우선 검증"""

    def prioritize_verification(self, items: List[Detection]) -> List[Detection]:
        # 신뢰도 기준 정렬 (낮은 순)
        sorted_items = sorted(items, key=lambda x: x.confidence)

        # 검증 우선순위:
        # 1. 신뢰도 < 0.7 (필수 검증)
        # 2. 관계 연결 실패 (연결 대상 없음)
        # 3. 신뢰도 0.7-0.9 (선택 검증)
        # 4. 신뢰도 > 0.9 (자동 승인 가능)

        priority_queue = []
        for item in sorted_items:
            if item.confidence < 0.7:
                item.priority = 'critical'
            elif not item.has_relation:
                item.priority = 'high'
            elif item.confidence < 0.9:
                item.priority = 'medium'
            else:
                item.priority = 'low'
            priority_queue.append(item)

        return priority_queue

    def log_verification_result(self, item: Detection, user_action: str):
        """검증 결과 로깅 → 모델 개선 데이터"""
        log_entry = {
            'original': item.to_dict(),
            'user_action': user_action,  # approved, rejected, modified
            'timestamp': datetime.now(),
            'session_id': self.session_id
        }
        self.verification_log.append(log_entry)
```

---

## 5. 도면 유형 프리셋 (유지 + 개선)

### 5.1 프리셋 정의

#### 프리셋 1: "기계 부품도" 모드

```yaml
preset: mechanical_part
name: "기계 부품도"
description: "치수, 공차, 표면 거칠기 분석"

auto_enable:
  - edocr2           # 치수 OCR
  - dimension_line   # 치수선 검출 (NEW)
  - tolerance_parser # 공차 추출
  - surface_finish   # 표면 거칠기
  - title_block_ocr  # 표제란

relation_strategy: "dimension_line_trace"  # NEW: 치수선 기반

workflow:
  1. (VLM) 도면 유형 확인 → 기계 부품도 자동 선택
  2. 영역 분할: 도면영역 / 표제란
  3. 치수선 검출 + eDOCr2 치수 OCR
  4. 치수선 기반 관계 추출
  5. 저신뢰 항목 우선 검증 (Active Learning)
  6. 출력: 치수 테이블 + 공차 리포트

outputs:
  - dimension_table
  - tolerance_report
  - surface_specs
```

#### 프리셋 2: "P&ID/배관도" 모드

```yaml
preset: pid
name: "P&ID 배관계장도"
description: "심볼, 연결, 태그 분석"

auto_enable:
  - yolo             # P&ID 심볼 검출 (model_type=pid_class_aware)
  - line_detector    # 배관선 검출
  - paddleocr        # 태그 번호 OCR
  - pid_analyzer     # 연결성 분석

relation_strategy: "line_connection"  # 연결선 기반

workflow:
  1. (VLM) 도면 유형 확인 → P&ID 자동 선택
  2. 영역 분할: 도면영역 / 표제란 / 범례
  3. 심볼 + 라인 + 텍스트 병렬 검출
  4. 연결선 기반 관계 추출
  5. 저신뢰 항목 우선 검증
  6. 출력: BOM + 연결 다이어그램

outputs:
  - bom
  - connectivity_diagram
  - line_list
```

---

## 6. 통합 검증 UI 설계 (개선)

### 6.1 Active Learning 통합 UI

```
┌─────────────────────────────────────────────────────────────────────┐
│ 도면 유형: [✓ 기계 부품도] (VLM 자동 감지 95%) [변경]               │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                    [이미지 + 오버레이]                           │ │
│ │    - 치수: 초록 (신뢰도에 따라 진하기 조절)                       │ │
│ │    - 치수선: 파선                                               │ │
│ │    - 연결 관계: 점선                                            │ │
│ └─────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│ 검증 큐: [우선] [일반] [자동승인 후보]                               │
├─────────────────────────────────────────────────────────────────────┤
│ 🔴 우선 검증 (3건) - 신뢰도 낮음                                    │
│ ┌──────┬──────────┬────────┬──────────┬─────────┬────────────────┐ │
│ │ 상태  │ 항목      │ 값      │ 연결 대상  │ 신뢰도   │ 액션           │ │
│ ├──────┼──────────┼────────┼──────────┼─────────┼────────────────┤ │
│ │ ⚠️   │ 치수      │ Ø5?    │ 축 중앙   │ 45%     │ [수정] [삭제]  │ │
│ │ ⚠️   │ 공차      │ ±0.??  │ -        │ 52%     │ [입력] [삭제]  │ │
│ │ ⚠️   │ 치수      │ 100    │ ?        │ 68%     │ [연결] [승인]  │ │
│ └──────┴──────────┴────────┴──────────┴─────────┴────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│ 🟡 일반 검증 (12건)                                                 │
│ ┌──────┬──────────┬────────┬──────────┬─────────┬────────────────┐ │
│ │ ?    │ 치수      │ Ø80    │ 외경     │ 78%     │ [승인] [수정]  │ │
│ │ ?    │ 길이      │ 150mm  │ 전체     │ 82%     │ [승인] [수정]  │ │
│ └──────┴──────────┴────────┴──────────┴─────────┴────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│ 🟢 자동 승인 후보 (35건) - 신뢰도 90%+      [일괄 승인]              │
├─────────────────────────────────────────────────────────────────────┤
│ 현재 검증 현황: 승인 35 / 거부 1 / 대기 15 / 수동 2                  │
│ 예상 잔여 시간: ~3분 (저신뢰 3건 집중)                               │
│                                                                     │
│ [◀ 이전] [다음 ▶]                            [검증 완료]             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. 성능 예측

### 7.1 정량적 기대 효과

| 지표 | 기존 제안 | v2 개선 | 개선폭 | 근거 |
|------|----------|---------|--------|------|
| 심볼 검출 | 94% | 94% | - | YOLO 기준 유지 |
| 치수 OCR | 90% | 90% | - | eDOCr2 기준 유지 |
| **관계 추출** | 60%* | 85%+ | **+25%** | 치수선 추적 방식 |
| **검증 효율** | 기준 | +30% | **+30%** | Active Learning |
| **도면 분류** | 수동 | 자동(95%) | UX 개선 | VLM 활용 |

*60%는 단순 근접성 휴리스틱 예상치

### 7.2 정성적 기대 효과

1. **사용자 경험**: 도면 업로드 → 자동 분류 → 저신뢰 항목만 검증
2. **확장성**: 새 도면 유형 → 프리셋 추가로 대응
3. **모델 개선**: 검증 데이터 축적 → 자동 재학습 기반
4. **오프라인 지원**: VLM 없이도 프리셋 수동 선택 가능

---

## 8. 수정된 구현 로드맵

### Phase 1: 핵심 기반 (2주)

**목표:** 치수 OCR + 기본 검증 UI

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| eDOCr2 통합 | 치수 OCR 호출 | P0 |
| Dimension 모델 | 치수 데이터 스키마 | P0 |
| 다중 선택 UI | 분석 옵션 체크박스 | P0 |
| 치수 검증 UI | 목록 + 승인/수정 | P0 |
| 치수 테이블 출력 | Excel/CSV | P1 |

### Phase 2: 치수선 기반 관계 추출 (1주) - 핵심 개선

**목표:** 관계 정확도 60% → 85%

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| 치수선 검출 | Hough 변환 또는 Line Detector 확장 | P0 |
| 화살표 방향 분석 | 치수선 끝점 방향 추론 | P0 |
| 관계 생성 로직 | 치수선 → 대상 객체 연결 | P0 |
| 신뢰도 점수 | 방식별 신뢰도 차등 부여 | P1 |

### Phase 3: Active Learning 통합 (1주) - 효율 개선

**목표:** 검증 효율 +30%

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| 우선순위 큐 | 저신뢰 항목 우선 정렬 | P0 |
| UI 큐 표시 | 우선/일반/자동승인 탭 | P0 |
| 일괄 승인 | 고신뢰 항목 일괄 처리 | P1 |
| 검증 로깅 | 모델 개선용 데이터 수집 | P1 |

### Phase 4: VLM 초기 분류 (1주) - 조건부

**조건:** 온라인 API 사용 가능 시

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| VLM 호출 | GPT-4V 또는 Claude Vision | P1 |
| 도면 분류 프롬프트 | 유형 + 영역 식별 | P1 |
| 프리셋 자동 적용 | 분류 → 프리셋 매핑 | P1 |
| 오프라인 폴백 | VLM 없이 수동 선택 | P2 |

### Phase 5: 영역 분할 (1주)

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| 영역 분류 모델 | 도면/표제란/BOM테이블 | P1 |
| 영역별 처리 | 각 영역에 최적 모델 적용 | P1 |

### Phase 6: P&ID 통합 (2주)

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| Line Detector 통합 | 배관선 검출 | P0 |
| 연결성 분석 | 심볼-라인-심볼 그래프 | P0 |
| 통합 검증 UI | 탭 기반 다중 요소 | P1 |
| 연결 다이어그램 | Mermaid 출력 | P2 |

### Phase 7: GD&T 파서 (2주)

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| FCF 검출 | Feature Control Frame 영역 | P1 |
| 기호 인식 | ◎, ⌀, ⊥ 등 GD&T 심볼 | P1 |
| 값 파싱 | 공차 값 추출 | P1 |

---

## 9. 결론

### 9.1 최종 권장사항

1. **기본 방향 유지**: 모듈식 파이프라인 + 프리셋 + Human-in-the-Loop
2. **핵심 개선 3가지**:
   - 치수선 기반 관계 추출 (정확도 +25%)
   - Active Learning 검증 큐 (효율 +30%)
   - VLM 초기 분류 (UX 개선)

### 9.2 진화 경로

```
Phase 1-3 (단기): 치수 분석 + 관계 추출 + Active Learning
    → MVP로 파나시아 8507 상용화

Phase 4-5 (중기): VLM 분류 + 영역 분할
    → 다양한 도면 유형 자동 대응

Phase 6-7 (장기): P&ID 통합 + GD&T 파서
    → 완전한 도면 분석 플랫폼
```

### 9.3 참고 문헌

- [Springer: Deep learning for engineering drawings (2024)](https://link.springer.com/article/10.1007/s10462-024-10779-2)
- [Microsoft ISE: P&ID Digitization](https://devblogs.microsoft.com/ise/engineering-document-pid-digitization/)
- [ScienceDirect: P&ID Recognition (2021)](https://www.sciencedirect.com/science/article/abs/pii/S0957417421007661)
- [Springer: VLM for Engineering Design (2025)](https://link.springer.com/article/10.1007/s10462-025-11290-y)
- [VectorGraphNET (2024)](https://arxiv.org/html/2410.01336v1)
- [ACL: DocLLM (2024)](https://aclanthology.org/2024.acl-long.463/)
- [J. Intelligent Manufacturing: GD&T Detection (2025)](https://link.springer.com/article/10.1007/s10845-025-02669-3)
- [Springer: Human-in-the-Loop ML (2022)](https://link.springer.com/article/10.1007/s10462-022-10246-w)

---

*작성: Claude Code (Opus 4.5) | 버전: 2.0 | 검토 필요: 기획팀*
