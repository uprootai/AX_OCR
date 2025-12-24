# Blueprint AI BOM API

> **Human-in-the-Loop 기반 도면 분석 및 BOM 생성**

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| **포트** | 5020 |
| **Frontend** | http://localhost:3000 |
| **API Docs** | http://localhost:5020/docs |
| **버전** | v8.0 |

---

## 주요 기능

### 1. AI 심볼 검출
- YOLO v11 기반 27개 클래스 자동 검출
- 신뢰도 기반 필터링

### 2. OCR 치수 인식
- eDOCr2 기반 한국어 치수 인식
- 단위 및 공차 파싱

### 3. GD&T 분석
- 기하공차 심볼 파싱 (⌀, ⊥, ∥, ⊙, ⌖)
- 데이텀 검출 (A, B, C)

### 4. Active Learning 검증 큐
| 우선순위 | 조건 | 설명 |
|---------|------|------|
| CRITICAL | 신뢰도 < 0.7 | 즉시 확인 필요 |
| HIGH | 심볼 연결 없음 | 연결 확인 필요 |
| MEDIUM | 신뢰도 0.7-0.9 | 검토 권장 |
| LOW | 신뢰도 ≥ 0.9 | 자동 승인 후보 |

### 5. BOM 생성 및 내보내기
- Excel, CSV, JSON, PDF 형식 지원

### 6. Feedback Loop Pipeline (v8.0)
- 검증된 데이터 YOLO 재학습용 데이터셋 내보내기

---

## 파라미터

### detection_confidence (신뢰도 임계값)

검출 결과를 필터링하는 신뢰도 기준입니다.

- **타입**: number (0.0 ~ 1.0)
- **기본값**: `0.4`
- **팁**: 작은 심볼이 많으면 `0.3`으로 낮추세요

### auto_approve_threshold (자동 승인 임계값)

자동 승인 대상이 되는 최소 신뢰도입니다.

- **타입**: number (0.5 ~ 1.0)
- **기본값**: `0.9`

### critical_threshold (크리티컬 임계값)

즉시 확인이 필요한 항목의 신뢰도 기준입니다.

- **타입**: number (0.0 ~ 0.9)
- **기본값**: `0.7`

### ocr_languages (OCR 언어)

치수 인식에 사용할 언어입니다.

- **타입**: array
- **기본값**: `["ko", "en"]`
- **옵션**: ko, en, ja, zh

---

## API 엔드포인트

### 세션 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/sessions/upload` | 이미지 업로드 |
| GET | `/sessions` | 세션 목록 |
| GET | `/sessions/{id}` | 세션 상세 |
| DELETE | `/sessions/{id}` | 세션 삭제 |

### 분석

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/analysis/detect/{id}` | YOLO 검출 |
| POST | `/analysis/ocr/{id}` | OCR 인식 |
| POST | `/analysis/full/{id}` | 전체 분석 |

### 검증 (Active Learning)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/verification/queue/{id}` | 검증 큐 조회 |
| POST | `/verification/verify/{id}` | 단일 항목 검증 |
| POST | `/verification/auto-approve/{id}` | 자동 승인 |
| POST | `/verification/bulk-approve/{id}` | 일괄 승인 |

### BOM

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/bom/generate/{id}` | BOM 생성 |
| GET | `/bom/export/{id}/{format}` | 내보내기 |

### Feedback Loop (v8.0)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/feedback/stats` | 피드백 통계 |
| POST | `/feedback/export/yolo` | YOLO 데이터셋 내보내기 |
| GET | `/feedback/exports` | 내보내기 목록 |

---

## 27개 검출 클래스

| ID | 클래스명 | 한글명 |
|----|---------|--------|
| 0 | ARRESTER | 피뢰기 |
| 1 | BUS | 모선 |
| 2 | CT | 변류기 |
| 3 | DS | 단로기 |
| 4 | ES | 접지개폐기 |
| 5 | GCB | 가스차단기 |
| 6 | GPT | 접지형계기용변압기 |
| 7 | GS | 가스구간개폐기 |
| 8 | LBS | 부하개폐기 |
| 9 | MOF | 계기용변성기 |
| 10 | OCB | 유입차단기 |
| 11 | PT | 계기용변압기 |
| 12 | RECLOSER | 리클로저 |
| 13 | SC | 직렬콘덴서 |
| 14 | SHUNT_REACTOR | 분로리액터 |
| 15 | SS | 정류기 |
| 16 | TC | 탭절환기 |
| 17 | TR | 변압기 |
| 18 | TVSS | 서지흡수기 |
| 19 | VCB | 진공차단기 |
| 20 | 고장점표시기 | 고장점표시기 |
| 21 | 단로기_1P | 단로기(1P) |
| 22 | 부하개폐기_1P | 부하개폐기(1P) |
| 23 | 접지 | 접지 |
| 24 | 차단기 | 차단기 |
| 25 | 퓨즈 | 퓨즈 |
| 26 | 피뢰기 | 피뢰기 |

---

## 권장 파이프라인

### 기본 BOM 생성
```
ImageInput → Blueprint AI BOM
```

### 정밀 분석 (YOLO 선행)
```
ImageInput → YOLO → Blueprint AI BOM
```

### 저해상도 도면
```
ImageInput → ESRGAN(2x) → Blueprint AI BOM
```

---

## 리소스 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| RAM | 4GB | 8GB |
| CPU 코어 | 4 | 8 |
| 디스크 | 20GB | 50GB |

---

**마지막 업데이트**: 2025-12-24
