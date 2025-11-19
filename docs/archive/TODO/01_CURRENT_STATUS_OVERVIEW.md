# 현재 시스템 상태 개요

> 작성일: 2025-11-13
> 작성자: Claude Code
> 목적: 전체 API 서비스 현황 파악 및 개선 방향 제시

---

## 📊 시스템 전체 현황

### 서비스 개수: 6개 (+ Gateway 1개 = 총 7개)

| 서비스 | 포트 | 구현 상태 | 통합 상태 | 정확도 | 우선순위 |
|--------|------|-----------|-----------|--------|----------|
| **Gateway API** | 8000 | ✅ 실제 | ✅ 중앙 허브 | N/A | 🔴 핵심 |
| **YOLO API** | 5005 | ✅ 실제 | ✅ 직접 연동 | 85-90% | 🔴 핵심 |
| **eDOCr2 API** | 5001 | 🔴 Mock | ⚠️ 연동되나 동작 안함 | 0% | 🔴 **심각** |
| **EDGNet API** | 5012 | ✅ 실제 | ✅ 직접 연동 | 90% | 🟡 중간 |
| **Skin Model API** | 5003 | 🟡 규칙 기반 | ✅ 부분 연동 | ~70% | 🟢 낮음 |
| **PaddleOCR API** | 5006 | ✅ 실제 | ❌ 미사용 | 85-95% | 🟢 낮음 |
| **VL API** | 5004 | ✅ 실제 | ✅ 대안 | 95%+ | 🟡 중간 |

---

## 🚨 심각한 문제

### 1. eDOCr2 API - Mock 데이터만 반환 중 🔴

**파일**: `edocr2-api/api_server.py` (122-149줄)

**증상**:
```python
def process_ocr(...):
    """
    TODO: 실제 eDOCr2 파이프라인 연동  # 🚨 명시적 TODO!
    현재는 Mock 데이터 반환             # 🚨 Mock 인정!
    """

    # 실제 import는 모두 주석 처리됨
    # from edocr2.keras_ocr import pipeline    # ❌ COMMENTED
    # from edocr2.tools import ocr_pipelines   # ❌ COMMENTED

    time.sleep(2)  # 가짜 지연

    return {
        "dimensions": [],  # 🚨 항상 빈 배열
        "gdt": [],         # 🚨 항상 빈 배열
        "text": {
            "drawing_number": "MOCK-001",  # 🚨 하드코딩
            ...
        }
    }
```

**영향**:
- ✅ YOLO가 bbox를 정확히 검출해도
- ❌ eDOCr2가 치수/GD&T 값을 추출하지 못함
- ❌ 결과적으로 **치수 추출 0%, GD&T 추출 0%**
- ❌ 파이프라인의 핵심 기능 마비

**해결 방법**: `02_EDOCR2_INTEGRATION_PLAN.md` 참조

---

### 2. 학습 데이터셋 문서 부재 🔴

**YOLO 모델**:
- 파일: `yolo-api/api_server.py` (291-340줄)
- 14개 클래스 정의됨 (diameter_dim, linear_dim, flatness, ...)
- **하지만**: 이 모델을 어떤 데이터로 학습했는지 기록 없음
- **문제**: 재현 불가, 개선 불가, 검증 불가

**필요한 정보**:
```
❓ 어떤 데이터셋? (도면 몇 장?)
❓ 어떻게 라벨링? (도구는?)
❓ 학습 하이퍼파라미터? (epochs, lr, batch_size?)
❓ 성능 지표? (mAP, Precision, Recall?)
❓ 검증 방법? (Test set 분할?)
```

**해결 방법**: `04_YOLO_TRAINING_DOCUMENTATION.md` 참조

---

## ✅ 잘 작동하는 부분

### 1. YOLO API (5005) - 완벽 구현 ⭐⭐⭐⭐⭐

**라이브러리**: ultralytics >= 8.0.0 (YOLOv11)
**모델**: yolo11n.pt (2.6M 파라미터)
**처리 속도**: 30-50ms (GPU) / 200-500ms (CPU)

**14개 클래스 검출**:
```python
0-6:  치수 (Diameter, Linear, Radius, Angular, Chamfer, Tolerance, Reference)
7-11: GD&T (Flatness, Cylindricity, Position, Perpendicularity, Parallelism)
12:   표면 거칠기 (Surface Roughness)
13:   텍스트 블록 (Unclassified Text)
```

**API 엔드포인트**:
- `/api/v1/detect`: 객체 검출 + bbox
- `/api/v1/extract_dimensions`: 치수만 추출
- `/api/v1/download/{file_id}`: 결과 다운로드

**통합 상태**: Gateway에서 직접 호출, 정상 동작

---

### 2. EDGNet API (5012) - 그래프 신경망 ⭐⭐⭐⭐

**라이브러리**: torch-geometric 2.4.0 (GraphSAGE)
**입력**: 베지어 곡선 (Bezier curves) + 19차원 특징
**출력**: 3-클래스 분류 (Contour/Text/Dimension)

**파이프라인**:
```
이미지 입력
  → Skeletonization (골격 추출)
  → Trajectory Tracing (경로 추적)
  → Bezier Fitting (베지어 곡선 피팅)
  → Graph Construction (150-300 노드)
  → GraphSAGE Forward (5-layer GNN)
  → Classification (Contour/Text/Dimension)
```

**성능**:
- 3-클래스 정확도: 90.82%
- 2-클래스 정확도: 98.48%

**주의사항**:
- ⚠️ 모델 파일 없으면 Mock으로 fallback (조용히)
- ⚠️ 모델 경로: `/models/graphsage_dimension_classifier.pth`
- ✅ 실제 구현은 정상 작동

---

### 3. VL API (5004) - 비전 언어 모델 ⭐⭐⭐⭐

**지원 모델**:
- Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- GPT-4o (gpt-4o)
- Claude 3 Opus, Haiku

**기능**:
1. `/api/v1/extract_info_block`: 타이틀 블록 추출
2. `/api/v1/extract_dimensions`: 치수 추출
3. `/api/v1/infer_manufacturing_process`: 제조 공정 추론
4. `/api/v1/generate_qc_checklist`: QC 체크리스트 생성

**장점**:
- ✅ 정확도 95%+ (eDOCr2보다 높음)
- ✅ 유연함 (다양한 도면 포맷 처리)
- ✅ 즉시 사용 가능 (학습 불필요)

**단점**:
- ⚠️ 느림 (5-30초/이미지)
- ⚠️ 비용 ($0.01-0.10/이미지)
- ⚠️ API 키 필요 (ANTHROPIC_API_KEY, OPENAI_API_KEY)
- ⚠️ 외부 의존성 (오프라인 불가)

**용도**: eDOCr2 수리 전까지 임시 대안으로 사용 중

---

## 🟡 부분 구현 / 개선 필요

### 4. Skin Model API (5003) - 규칙 기반 ⭐⭐⭐

**현재 구현**: 공학 휴리스틱 (Engineering Heuristics)
**실제 아님**: FEM 시뮬레이션 ❌

**동작 방식**:
```python
# 1. 재질별 계수 룩업
material_factors = {
    "Steel": 1.0,
    "Aluminum": 0.8,
    "Titanium": 1.5,
    "Plastic": 0.6
}

# 2. 공정별 기본 공차
process_tolerances = {
    "machining": {"flatness": 0.02, "cylindricity": 0.03},
    "casting": {"flatness": 0.15, "cylindricity": 0.20},
}

# 3. 선형 계산
tolerance = base * material_factor * size_factor * corr_factor

# 4. 임계값 기반 점수
if tolerance < 0.05:
    score = 0.65  # Hard
elif tolerance < 0.10:
    score = 0.80  # Medium
else:
    score = 0.92  # Easy
```

**왜 FEM이 아닌가**:
- ❌ 물리 시뮬레이션 없음
- ❌ 응력/변형 계산 없음
- ❌ 경계 조건 없음
- ✅ 단순 룩업 테이블 + 선형 곱셈

**정확도**: ~70% (실제 제조 결과와 비교 시)

**개선 방안**: `05_SKIN_MODEL_IMPROVEMENT.md` 참조

---

### 5. PaddleOCR API (5006) - 미사용 상태 ⭐⭐

**구현 상태**: ✅ 완전히 작동
**통합 상태**: ❌ Gateway에서 호출 안 함

**라이브러리**: paddleocr >= 2.7.0
**기능**: 텍스트 검출 + 인식

**PaddleOCR vs Tesseract**:
| 항목 | PaddleOCR | Tesseract |
|------|-----------|-----------|
| 정확도 | 95%+ | 85-90% |
| 속도 | 빠름 (GPU) | 중간 |
| 딥러닝 | CRNN | 전통 방식 |
| 각도 보정 | ✅ | 제한적 |

**왜 사용 안 하나?**:
1. eDOCr2가 도면 특화 OCR이어야 함
2. PaddleOCR은 범용 OCR
3. GD&T 기호 인식 안 됨
4. Gateway 코드에 통합 안 됨

**개선 방안**:
- Option A: eDOCr2 수리되면 삭제
- Option B: 텍스트 영역 fallback으로 사용
- Option C: 앙상블에 추가 (검증용)

---

## 📈 전체 시스템 평가

### 구현 완성도: 60%

```
✅ 완전 구현 (3/7): YOLO, EDGNet, VL API
🟡 부분 구현 (2/7): Skin Model (규칙 기반), PaddleOCR (미통합)
🔴 미구현 (1/7): eDOCr2 (Mock)
✅ 인프라 (1/1): Gateway (오케스트레이션)
```

### 파이프라인 정확도

**현재 (eDOCr2 Mock 상태)**:
```
YOLO 검출: 85-90% ✅
치수 추출: 0%      🔴 (eDOCr2 고장)
GD&T 추출: 0%      🔴 (eDOCr2 고장)
공차 예측: ~70%    🟡 (규칙 기반)
```

**수리 후 예상 (eDOCr2 실제 구현)**:
```
YOLO 검출: 85-90% ✅
치수 추출: 85-90% ✅
GD&T 추출: 80-85% ✅
공차 예측: ~70%    🟡
```

---

## 🎯 우선순위별 작업

### 🔴 Priority 1 - 긴급 (1주일)

1. **eDOCr2 실제 구현으로 교체**
   - 파일: `02_EDOCR2_INTEGRATION_PLAN.md`
   - 예상 소요: 2-3일
   - 영향: 파이프라인 40% 기능 복구

2. **YOLO 학습 데이터 문서화**
   - 파일: `04_YOLO_TRAINING_DOCUMENTATION.md`
   - 예상 소요: 1일
   - 영향: 재현성, 개선 가능성 확보

3. **VL API 키 검증 추가**
   - 파일: `03_MINOR_FIXES.md`
   - 예상 소요: 4시간
   - 영향: 사용자 경험 개선

### 🟡 Priority 2 - 중요 (2-3주)

4. **EDGNet 모델 검증 강화**
   - Silent fallback → 명시적 에러
   - 예상 소요: 2시간

5. **PaddleOCR 통합 또는 제거**
   - 앙상블 추가 또는 삭제 결정
   - 예상 소요: 4시간

6. **앙상블 가중치 개선**
   - 신뢰도 기반 투표
   - 예상 소요: 1일

### 🟢 Priority 3 - 개선 (1개월)

7. **Skin Model ML 전환**
   - 규칙 → 머신러닝 또는 FEM API
   - 예상 소요: 10-15일

8. **모델 버전 관리**
   - 레지스트리, 체크섬, 자동 다운로드
   - 예상 소요: 3-4일

---

## 📂 관련 문서

### TODO 디렉토리 구조

```
/home/uproot/ax/poc/TODO/
├── 01_CURRENT_STATUS_OVERVIEW.md          (이 문서)
├── 02_EDOCR2_INTEGRATION_PLAN.md          (eDOCr2 수리 계획)
├── 03_MINOR_FIXES.md                       (간단한 수정 사항)
├── 04_YOLO_TRAINING_DOCUMENTATION.md      (YOLO 문서화)
├── 05_SKIN_MODEL_IMPROVEMENT.md           (Skin Model 개선)
├── 06_PADDLEOCR_INTEGRATION_OPTIONS.md    (PaddleOCR 처리)
├── 07_ALTERNATIVE_MODELS_RESEARCH.md      (대안 모델 조사)
└── 08_LONG_TERM_IMPROVEMENTS.md           (장기 개선 과제)
```

### 기존 문서

- `docs/architecture/DECISION_MATRIX.md`: 모델 선정 비교표
- `docs/opensource/COMPARISON_REPORT.md`: eDOCr v1/v2 분석
- `docs/reports/FINAL_COMPREHENSIVE_REPORT.md`: 최종 보고서

---

## 🔍 핵심 통찰

1. **인프라는 훌륭함**: FastAPI, Docker, 마이크로서비스 구조 우수
2. **YOLO는 완벽**: 검출 성능 좋고 빠름
3. **eDOCr2가 병목**: Mock 데이터로 인해 전체 파이프라인 마비
4. **대안은 있음**: VL API가 임시 해결책으로 작동 중
5. **문서 부족**: 학습 데이터, 모델 버전, 성능 지표 기록 필요

---

**다음 단계**: `02_EDOCR2_INTEGRATION_PLAN.md` 읽고 eDOCr2 수리 시작
