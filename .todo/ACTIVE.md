# 진행 중인 작업

> **마지막 업데이트**: 2026-01-22
> **현재 활성화된 작업 목록**

---

## 🔴 진행 중

### 1. Git 변경사항 커밋 준비

**상세**: `13_GIT_CHANGES_SUMMARY.md`
**우선순위**: P0 (즉시)

| 작업 | 상태 |
|------|------|
| Zone.Identifier 파일 삭제 | ✅ 완료 |
| 중복 스크립트 정리 | ✅ 완료 |
| 문서 재배치 | ✅ 완료 |
| .gitignore 업데이트 | ✅ 완료 |
| 전체 테스트 실행 | ✅ 완료 (185 + 364 = 549 tests) |
| 커밋 생성 | ⏳ 대기 |

---

## ✅ 검증 완료 (2026-01-22)

**실제 검증 결과:**

| 항목 | 결과 | 상세 |
|------|------|------|
| Config 디렉토리 일관성 | ✅ 검증 완료 | 18/18 API (defaults.py 또는 대안) |
| 프로파일 시스템 (DEFAULTS) | ✅ 검증 완료 | 16개 API에 DEFAULTS 딕셔너리 존재 |
| 테스트 스위트 | ✅ 549개 통과 | web-ui: 185, gateway: 364 |
| API 헬스체크 | ✅ 14/18 healthy | 선택적 API 4개 미배포 |
| SVG 생성기 | ✅ 5개 API 존재 | pid-composer, line-detector, yolo, edocr2, paddleocr |
| NodeDefinitions | ✅ 30개 노드 | 테스트 업데이트 완료 (29→30) |
| ESLint | ✅ 0 errors | 1 warning (minor) |
| Build | ✅ 성공 | 15.38s |

### 테스트 수정 내역 (2026-01-22)
- `nodeDefinitions.test.ts`: 노드 개수 29→30 업데이트 (table_detector 추가 반영)
- detection 카테고리 1→2 업데이트

---

## ✅ 완료됨

### Config 디렉토리 일관성 (2026-01-19)

**상세**: `11_CONFIG_DIRECTORY_CONSISTENCY.md`

| API | config/ 상태 |
|-----|-------------|
| pid-analyzer-api | ✅ 완료 |
| skinmodel-api | ✅ 완료 |
| knowledge-api | ✅ 완료 |
| pid-composer-api | ✅ 완료 |
| vl-api | ✅ 완료 |
| esrgan-api | ✅ 완료 |
| ocr-ensemble-api | ✅ 이미 완료 |

---

### 프로파일 시스템 통합 (2026-01-19)

**상세**: `14_NODE_PROFILES_INTEGRATION.md`

| 작업 | 상태 |
|------|------|
| 백엔드 config/defaults.py 패턴 적용 | ✅ 19/19 API 완료 |
| 프론트엔드 ProfileDefinition 타입 추가 | ✅ 완료 |
| NodeDefinitions에 profiles 필드 추가 | ✅ 완료 (14 노드) |

**추가된 프로파일 노드**:
- **Detection**: yolo (4 profiles), table_detector (4 profiles)
- **OCR**: edocr2, paddleocr, tesseract, trocr, ocr_ensemble, suryaocr, doctr, easyocr (각 3 profiles)
- **Segmentation**: edgnet, linedetector (각 3-4 profiles)
- **Preprocessing**: esrgan (4 profiles)
- **Analysis**: skinmodel, pidanalyzer, pidcomposer (각 4 profiles)
- **Knowledge**: knowledge (4 profiles)
- **AI**: vl (4 profiles)

---

### UX Toast 시스템 (2026-01-16)
- APIStatusMonitor 토스트 적용 ✅
- useAPIDetail 훅 토스트 적용 ✅
- BlueprintFlow 노드 실행 토스트 ✅
- 전역 로딩 오버레이 시스템 ✅

### Toast 마이그레이션 (2026-01-16)
- 12개 파일 마이그레이션 완료 ✅

### E2E 테스트 구조화 (2026-01-16)
- 테스트 파일 구조 정리 ✅
- fixture 분리 ✅
- 549개 테스트 통과 ✅ (업데이트: 2026-01-22)

### 디렉토리 정리 (2026-01-19)
- rnd/ 정리 및 모델 추가 ✅
- scripts/ 정리 (training scripts 이동) ✅
- web-ui/ 정리 (test artifacts 삭제) ✅
- root 파일 정리 (32 → 15개) ✅
- docs/ 정리 (보수적 접근) ✅

---

## 📊 진행 현황 요약

| 작업 | 진행률 | 상태 |
|------|--------|------|
| 디렉토리 정리 | 100% | ✅ 완료 (검증됨) |
| Config 일관성 | 100% | ✅ 완료 (18/18 API 검증) |
| 프로파일 통합 | 100% | ✅ 완료 (16개 API 검증) |
| 테스트 스위트 | 100% | ✅ 549개 통과 |
| 커밋 준비 | 95% | 커밋 생성만 남음 |

---

## 📂 TODO 파일 목록

| 파일 | 설명 | 상태 |
|------|------|------|
| `11_CONFIG_DIRECTORY_CONSISTENCY.md` | API config/ 디렉토리 일관성 | ✅ 검증 완료 |
| `12_API_SPEC_NAMING_CONSISTENCY.md` | API 스펙 네이밍 (정보용) | ℹ️ 정보 |
| `13_GIT_CHANGES_SUMMARY.md` | Git 변경사항 요약 | ⏳ 커밋 대기 |
| `14_NODE_PROFILES_INTEGRATION.md` | 프로파일 시스템 통합 | ✅ 검증 완료 |
| `2026-01-22_DSE_BEARING_TEMPLATE_FIXES.md` | DSE Bearing 템플릿 개선 | 🔄 진행 예정 |

---

## 다음 우선순위

1. **P0**: 커밋 생성 (모든 변경사항 완료)
2. **P1**: DSE Bearing 템플릿 파라미터 정리 (78/100점)
3. ~~P1: pid-analyzer-api, skinmodel-api config 추가~~ ✅
4. ~~P2: 나머지 API config 추가~~ ✅
5. ~~P2: NodeDefinitions 프로파일 연동~~ ✅

---

*마지막 업데이트: 2026-01-22*
