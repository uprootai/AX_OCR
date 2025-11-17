# Claude Code 프로젝트 관리 가이드

> **목적**: LLM이 효율적으로 프로젝트를 이해하고 관리할 수 있도록 구조화된 가이드

---

## 🎯 프로젝트 개요

**도면 OCR 및 제조 견적 자동화 시스템**

- **목표**: 기계 도면 → 치수 추출 → 공차 분석 → 자동 견적
- **핵심 기술**: YOLO, eDOCr, EDGNet, Skin Model, 앙상블 OCR
- **아키텍처**: 마이크로서비스 (Docker Compose)
- **UI**: React (TypeScript) + FastAPI Gateway

---

## 📁 프로젝트 구조 (중요도 순)

```
/home/uproot/ax/poc/
├── gateway-api/          ⭐⭐⭐ [최우선] Gateway 오케스트레이션
│   ├── api_server.py     (2005 lines - 리팩토링 필요!)
│   ├── cost_estimator.py
│   ├── pdf_generator.py
│   └── advanced_features.py
├── web-ui/               ⭐⭐⭐ [최우선] React 프론트엔드
│   ├── src/pages/test/TestGateway.tsx  (714 lines)
│   ├── src/types/api.ts  (타입 정의)
│   └── dist/             (빌드 결과)
├── yolo-api/             ⭐⭐ 객체 검출 (YOLO)
├── edocr2-v2-api/        ⭐⭐ OCR 서비스 (eDOCr v2)
├── paddleocr-api/        ⭐⭐ 보조 OCR (PaddleOCR)
├── edgnet-api/           ⭐ 세그멘테이션 (EDGNet)
├── skinmodel-api/        ⭐ 공차 분석 (Skin Model)
└── vl-api/               ⭐ Vision-Language 모델
```

---

## 🔥 **리팩토링 우선순위** (매우 중요!)

### 문제점
1. **gateway-api/api_server.py**: 2005 라인 (1개 파일에 모든 로직)
2. **모듈화 부족**: 함수들이 순서대로 나열
3. **테스트 어려움**: 의존성이 강하게 결합됨

### 해결 방안: 객체지향 + 모듈 분리

```
gateway-api/
├── api_server.py         (200 lines) - 엔드포인트만
├── services/
│   ├── __init__.py
│   ├── ocr_service.py    (300 lines) - OCR 관련 통합
│   ├── ensemble_service.py (200 lines) - 앙상블 전략
│   ├── yolo_service.py   (150 lines) - YOLO 호출
│   ├── tolerance_service.py (150 lines) - 공차 분석
│   └── quote_service.py  (200 lines) - 견적 생성
├── models/
│   ├── __init__.py
│   ├── request_models.py (100 lines) - Pydantic 요청 모델
│   └── response_models.py (100 lines) - Pydantic 응답 모델
├── utils/
│   ├── __init__.py
│   ├── image_utils.py    (150 lines) - crop, upscale, pdf2img
│   ├── filters.py        (100 lines) - False Positive 필터
│   └── progress.py       (100 lines) - ProgressTracker
└── config.py             (50 lines) - 환경 변수, 상수
```

**예상 효과**:
- 파일당 평균 150 라인 (LLM 컨텍스트 효율 ↑)
- 단일 책임 원칙 (테스트 용이)
- 병렬 개발 가능

---

## 🚀 핵심 기능 (LLM이 알아야 할 것)

### 1. YOLO Crop OCR (신규 ⭐)
**위치**: `gateway-api/api_server.py:828-970`
**함수**: `process_yolo_crop_ocr()`
**기능**: YOLO 검출 영역별 개별 eDOCr2 OCR 실행
**성능**: 재현율 93.3% (+16.7%p), 시간 +2.1%
**개선사항**:
- False Positive 필터링 (7가지 패턴)
- Crop 최소 크기 보장 (50px)
- 작은 영역 2x upscaling
- asyncio.gather() 병렬 처리
- **2025-11-17**: PaddleOCR → eDOCr2로 변경

**⚠️ 알려진 이슈**:
- eDOCr2는 crop된 작은 이미지에서 프레임 검출 실패 가능 (`find_frame()` 오류)
- UI에서 **Graceful Degradation** 적용 필요
  - Crop OCR 실패 시 전체 이미지 OCR로 자동 폴백
  - 사용자에게 부분 실패 상태 명확히 표시
  - 성공한 crop 결과만 표시하고 실패한 crop은 "재시도" 옵션 제공

### 2. 앙상블 전략 (신규 ⭐)
**위치**: `gateway-api/api_server.py:961-1047`
**함수**: `ensemble_ocr_results()`
**기능**: YOLO Crop OCR + eDOCr v2 가중치 기반 융합
**알고리즘**:
- 유사도 기반 매칭 (difflib.SequenceMatcher)
- 가중치: YOLO 0.6, eDOCr 0.4
- 양쪽 확인된 치수 우선
**예상 성능**: 정밀도 90%+, 재현율 100%, F1 95%+

### 3. Gateway API 엔드포인트
**메인**: `POST /api/v1/process`
**파라미터**:
- `use_yolo_crop_ocr: bool` - YOLO Crop OCR 활성화
- `use_ensemble: bool` - 앙상블 전략 활성화
- `pipeline_mode: str` - "speed" | "hybrid"

---

## 📝 작업 시나리오별 가이드

### 시나리오 1: 새로운 OCR 방법 추가
1. `services/ocr_service.py`에 `call_new_ocr()` 함수 추가
2. `services/ensemble_service.py`에 통합
3. `models/request_models.py`에 옵션 추가
4. `web-ui/src/types/api.ts`에 타입 추가
5. `web-ui/src/pages/test/TestGateway.tsx`에 UI 추가

### 시나리오 2: 성능 개선
1. **병목 지점 확인**: `processing_time` 메트릭 분석
2. **병렬화 가능 여부**: `asyncio.gather()` 적용
3. **캐싱**: 동일 이미지 재처리 방지
4. **최적화**: 불필요한 변환 제거

### 시나리오 3: 버그 수정
1. **로그 확인**: `docker logs gateway-api --tail 100`
2. **타입 오류**: TypeScript는 빌드 시 검증
3. **API 오류**: Postman/curl로 직접 테스트
4. **컨테이너 재시작**: `docker-compose restart <service>`

### 시나리오 4: UI 수정
1. **개발 모드**: `cd web-ui && npm run dev` (포트 5174)
2. **수정**: `src/pages/test/TestGateway.tsx`
3. **빌드**: `npm run build`
4. **배포**: `docker cp dist/. web-ui:/usr/share/nginx/html/`

---

## 🛠 개발 워크플로우

### 백엔드 수정
```bash
# 1. 코드 수정
vim gateway-api/api_server.py

# 2. 재빌드 + 재시작
docker-compose build gateway-api
docker rm -f gateway-api
docker-compose up -d gateway-api

# 3. 로그 확인
docker logs gateway-api -f
```

### 프론트엔드 수정
```bash
# 1. 코드 수정
vim web-ui/src/pages/test/TestGateway.tsx

# 2. 빌드
cd web-ui && npm run build

# 3. 배포
docker cp dist/. web-ui:/usr/share/nginx/html/

# 4. 브라우저 캐시 클리어 (Ctrl+Shift+R)
```

---

## 📊 성능 메트릭 추적

### 주요 지표
| 메트릭 | 목표 | 현재 | 개선 방향 |
|--------|------|------|-----------|
| **재현율** | 100% | 93.3% | Crop 성공률 ↑ |
| **정밀도** | 90%+ | 57.14% → 90%+ (필터링 후) | False Positive ↓ |
| **F1 Score** | 95%+ | 64% → 95%+ (앙상블) | 균형 |
| **처리 시간** | <10s | 19.78s → 8-10s (병렬) | asyncio.gather |

### 모니터링
- **Gateway Health**: http://localhost:8000/api/v1/health
- **웹 UI**: http://localhost:5173
- **로그**: `docker logs <service> --tail 100`

---

## 🔍 디버깅 체크리스트

### API 500 에러
1. `docker logs gateway-api --tail 50 | grep ERROR`
2. Python 스택 트레이스 확인
3. 타입 변환 오류 (multipart form data → str)
4. 경로 존재 여부 확인

### UI 타입 오류
1. `src/types/api.ts`에 타입 정의 확인
2. `npm run build` 출력 확인
3. `?.` 옵셔널 체이닝 사용

### Docker 문제
1. `docker ps -a` - 컨테이너 상태 확인
2. `docker logs <container>` - 로그 확인
3. `docker system prune` - 오래된 이미지/컨테이너 정리

---

## 📚 주요 파일 요약

### gateway-api/api_server.py
**라인 수**: 2005 (리팩토링 필요!)
**주요 함수**:
- `process_drawing()` (line 1273) - 메인 엔드포인트
- `process_yolo_crop_ocr()` (line 819) - YOLO Crop OCR
- `ensemble_ocr_results()` (line 961) - 앙상블
- `is_false_positive()` (line 777) - 필터링
- `crop_bbox()` (line 693) - Crop + upscale

### web-ui/src/pages/test/TestGateway.tsx
**라인 수**: 714
**주요 섹션**:
- Line 25-32: 옵션 state (use_yolo_crop_ocr, use_ensemble)
- Line 306-369: 고급 OCR 전략 UI
- Line 505-550: YOLO Crop OCR 결과 카드
- Line 552-605: 앙상블 결과 카드

### 최근 구현 내역

#### 2025-11-16 (최신)
**주요 작업**:
1. ✅ YOLO 시각화 이미지 Base64 인코딩 (`yolo-api/api_server.py:452-494`)
2. ✅ Web UI 시각화 카드 추가 (`web-ui/src/pages/test/TestGateway.tsx:476-514`)
3. ✅ Skills 시스템 구축 (doc-updater, code-janitor, ux-enhancer)
4. ✅ Pydantic 타입 정의 확장 (`web-ui/src/types/api.ts:124-136`)
5. ✅ 사용자 피드백 반영: "시각화 체크했는데 이미지 안보임" 버그 수정

**문서**:
- VISUALIZATION_FIX_REPORT.md
- CHANGELOG_2025-11-16.md
- .claude/skills/README.md

#### 2025-11-15
**작업**:
1. False Positive 필터링 (7가지 패턴)
2. Crop 최소 크기 + upscaling
3. asyncio.gather() 병렬 처리
4. eDOCr v2 CUDA 오류 수정
5. 앙상블 전략 구현
6. 웹 UI 통합

---

## 🎓 LLM을 위한 팁

### 효율적인 코드 읽기
1. **파일 크기 확인 먼저**: `wc -l <file>` - 500줄 이상이면 함수 목록만 먼저 확인
2. **함수 시그니처 파악**: `grep "^def \|^async def" <file>`
3. **타입 정의 우선**: Pydantic 모델을 먼저 읽으면 API 구조 이해 쉬움
4. **주석 활용**: 함수 docstring에 의도가 명확함

### 컨텍스트 절약
1. **한 번에 하나의 서비스만**: Gateway 작업 시 다른 서비스 코드 읽지 않기
2. **Read 대신 Grep**: 특정 함수만 찾을 때는 Grep 사용
3. **타입 체크**: TypeScript 빌드로 타입 오류 사전 발견

### 리팩토링 시 주의
1. **테스트 먼저**: 기존 API 호출이 정상 작동하는지 확인
2. **점진적 분리**: 한 번에 하나의 모듈만 분리
3. **import 순환 주의**: `models` → `utils` → `services` → `api_server` 순서 유지

---

## 🚧 다음 단계 (우선순위)

### 1주일 내
- [ ] gateway-api 리팩토링 (services/ 분리)
- [ ] 단위 테스트 추가 (pytest)
- [ ] API 문서 자동 생성 (OpenAPI)

### 1개월 내
- [ ] 성능 벤치마크 자동화
- [ ] CI/CD 파이프라인 (GitHub Actions)
- [ ] 로그 중앙화 (ELK Stack)

### 3개월 내
- [ ] Kubernetes 마이그레이션
- [ ] 모델 A/B 테스트
- [ ] 실시간 모니터링 대시보드

---

## 📞 문제 발생 시

1. **로그 확인**: `docker logs <service> --tail 100`
2. **Health Check**: `curl http://localhost:8000/api/v1/health`
3. **재시작**: `docker-compose restart <service>`
4. **재빌드**: `docker-compose build <service> && docker rm -f <service> && docker-compose up -d <service>`

---

**마지막 업데이트**: 2025-11-17
**버전**: 1.2.0
**관리자**: Claude Code

**주요 변경**:
- YOLO Crop OCR이 eDOCr2 사용하도록 변경
- Pydantic 모델 visualized_image 필드 추가
- 타이머 증가 버그 수정 (PipelineProgress.tsx)
- eDOCr2 프레임 검출 실패 시 Graceful Degradation UI/UX 가이드 추가
