# AX POC 시스템 개선 계획 - 전체 인덱스

> 작성일: 2025-11-13
> 작성자: Claude Code
> 목적: 전체 개선 계획 가이드

---

## 📋 문서 개요

이 디렉토리는 AX POC 엔지니어링 도면 분석 시스템의 현황 분석과 개선 계획을 담고 있습니다.

### 문서 구조

```
TODO/
├── 00_INDEX.md                             📖 이 문서 (시작 가이드)
├── 01_CURRENT_STATUS_OVERVIEW.md          ← 여기서 시작!
├── 02_EDOCR2_INTEGRATION_PLAN.md          🔴 최우선 과제
├── 03_MINOR_FIXES.md                       🟡 빠른 개선
├── 04_YOLO_TRAINING_DOCUMENTATION.md      🔴 문서화 필수
├── 05_SKIN_MODEL_IMPROVEMENT.md           🟢 중장기 개선
├── 06_PADDLEOCR_INTEGRATION_OPTIONS.md    🟡 통합 옵션
├── 07_ALTERNATIVE_MODELS_RESEARCH.md      📚 대안 조사
└── 08_LONG_TERM_IMPROVEMENTS.md           🟢 장기 과제
```

---

## 🚨 핵심 발견 사항

### 시스템 현황 (60% 완성)

**✅ 완전히 작동 (3/7)**:
- YOLO API (5005) - 객체 검출 (85-90%)
- EDGNet API (5012) - 그래프 신경망 (90%)
- VL API (5004) - 비전 언어 (95%+)

**🔴 심각한 문제 (1/7)**:
- **eDOCr2 API (5001)** - Mock 데이터만 반환
  - 치수 추출: 0%
  - GD&T 추출: 0%
  - **파이프라인 40% 마비**

**🟡 부분 구현 (2/7)**:
- Skin Model API (5003) - 규칙 기반 (~70%)
- PaddleOCR API (5006) - 구현, 미사용

**✅ 완벽 (1/1)**:
- Gateway API (8000) - 오케스트레이션

---

## 🎯 우선순위별 작업 계획

### 🔴 Priority 1 - 긴급 (1주일)

| 작업 | 문서 | 소요 | 영향 |
|------|------|------|------|
| eDOCr2 수리 | 02번 | 2-3일 | 파이프라인 40% 복구 |
| YOLO 문서화 | 04번 | 1일 | 재현성 확보 |
| VL 키 검증 | 03번 | 4시간 | UX 개선 |

**목표**: 핵심 기능 복구 (60% → 85%)

---

### 🟡 Priority 2 - 중요 (2-3주)

| 작업 | 문서 | 소요 | 영향 |
|------|------|------|------|
| 안정성 개선 | 03번 | 8시간 | 안정성 향상 |
| PaddleOCR Fallback | 06번 | 4-6시간 | 고가용성 |
| Skin Model 개선 | 05번 | 1주일 | 정확도 +15% |

**목표**: 안정성 + 정확도 (85% → 95%)

---

### 🟢 Priority 3 - 개선 (1-3개월)

| 작업 | 문서 | 소요 | 영향 |
|------|------|------|------|
| 모델 레지스트리 | 08번 | 3-4일 | 버전 관리 |
| 비동기 처리 | 08번 | 3-4일 | 처리량 10x |
| 모니터링 | 08번 | 2-3일 | 관찰성 |
| 분산 추론 | 08번 | 2-3일 | 성능 향상 |

**목표**: 프로덕션 레벨 (95% → 100%)

---

## 📚 문서별 요약

### [01. 현재 상태 개요](01_CURRENT_STATUS_OVERVIEW.md)
⏱️ **10분**

**내용**:
- 7개 서비스 구현 상태
- eDOCr2 Mock 문제 상세
- YOLO 문서 부재 문제
- 우선순위 작업 목록

**언제?**: 프로젝트 첫 시작, 전체 현황 파악

---

### [02. eDOCr2 통합 계획](02_EDOCR2_INTEGRATION_PLAN.md)
⏱️ **15분** | 🔴 **최우선**

**내용**:
- Mock 문제 원인 분석
- 4가지 해결 옵션 비교
- 3단계 구현 계획
- 예상 소요: 2-3일

**권장**: Option 1 (dev/edocr2 repo)

---

### [03. 간단한 수정사항](03_MINOR_FIXES.md)
⏱️ **10분** | 🟡 **빠른 개선**

**내용**:
- VL API 키 검증
- EDGNet 모델 검증
- Gateway 에러 핸들링
- 로깅, Health Check
- 파일 크기 제한

**효과**: 8시간 작업으로 안정성 크게 향상

---

### [04. YOLO 학습 문서화](04_YOLO_TRAINING_DOCUMENTATION.md)
⏱️ **12분** | 🔴 **필수**

**내용**:
- 필요한 문서 목록
- 정보 수집 방법
- 작성할 파일 목록
- 4단계 작업 계획

**문제**: 학습 데이터, 하이퍼파라미터, 성능 모두 불명

---

### [05. Skin Model 개선](05_SKIN_MODEL_IMPROVEMENT.md)
⏱️ **15분** | 🟢 **중장기**

**내용**:
- 규칙 기반 분석 (왜 FEM 아닌가?)
- 3가지 개선 옵션:
  1. ML 회귀 (XGBoost) - 4-5일, 85-90%
  2. FEM API - 2-3주, 95%+, 느림
  3. ISO 표준 - 1일, 75%
- 단계별 로드맵

**권장**: ISO + ML XGBoost

---

### [06. PaddleOCR 통합](06_PADDLEOCR_INTEGRATION_OPTIONS.md)
⏱️ **12분** | 🟡 **옵션**

**내용**:
- OCR 비교 (PaddleOCR vs 타사)
- 4가지 통합 옵션:
  1. 삭제 (eDOCr2 수리 후)
  2. Fallback (추천)
  3. 앙상블 (+5-10% 정확도)
  4. 역할 분리

**권장**: Fallback (4-6시간)

---

### [07. 대안 모델 조사](07_ALTERNATIVE_MODELS_RESEARCH.md)
⏱️ **20분** | 📚 **참고**

**내용**:
- YOLO 대안: YOLOv8/9, Faster R-CNN
- OCR 대안: PaddleOCR, EasyOCR, TrOCR
- GNN 대안: GAT, GCN+Transformer
- Tolerance 대안: ML, FEM, ISO
- 비용-효과 분석

**결론**: 대부분 현재 선택 최선, eDOCr2만 교체

---

### [08. 장기 개선 과제](08_LONG_TERM_IMPROVEMENTS.md)
⏱️ **20분** | 🟢 **장기**

**내용**:
- 7가지 장기 과제:
  1. 모델 레지스트리 (MLflow)
  2. 분산 추론 (Ray/K8s)
  3. 비동기 처리 (Celery)
  4. 모니터링 (Prometheus)
  5. CI/CD (GitHub Actions)
  6. 데이터 버전 (DVC)
  7. 보안 강화 (JWT)
- 8-11주 로드맵

**목표**: 99.9% 가동률, 10+ RPS

---

## 🛣️ 추천 작업 순서

### Week 1: 긴급 수리
```
Day 1-3: eDOCr2 실제 구현 통합 (02번)
Day 4:   YOLO 학습 데이터 문서화 (04번)
Day 5:   VL API 키 검증 추가 (03번)
```

### Week 2-3: 안정화
```
Week 2:
  - 간단한 수정 완료 (03번)
  - PaddleOCR Fallback (06번)

Week 3:
  - Skin Model ISO 표준 (05번 Step 1)
  - 통합 테스트
```

### Week 4-5: 정확도
```
Week 4-5:
  - Skin Model ML 학습 (05번 Step 2)
  - 앙상블 전략
  - 성능 벤치마크
```

### Month 2-3: 프로덕션 (선택)
```
Month 2:
  - 모델 레지스트리 (08번)
  - 비동기 처리 (08번)
  - 모니터링 (08번)

Month 3:
  - 분산 추론 (08번)
  - CI/CD (08번)
  - 보안 강화 (08번)
```

---

## 📊 예상 성과

### 1주일 후 (Priority 1)
| 지표 | 현재 | 목표 |
|------|------|------|
| eDOCr2 작동 | 0% | **85-90%** |
| 치수 추출 | 0% | **85-90%** |
| GD&T 추출 | 0% | **80-85%** |
| 시스템 완성도 | 60% | **85%** |

### 3주일 후 (Priority 2)
| 지표 | 현재 | 목표 |
|------|------|------|
| 공차 예측 | 70% | **85-90%** |
| 안정성 | 중간 | **높음** |
| 가용성 | 95% | **99%** |
| 시스템 완성도 | 85% | **95%** |

### 3개월 후 (Priority 3)
| 지표 | 현재 | 목표 |
|------|------|------|
| 처리량 | 1-2 RPS | **10+ RPS** |
| 응답 시간 | 30초 | **5초** |
| 가동률 | 95% | **99.9%** |
| 시스템 완성도 | 95% | **100%** |

---

## 🔗 관련 문서

### 기존 문서 (프로젝트 루트)
- `docs/architecture/DECISION_MATRIX.md` - 모델 선정 비교
- `docs/opensource/COMPARISON_REPORT.md` - eDOCr v1/v2 분석
- `docs/reports/FINAL_COMPREHENSIVE_REPORT.md` - 최종 보고서

### 새 문서 (최근 작성)
- `docs/API_DOCUMENTATION_STATUS.md` - API 품질 (100점)
- `docs/SCHEMA_IMPROVEMENT_REPORT.md` - 스키마 개선
- `docs/testing/HYPERPARAMETER_TEST_REPORT.md` - 하이퍼파라미터 테스트

---

## ❓ FAQ

### Q1: 어디서 시작?
**A**: `01_CURRENT_STATUS_OVERVIEW.md` → `02_EDOCR2_INTEGRATION_PLAN.md`

### Q2: eDOCr2가 최우선인 이유?
**A**: 파이프라인 40% 마비. 치수/GD&T 추출 0%.

### Q3: 최소한 무엇만?
**A**: Priority 1만 (1주일). 60% → 85% 향상.

### Q4: Priority 3 필수?
**A**: 아니요. 소규모 온프레미스는 1-2만으로 충분.

### Q5: 소요 시간 정확?
**A**: 경험자 기준. 초보는 1.5-2배 예상.

---

## 📞 다음 단계

1. **지금 바로**: `01_CURRENT_STATUS_OVERVIEW.md` 읽기 (10분)
2. **오늘**: `02_EDOCR2_INTEGRATION_PLAN.md` 읽기 (15분)
3. **내일부터**: eDOCr2 수리 시작 (2-3일)

---

**작성일**: 2025-11-13
**총 문서**: 8개 (01-08번)
**총 분량**: ~120KB
**예상 독서 시간**: 2시간
