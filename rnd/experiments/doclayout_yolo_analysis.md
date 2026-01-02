# DocLayout-YOLO Fine-tuning 검토

> **작성일**: 2026-01-02
> **우선순위**: P1
> **상태**: 검토 완료

---

## 1. 논문 개요

- **제목**: DocLayout-YOLO: Document Layout Analysis with YOLO
- **arXiv**: [2410.12628](https://arxiv.org/abs/2410.12628)
- **날짜**: 2024-10
- **핵심 기여**:
  - YOLO 기반 문서 레이아웃 검출 특화 모델
  - DocSynth-300K: 300K 합성 문서 데이터셋
  - 글로벌+로컬 정보 융합 아키텍처
  - YOLOv8/v10/v11 백본 지원

---

## 2. 현재 시스템과의 관계

### 현재 도면 영역 검출 방식

| 컴포넌트 | 현재 방식 | 한계 |
|----------|----------|------|
| BOM 표 영역 | YOLO bom_detector | 심볼 중심, 표 구조 미인식 |
| 노트 영역 | Line Detector + VLM | 점선 박스만 검출 |
| 타이틀 블록 | VLM 휴리스틱 | 정확도 낮음 |
| 상세도/확대도 | 미구현 | - |

### DocLayout-YOLO 적용 시 개선점

| 영역 | 예상 효과 |
|------|----------|
| BOM 표 | 표 구조 + 셀 단위 검출 |
| 타이틀 블록 | 위치/크기 정확 검출 |
| 상세도/확대도 | 영역 분리 가능 |
| 개정 이력 | 개정 테이블 영역 검출 |

---

## 3. 기술적 분석

### 3.1 아키텍처 특징

```
DocLayout-YOLO
├── Backbone: YOLOv8/v10/v11 (선택 가능)
├── Feature Fusion: Global + Local Attention
├── Head: Multi-scale Detection
└── Output: 11개 문서 요소 클래스
```

### 3.2 기본 클래스 (DocLayNet 기준)

| 클래스 ID | 이름 | 도면 적용 |
|-----------|------|----------|
| 0 | Caption | 주석/노트 |
| 1 | Footnote | 하단 노트 |
| 2 | Formula | 수식 (공차?) |
| 3 | List-item | 체크리스트 |
| 4 | Page-footer | - |
| 5 | Page-header | 타이틀 블록 |
| 6 | Picture | 상세도 |
| 7 | Section-header | - |
| 8 | Table | BOM 표 |
| 9 | Text | 일반 텍스트 |
| 10 | Title | 도면 제목 |

### 3.3 도면용 커스텀 클래스 (Fine-tuning 필요)

| 클래스 ID | 이름 | 설명 |
|-----------|------|------|
| 0 | title_block | 타이틀 블록 (우하단) |
| 1 | bom_table | BOM 표 |
| 2 | revision_table | 개정 이력 표 |
| 3 | note_area | 일반 노트 영역 |
| 4 | special_note | 특수 노트 (열처리, 도장 등) |
| 5 | detail_view | 상세도/확대도 |
| 6 | section_view | 단면도 |
| 7 | auxiliary_view | 보조 투상도 |
| 8 | drawing_area | 메인 도면 영역 |
| 9 | tolerance_block | 공차 블록 |
| 10 | material_spec | 재질 사양 |

---

## 4. 구현 로드맵

### Phase 1: 평가 (1-2주)
- [ ] DocLayout-YOLO 사전학습 모델 다운로드
- [ ] TECHCROSS 도면 샘플 10장으로 기본 성능 평가
- [ ] 현재 시스템 대비 영역 검출 정확도 비교

### Phase 2: 데이터 준비 (2-4주)
- [ ] 도면용 어노테이션 가이드라인 작성
- [ ] TECHCROSS BWMS 도면 50장 수집
- [ ] CVAT/Labelbox로 어노테이션 (11개 클래스)
- [ ] Train/Val/Test 분리 (35/10/5)

### Phase 3: Fine-tuning (1-2주)
- [ ] DocLayout-YOLO 설치 및 환경 구성
- [ ] 커스텀 데이터셋 YOLO 포맷 변환
- [ ] Fine-tuning 실행 (100 epochs)
- [ ] 최적 모델 선택

### Phase 4: 통합 (1주)
- [ ] YOLO API에 model_type='doclayout' 추가
- [ ] Line Detector 또는 별도 서비스로 통합
- [ ] BlueprintFlow 노드 정의

---

## 5. 리소스 요구사항

### GPU 요구사항 (RTX 3080 8GB 기준)

| 작업 | VRAM | 시간 |
|------|------|------|
| 추론 | ~2GB | 0.1초/이미지 |
| Fine-tuning (batch=8) | ~4GB | 2시간/100epochs |
| Fine-tuning (batch=16) | ~6GB | 1.5시간/100epochs |

### 데이터 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| 학습 이미지 | 50 | 200 |
| 에폭 | 50 | 100-200 |
| 클래스당 인스턴스 | 10 | 50+ |

---

## 6. 예상 효과

### 정량적 효과

| 지표 | 현재 | 목표 |
|------|------|------|
| 영역 검출 mAP | ~50% | ~80% |
| BOM 표 검출 정확도 | 70% | 95% |
| 타이틀 블록 검출 | 60% | 90% |

### 정성적 효과

- Blueprint AI BOM의 "영역 세분화" 기능 강화
- 노트 추출 정확도 향상
- 도면 자동 분류 가능

---

## 7. 결론

**권장사항**:
1. **Phase 1 평가 먼저 진행** - 사전학습 모델로 현재 도면 테스트
2. 성능이 충분하면 즉시 통합 (Fine-tuning 없이)
3. 부족하면 50장으로 Quick Fine-tuning 진행

**대안**:
- SFDLA (Source-Free Domain Adaptation) 적용 검토 - 라벨 없이 적응 가능
- VGT (Vision Grid Transformer) - 더 정확하지만 GPU 요구량 높음

---

*작성자*: Claude Code
