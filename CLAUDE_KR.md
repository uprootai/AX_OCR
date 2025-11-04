# CLAUDE.md (한국어)

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 참고할 가이드입니다.

## 프로젝트 개요

**AX 실증산단 - 마이크로서비스 API 시스템**

공학 도면 기반 견적 자동화를 위한 마이크로서비스 시스템입니다. 4개의 독립적인 API 서비스와 웹 UI로 구성되어 있으며, 도면을 처리하고 치수를 추출하고 세그멘테이션을 수행하고 공차를 예측하여 최종적으로 비용 견적을 생성합니다.

## 아키텍처

### 서비스 구조

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  eDOCr2 API     │     │  EDGNet API     │     │  Skin Model API  │
│  포트: 5001/5002│     │  포트: 5012     │     │  포트: 5003      │
│  OCR 처리       │     │  세그멘테이션    │     │  공차 예측       │
└─────────────────┘     └─────────────────┘     └──────────────────┘
         ↑                       ↑                       ↑
         └───────────────────────┴───────────────────────┘
                                 │
                        ┌────────────────┐
                        │  Gateway API   │
                        │  포트: 8000    │
                        │  오케스트레이터 │
                        └────────────────┘
                                 ↑
                        ┌────────────────┐
                        │  Web UI        │
                        │  포트: 5173    │
                        │  React + Vite  │
                        └────────────────┘
```

### 서비스 상세

1. **eDOCr2 API** (edocr2-api/)
   - 이중 배포: v1 (포트 5001) 및 v2 (포트 5002)
   - v1: eDOCr v1 with Keras 2.x 모델 (.h5)
   - v2: edocr2 v2 with Keras 3.x 모델 (.keras) + 테이블 OCR 지원
   - 추출 항목: 치수, GD&T 기호, 텍스트/인포블록
   - 서버 파일: `api_server_edocr_v1.py`, `api_server_edocr_v2.py`
   - **중요**: v2 모델은 `.keras` 파일과 `.txt` alphabet 파일 모두 필요

2. **EDGNet API** (edgnet-api/)
   - 그래프 신경망 기반 도면 세그멘테이션
   - 도면 구성 요소 분류 (윤곽선, 텍스트, 치수)
   - 모델: GraphSAGE dimension classifier (.pth)
   - 엔드포인트: `/api/v1/segment`, `/api/v1/vectorize`

3. **Skin Model API** (skinmodel-api/)
   - 기하 공차 예측
   - 제조 가능성 분석
   - GD&T 검증

4. **Gateway API** (gateway-api/)
   - 모든 서비스 간 전체 파이프라인 오케스트레이션
   - eDOCr2, EDGNet, Skin Model 간 워크플로우 관리
   - 분석 결과로부터 견적서 생성

5. **Web UI** (web-ui/)
   - React 19 + TypeScript + Vite
   - 스타일링: Tailwind CSS
   - 상태 관리: Zustand (모니터링/추적 상태)
   - 데이터 페칭: TanStack Query (React Query)
   - 라우팅: React Router v7

## 개발 명령어

### 서비스 빌드 및 실행

#### 전체 시스템 (모든 서비스)
```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 모든 서비스 중지
docker-compose down
```

#### 개별 서비스

**eDOCr2 API (이중 배포 - v1 + v2)**
```bash
cd edocr2-api

# v1 빌드
docker build -f Dockerfile.v1 -t edocr-api:v1 .

# v2 빌드
docker build -f Dockerfile.v2 -t edocr-api:v2 .

# 이중 배포 실행 (v1: 5001, v2: 5002)
docker-compose -f docker-compose-dual.yml up -d

# 헬스 체크
curl http://localhost:5001/api/v1/health  # v1
curl http://localhost:5002/api/v2/health  # v2
```

**EDGNet API**
```bash
cd edgnet-api
docker build -t edgnet-api .
docker run -d -p 5012:5002 --name edgnet edgnet-api
curl http://localhost:5012/api/v1/health
```

**Skin Model API**
```bash
cd skinmodel-api
docker build -t skinmodel-api .
docker run -d -p 5003:5003 --name skinmodel skinmodel-api
curl http://localhost:5003/api/v1/health
```

**Gateway API**
```bash
cd gateway-api
docker build -t gateway-api .
docker run -d -p 8000:8000 --name gateway gateway-api
curl http://localhost:8000/api/v1/health
```

**Web UI**
```bash
cd web-ui

# 개발 모드 (hot reload)
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 빌드 미리보기
npm run preview

# 린팅
npm run lint

# Docker 배포
docker build -t web-ui .
docker run -d -p 5173:80 --name web-ui web-ui
```

### 테스트

#### API 헬스 체크
```bash
# 모든 서비스 한번에 테스트
cd /home/uproot/ax/poc
./test_apis.sh
```

#### Python 테스트 스크립트
```bash
# 일반 API 테스트
python test_apis.py

# eDOCr2 시각화 테스트
python test_edocr2_viz.py

# OCR 시각화 테스트
python test_ocr_visualization.py

# PDF 변환 테스트
python test_pdf_conversion.py

# 바운딩 박스 검증
python test_edocr2_bbox.py
python test_edocr2_bbox_detailed.py
python verify_bbox_api.py
```

#### 수동 API 테스트

**eDOCr2 v1 OCR**
```bash
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@drawing.pdf" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true"
```

**eDOCr2 v2 OCR (테이블 추출 포함)**
```bash
curl -X POST http://localhost:5002/api/v2/ocr \
  -F "file=@drawing.pdf" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true" \
  -F "extract_tables=true"
```

**EDGNet 세그멘테이션**
```bash
curl -X POST http://localhost:5012/api/v1/segment \
  -F "file=@drawing.png" \
  -F "visualize=true"
```

**Gateway 전체 파이프라인**
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@drawing.pdf" \
  -F "generate_quote=true"
```

## 핵심 기술 세부사항

### eDOCr2 이중 배포 시스템

이 프로젝트는 eDOCr의 두 가지 버전을 동시에 실행합니다:

- **v1 (포트 5001)**: 더 빠름, Keras 2.x 사용, 안정적
- **v2 (포트 5002)**: 고급 기능 (테이블 OCR), Keras 3.x 사용, alphabet 파일 필요

**중요**: v2 작업 시:
1. 모델 파일은 `.keras`와 `.txt` 파일 모두 필요 (예: `recognizer_dimensions_2.keras` + `recognizer_dimensions_2.txt`)
2. `.txt` 파일은 인식기에 필요한 alphabet 정의를 포함
3. alphabet 파일이 없으면 `FileNotFoundError` 발생
4. v2 모델 다운로드: https://github.com/javvi51/edocr2/releases/tag/v1.0.0

### 데이터 변환 레이어

eDOCr v1과 v2는 서로 다른 출력 형식을 가집니다. API 서버는 이를 UI 호환 형식으로 변환합니다:

**v1**: `api_server_edocr_v1.py`의 `transform_edocr_to_ui_format()` 사용
- eDOCr v1 형식의 'pred', 'box' 키 처리
- 'value'/'nominal'을 UI 예상 형식으로 변환

**v2**: `api_server_edocr_v2.py`의 `transform_edocr2_to_ui_format()` 사용
- edocr2 형식의 다른 스키마 처리
- 좌표 스케일링/오프셋을 포함하여 처리된 이미지 좌표를 원본 이미지 좌표로 변환
- 테이블 추출 결과 지원

**주요 변환**: 두 함수 모두 다음 UI 형식으로 변환:
```json
{
  "dimensions": [{"type": "linear|diameter|radius", "value": 50.5, "unit": "mm", "tolerance": "±0.1", "bbox": {"x": 100, "y": 200, "width": 80, "height": 30}}],
  "gdt": [{"type": "⏤", "value": 0.05, "datum": "A", "bbox": {"x": 150, "y": 250, "width": 60, "height": 25}}],
  "text": {"drawing_number": "DWG-001", "revision": "A", "title": "Part", "material": "Steel", "notes": [], "total_blocks": 5}
}
```

### Web UI 아키텍처

**상태 관리**:
- `monitoringStore.ts`: API 헬스 상태 및 요청 추적을 위한 Zustand store
- 서비스 헬스 추적: gateway, edocr2_v1, edocr2_v2, edgnet, skinmodel
- 요청 추적 이력 유지 (최대 50개)
- 성능 메트릭 계산 (avgResponseTime, successRate, errorRate)

**주요 컴포넌트**:
- `TestEdocr2.tsx`: v1/v2 간 전환 가능, 바운딩 박스로 OCR 결과 시각화
- `OCRVisualization.tsx`: 이미지에 치수/GD&T 오버레이 렌더링
- `APIStatusMonitor.tsx`: 실시간 서비스 헬스 모니터링
- `RequestInspector.tsx`: API 요청/응답 검사 디버그 도구

**버전 선택**:
UI는 드롭다운을 통해 eDOCr v1과 v2 간 선택을 지원합니다. API 엔드포인트가 `/api/v1/ocr`에서 `/api/v2/ocr`로 변경됩니다.

### Docker 볼륨

모든 서비스는 다음을 위해 볼륨 마운트를 사용합니다:
- 모델 파일 (읽기 전용): `/home/uproot/ax/dev/`에서 공유
- 업로드 디렉토리: 임시 파일 저장
- 결과 디렉토리: 처리된 출력

eDOCr2 예시:
```yaml
volumes:
  - ./dev/edocr2/edocr2:/app/edocr2:ro  # 소스 코드 (읽기 전용)
  - ./dev/edocr2/models:/models:ro      # 모델 파일 (읽기 전용)
  - ./edocr2-api/uploads:/tmp/edocr2/uploads
  - ./edocr2-api/results:/tmp/edocr2/results
```

### CORS 설정

모든 API 서비스는 로컬 개발을 위해 CORS가 활성화되어 있습니다:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Web UI
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 환경 변수

각 서비스는 환경 변수로 설정 가능 (docker-compose.yml 참조):

- `EDOCR2_PORT`, `EDOCR2_WORKERS`, `EDOCR2_MODEL_PATH`, `EDOCR2_LOG_LEVEL`
- `EDGNET_PORT`, `EDGNET_WORKERS`, `EDGNET_MODEL_PATH`, `EDGNET_LOG_LEVEL`
- `SKINMODEL_PORT`, `SKINMODEL_WORKERS`, `SKINMODEL_LOG_LEVEL`
- `GATEWAY_PORT`, `GATEWAY_WORKERS`, `EDOCR2_URL`, `EDGNET_URL`, `SKINMODEL_URL`, `GATEWAY_LOG_LEVEL`

## 일반적인 패턴

### 새 API 엔드포인트 추가

1. 요청/응답용 Pydantic 모델 정의
2. FastAPI 라우트 핸들러 추가
3. 비즈니스 로직 구현
4. 필요시 CORS 추가
5. API 문서 업데이트 (FastAPI 자동 생성)
6. 새 서비스인 경우 헬스 체크 추가
7. 필요시 docker-compose.yml 업데이트

### NumPy/TensorFlow 출력 작업

NumPy 타입을 JSON 직렬화 가능한 Python 타입으로 변환하려면 `convert_to_serializable()` 헬퍼 사용:
```python
def convert_to_serializable(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    # ... dict, list 재귀적 처리
```

### 바운딩 박스 처리

OCR 결과의 바운딩 박스 작업 시:
- eDOCr v1은 `box` 또는 `bbox` 키 사용 (형식: [[x,y], [x,y], [x,y], [x,y]])
- eDOCr v2는 `bbox` 키 사용
- UI 기대 형식: `{x: int, y: int, width: int, height: int}`
- 처리 전 bbox가 4개 포인트를 가지는지 항상 검증
- 이미지가 처리 중 리사이즈된 경우 좌표 스케일링 적용

### UI 컴포넌트 추가

1. `web-ui/src/components/`에 컴포넌트 생성
2. `components/ui/`의 기존 UI 프리미티브 사용 (Card, Button, Badge, Tooltip)
3. 상태 필요시 Zustand store와 통합
4. 데이터 페칭은 TanStack Query 사용
5. 새 페이지인 경우 `App.tsx`에 라우트 추가
6. 기존 TypeScript 패턴 따르기

## 문제 해결

### 포트 충돌
```bash
# 포트를 사용 중인 프로세스 확인
sudo lsof -i :5001
sudo lsof -i :5002
sudo lsof -i :5012
sudo lsof -i :5003
sudo lsof -i :8000
```

### 컨테이너 로그
```bash
# 개별 서비스
docker logs -f edocr2-api-v1
docker logs -f edocr2-api-v2
docker logs -f edgnet
docker logs -f gateway

# 모든 서비스
docker-compose logs -f
```

### 모델 파일 문제

**eDOCr v1**: 모델은 처음 실행 시 `~/.keras-ocr/`에 자동 다운로드
**eDOCr v2**: `.keras` + `.txt` 파일을 `edocr2-api/models/`에 수동 다운로드 필요

```bash
cd edocr2-api/models
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_dimensions_2.keras
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_dimensions_2.txt
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_gdts.keras
curl -L -O https://github.com/javvi51/edocr2/releases/download/v1.0.0/recognizer_gdts.txt
```

### Web UI가 API에 연결되지 않음

1. 모든 서비스가 실행 중인지 확인: `docker ps`
2. API 서버의 CORS 설정 확인
3. `web-ui/Dockerfile` 또는 `.env`의 환경 변수 확인
4. UI 설정과 docker-compose 간 포트 일치 확인

### JSON 직렬화 오류

"Object of type 'int64' is not JSON serializable" 같은 오류가 발생하면:
- 반환 전 모든 데이터에 `convert_to_serializable()` 헬퍼 사용
- NumPy 배열, TensorFlow 출력, PIL 이미지에서 흔함

## 참고 문서

- **eDOCr v1**: https://github.com/javvi51/eDOCr
- **edocr2 v2**: https://github.com/javvi51/edocr2
- **FastAPI**: https://fastapi.tiangolo.com/
- **React Query**: https://tanstack.com/query/latest
- **Zustand**: https://zustand-demo.pmnd.rs/

## 프로젝트 특징

- 주 언어: 한국어 (도면 = drawing, 치수 = dimension, 공차 = tolerance, 견적 = quotation)
- 대상 도메인: 공학 도면 기반 제조/가공 비용 견적
- 성능: 전체 파이프라인 약 25-30초 (CPU), 서비스당 약 8-10초
- GPU 지원 계획 중이지만 아직 미설정
- 테스트 샘플 위치: `/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/`

---

## 🎯 OCR 성능 개선 전략

### 현재 문제점

**eDOCr v2 단독 사용 시 한계**:
- 치수 재현율: ~50% (목표: 90%+)
- GD&T 재현율: ~20% (목표: 75%+)
- 복잡한 영역의 치수 누락
- 맥락 정보 미활용

**원인 분석**:
1. 단일 OCR 엔진의 한계
2. 이미지 기반 검출의 한계 (복잡한 도면)
3. 치수-GD&T-윤곽선 관계 미활용
4. 누락 검증 메커니즘 부재

### 개선 전략: 멀티 모델 파이프라인

#### 전략 1: EDGNet을 전처리로 활용 ⭐⭐⭐

**EDGNet의 강점**:
- 그래프 신경망 기반 정확한 영역 분할
- 윤곽선/텍스트/치수 분리: 90.82% 정확도
- 맥락 정보 활용 (GraphSAGE)

**적용 방법**:
```
원본 도면
  ↓
EDGNet 벡터화 + 분할
  ├─ 윤곽선 영역
  ├─ 텍스트 영역
  └─ 치수 영역 (이것에 집중!)
  ↓
영역별 최적화된 OCR
  ├─ 치수 영역 → eDOCr v2 CRNN
  ├─ 텍스트 영역 → Tesseract + EasyOCR
  └─ GD&T → eDOCr v2 (치수 근처 집중 탐색)
  ↓
그래프 관계 활용
  └─ GD&T-치수 매칭
  └─ 치수-윤곽선 연결
```

**예상 효과**:
- 치수 재현율: 50% → **85%** (+35%p)
- GD&T 재현율: 20% → **70%** (+50%p)
- False Positive 감소

#### 전략 2: Skin Model로 누락 검증 및 보완 ⭐⭐

**Skin Model의 역할**:
- 형상 분석으로 예상 치수 위치 예측
- 누락 치수 탐지
- 인식된 치수의 타당성 검증

**적용 방법**:
```python
# 형상 분석으로 예상 치수 예측
expected_dims = skin_model.predict_expected_dimensions(contours)

# OCR 결과와 비교
missing = find_missing_dimensions(ocr_results, expected_dims)

# 누락 위치에 대해 OCR 재시도
for miss in missing:
    enhanced_region = super_resolution(crop(image, miss.location))
    recovered = ocr_engine.recognize(enhanced_region)
```

**예상 효과**:
- 중요 치수 누락 방지 (직경, 주요 길이)
- OCR 신뢰도 향상
- 사용자에게 누락 가능성 알림

#### 전략 3: Gateway 멀티 스테이지 파이프라인 ⭐⭐⭐

**Gateway 고도화**:
```python
# 4단계 파이프라인
async def advanced_ocr_pipeline(image):
    # Stage 1: EDGNet 세그멘테이션
    segmentation = await edgnet.segment(image)

    # Stage 2: v1/v2 앙상블 OCR
    ocr_v1 = await edocr_v1.ocr(image, regions=segmentation['dimensions'])
    ocr_v2 = await edocr_v2.ocr(image, regions=segmentation['dimensions'])
    dimensions = ensemble(ocr_v1, ocr_v2, weights={'v1': 0.6, 'v2': 0.4})

    # Stage 3: Skin Model 검증
    validation = await skinmodel.validate(segmentation['contours'], dimensions)

    # Stage 4: 누락 처리
    if validation['missing']:
        recovered = await retry_missing_regions(image, validation['missing'])
        dimensions.extend(recovered)

    return dimensions
```

**예상 효과**:
- 재현율: 50% → **90%**
- 정밀도 향상
- 신뢰도 증가

### 예상 성능 개선

| 항목 | 현재 (v2 단독) | 개선 후 (멀티 모델) | 향상 |
|------|---------------|-------------------|------|
| 치수 재현율 | ~50% | **90%** | +40%p |
| GD&T 재현율 | ~20% | **75%** | +55%p |
| 전체 F1 | 0.59 | **0.88** | +0.29 |

### 구현 우선순위

1. **Phase 1**: EDGNet 통합 (1-2주) - 가장 효과 큼
2. **Phase 2**: Gateway 멀티 스테이지 (2-3주)
3. **Phase 3**: Skin Model 검증 (2-3주)
4. **Phase 4**: 최적화 및 평가 (1-2주)

**총 소요 시간**: 6-10주

**목표 달성**:
- ✅ MaP 0.88 (사업 목표) → 달성 가능
- ✅ 메타데이터 추출 정확도 0.9 → 달성 가능

### 참고 자료

상세 분석: `/home/uproot/ax/poc/OCR_IMPROVEMENT_STRATEGY.md` 참조

---

**작성자**: Claude Code
**마지막 업데이트**: 2025-10-31
