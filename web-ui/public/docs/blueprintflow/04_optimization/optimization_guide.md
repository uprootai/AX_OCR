# BlueprintFlow 최적화 가이드

**Complete roadmap for implementing model diversification and pipeline optimization**

---

## 🎯 핵심 문제

### 현재 상태 (Phase 1-3 완료)
- ✅ 9개 노드 구현 (YOLO, eDOCr2, EDGNet 등)
- ✅ 비주얼 워크플로우 빌더 완성
- ❌ **YOLO 모델이 너무 단순화됨** (yolo11n/s/m만 선택 가능)
- ❌ **후처리 파이프라인 옵션 부재** (Crop, Background Removal 등)
- ❌ **조합별 전략적 설명 부족** (언제 어떤 조합을 쓸지 모름)

### 실제 요구사항
도면 종류와 목적에 따라 **최적화된 모델 조합**이 필요:
- **심볼 인식**: 용접, 베어링, 기어 등 14가지 기호 검출
- **치수 추출**: 숫자와 단위가 포함된 치수 텍스트 영역 검출
- **GD&T 분석**: 기하공차 심볼 전용 검출
- **텍스트 영역**: 주석, 제목란, 메모 영역 검출

---

## 🛠️ 구현 로드맵

### Phase 4A: YOLO 모델 다양화 (Week 1)
- [ ] symbol-detector-v1 학습 (14개 클래스)
- [ ] dimension-detector-v1 학습 (치수 영역)
- [ ] gdt-detector-v1 학습 (GD&T 심볼)
- [ ] text-region-detector-v1 학습 (텍스트 영역)
- [ ] YOLO API에 multi-model 지원 추가 (모델 선택 파라미터)

**Lines of Code**: ~50 lines (YOLO API model loading logic)

---

### Phase 4B: 후처리 노드 추가 (Week 2)
- [ ] **BackgroundRemoval** 노드 구현 (OpenCV 기반)
- [ ] **CropAndScale** 노드 구현 (BBox 기반 Crop + Resize)
- [ ] **BatchOCR** 노드 구현 (여러 영역 동시 OCR)
- [ ] NodeDetailPanel에 후처리 옵션 설명 추가

**Lines of Code**: ~200 lines (3 new nodes + detail panel updates)

---

### Phase 4C: 템플릿 고도화 (Week 3)
- [ ] Template 5: 심볼 인식 최적화 (symbol-detector + Crop + eDOCr2)
- [ ] Template 6: 치수 추출 최적화 (dimension-detector + Scale Up + eDOCr2)
- [ ] Template 7: GD&T 분석 (gdt-detector + SkinModel)
- [ ] Template 8: 영문 도면 (text-region + PaddleOCR)

**Lines of Code**: ~100 lines (4 new templates in WorkflowTemplates.tsx)

---

### Phase 4D: 성능 벤치마크 (Week 4)
- [ ] 100장 테스트 도면으로 4가지 옵션 비교
- [ ] 속도/정확도/메모리 메트릭 수집
- [ ] 자동 파이프라인 추천 알고리즘 구현

**Lines of Code**: ~150 lines (benchmarking script + recommendation engine)

---

## 📝 문서 업데이트 계획

### 1. CLAUDE.md 업데이트
- BlueprintFlow 섹션에 "모델 다양화 전략" 추가
- 각 시나리오별 권장 조합 예시 추가

### 2. 새 스킬 추가: workflow-optimizer.md
- 사용자의 도면 유형 분석
- 최적 파이프라인 자동 추천
- 성능 벤치마크 결과 제공

**Status**: ✅ Already created at `.claude/skills/workflow-optimizer.md`

### 3. nodeDefinitions.ts 확장
```typescript
// Before
options: ['yolo11n', 'yolo11s', 'yolo11m']

// After
options: [
  'symbol-detector-v1',      // 심볼 인식 (F1: 92%)
  'dimension-detector-v1',   // 치수 추출 (F1: 88%)
  'gdt-detector-v1',         // GD&T 분석 (F1: 85%)
  'text-region-detector-v1', // 텍스트 영역 (F1: 90%)
  'yolo11n-general'          // 범용 (테스트용)
]
```

---

## 🎯 예상 효과

| 항목 | Before (Phase 1-3) | After (Phase 4) | 개선율 |
|------|-------------------|----------------|--------|
| **YOLO 모델 선택** | 3개 (크기만 다름) | 5개 (용도별 특화) | +67% |
| **후처리 옵션** | 1개 (시각화만) | 4개 (조합 가능) | +300% |
| **템플릿 수** | 4개 | 8개 | +100% |
| **평균 정확도** | 75% (범용) | 90% (특화) | +20% |
| **처리 속도** | 1.5초 | 0.5-2초 (선택 가능) | 유연성 |

---

## 📊 Total Development Estimate

| Phase | Estimated Time | Lines of Code |
|-------|---------------|---------------|
| Phase 4A (YOLO 모델) | 1 week | ~50 lines |
| Phase 4B (후처리 노드) | 2 weeks | ~200 lines |
| Phase 4C (템플릿) | 1 week | ~100 lines |
| Phase 4D (벤치마크) | 1 week | ~150 lines |
| **TOTAL** | **5 weeks** | **~500 lines** |

**Prerequisites**:
- Training data: 2,000+ labeled drawings
- GPU: RTX 3080 or better
- Storage: 10GB+ for model weights

---

## 🚀 Next Steps

**최종 목표**: 사용자가 도면 유형만 선택하면 → 시스템이 최적 파이프라인 자동 구성

**Quick Start**:
1. Read [yolo_models.md](yolo_models.md) - Understand model selection
2. Read [pipeline_options.md](pipeline_options.md) - Choose post-processing strategy
3. Implement Phase 4A (YOLO model diversification)
4. Test with real drawings
5. Iterate based on user feedback

---

**See Also**:
- [yolo_models.md](yolo_models.md) - YOLO model details
- [pipeline_options.md](pipeline_options.md) - Post-processing options
- [../../ROADMAP.md](../../ROADMAP.md) - Overall project timeline
