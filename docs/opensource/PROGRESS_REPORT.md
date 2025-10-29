# eDOCr v1 통합 진행 상황 보고서

**날짜**: 2025-10-29
**작업**: 현재 POC에 실제 OCR 기능 통합

---

## 🎯 목표

Mock 데이터만 반환하는 현재 API 서버를 실제 OCR이 작동하는 시스템으로 교체

---

## ✅ 완료된 작업

### 1. 문제 분석 및 진단 ✅
- **발견**: 현재 API 서버는 Mock 데이터만 반환
- **원인**: 실제 OCR 코드가 주석 처리됨
- **증거**: `api_server.py:122-149` - `process_ocr()` 함수
- **영향**: 어떤 도면을 업로드해도 동일한 결과 반환

### 2. 저장소 분석 및 분류 ✅
15개 GitHub 저장소를 클론하고 분류:
```
/home/uproot/ax/poc/opensource/
├── 01-immediate/      # ✅ 즉시 통합 가능 (3개)
├── 02-short-term/     # ⚠️ 단기 통합 고려 (2개)
├── 03-research/       # 🔬 연구 및 장기 (3개)
├── 04-not-available/  # ❌ 통합 불가능 (2개)
└── 05-out-of-scope/   # 🏗️ 범위 외 (5개)
```

### 3. 문서 작성 ✅
- `README.md` - 15개 저장소 전체 분석
- `COMPARISON_REPORT.md` - edocr2 비교 분석
- `SOLUTION.md` - 해결 방안 가이드
- `PROGRESS_REPORT.md` - 본 문서

### 4. eDOCr v1 통합 코드 작성 ✅

#### 파일 생성:
- ✅ `api_server_edocr_v1.py` - 실제 OCR 구현 API 서버
- ✅ `Dockerfile.v1` - eDOCr v1 Docker 이미지
- ✅ `requirements_v1.txt` - 전체 종속성
- ✅ `docker-compose.v1.yml` - Docker Compose 설정

#### 주요 기능:
- ✅ eDOCr v1 자동 설치 (git clone)
- ✅ 모델 자동 다운로드 (GitHub Releases)
- ✅ 실제 OCR 파이프라인 구현
- ✅ Box detection, infoblock, GD&T, dimensions 추출
- ✅ 시각화 이미지 생성
- ✅ API 엔드포인트: `/api/v1/health`, `/api/v1/ocr`

### 5. 백업 생성 ✅
- ✅ `api_server_mock.py.backup` - 기존 API 서버 백업

---

## 🔄 진행 중

### 6. Docker 이미지 빌드 ⏳
```bash
docker build -f Dockerfile.v1 -t edocr-api:v1 .
```

**빌드 단계**:
1. ✅ Base 이미지 (Python 3.9-slim)
2. ✅ 시스템 종속성 설치 (tesseract-ocr, poppler-utils 등)
3. ⏳ eDOCr v1 git clone 중
4. ⏳ Python 패키지 설치 중 (TensorFlow, OpenCV 등)
5. ⏳ API 서버 복사

**예상 소요 시간**: 10-15분 (TensorFlow 설치 포함)

---

## 📝 대기 중 작업

### 7. Docker 컨테이너 배포 (다음 단계)
```bash
# 기존 컨테이너 중지
docker-compose down

# v1으로 시작
docker-compose -f docker-compose.v1.yml up -d

# 로그 확인
docker-compose -f docker-compose.v1.yml logs -f
```

**예상 로그**:
```
Loading eDOCr v1 models...
Downloading recognizer_infoblock.h5...
Downloading recognizer_dimensions.h5...
Downloading recognizer_gdts.h5...
✅ eDOCr v1 models loaded successfully!
```

### 8. Health Check 테스트
```bash
curl http://localhost:5001/api/v1/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "service": "eDOCr v1 API",
  "version": "1.0.0",
  "edocr_available": true,
  "models_loaded": true
}
```

### 9. OCR 기능 테스트
```bash
curl -X POST "http://localhost:5001/api/v1/ocr" \
  -F "file=@/home/uproot/ax/poc/opensource/01-immediate/eDOCr/tests/test_samples/Candle_holder.jpg" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true" \
  -F "visualize=true"
```

**예상 결과**:
```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {"value": 50.5, "tolerance": "+0.1/-0.05", ...},
      {"value": 12.0, "tolerance": "±0.05", ...}
    ],
    "gdt": [
      {"symbol": "⏤", "value": 0.02, ...}
    ],
    "text": {
      "drawing_number": "실제 값",
      "title": "실제 값",
      ...
    }
  },
  "processing_time": 5.8
}
```

### 10. 웹 UI 테스트
1. 브라우저에서 `http://localhost:5173/test/edocr2` 접속
2. 도면 파일 업로드
3. OCR 옵션 선택
4. 실행 버튼 클릭
5. **실제 OCR 결과** 확인 (Mock 데이터 아님!)

---

## 📊 예상 vs 실제 결과 비교

### 현재 (Mock)
```json
{
  "dimensions": [],  // ❌ 항상 비어있음
  "gdt": [],         // ❌ 항상 비어있음
  "text": {
    "drawing_number": "MOCK-001",  // ❌ 고정값
    "title": "Test Drawing"         // ❌ 고정값
  }
}
```

### eDOCr v1 적용 후 (실제)
```json
{
  "dimensions": [
    {"value": "50.5", "tolerance": "+0.1/-0.05"},
    {"value": "Ø12", "tolerance": "±0.05"}
  ],
  "gdt": [
    {"symbol": "⏤", "value": "0.02"}
  ],
  "text": {
    "drawing_number": "DRW-2024-001",
    "title": "Candle Holder Base",
    "material": "Aluminum 6061"
  }
}
```

---

## 🔧 기술 상세

### eDOCr v1 파이프라인

#### 1. 이미지 로드
```python
# PDF 또는 이미지 처리
if file_path.suffix.lower() == '.pdf':
    images = convert_from_path(str(file_path))
    img = np.array(images[0])
else:
    img = cv2.imread(str(file_path))
```

#### 2. Box Detection
```python
class_list, img_boxes = tools.box_tree.findrect(img)
```
- 도면에서 사각형 영역 탐지
- 프레임, 테이블, 치수 박스 분류

#### 3. Rectangle Processing
```python
boxes_infoblock, gdt_boxes, cl_frame, process_img = \
    tools.img_process.process_rect(class_list, img)
```
- 인포블록, GDT 박스, 프레임 분리
- 전처리된 이미지 생성

#### 4. OCR Infoblock
```python
infoblock_dict = tools.pipeline_infoblock.read_infoblocks(
    boxes_infoblock, img, alphabet_infoblock, model_infoblock
)
```
- 제목 블록에서 텍스트 추출
- 도면 번호, 개정, 제목, 재료 등

#### 5. OCR GD&T
```python
gdt_dict = tools.pipeline_gdts.read_gdtbox1(
    gdt_boxes, alphabet_gdts, model_gdts,
    alphabet_dimensions, model_dimensions
)
```
- 기하 공차 기호 인식
- GD&T 값 추출

#### 6. OCR Dimensions
```python
dimension_dict = tools.pipeline_dimensions.read_dimensions(
    str(process_img_path), alphabet_dimensions,
    model_dimensions, cluster_threshold
)
```
- 치수 텍스트 인식
- 공차 값 파싱
- 클러스터링으로 관련 치수 그룹화

#### 7. Visualization
```python
mask_img = tools.output.mask_the_drawing(
    img, infoblock_dict, gdt_dict, dimension_dict,
    cl_frame, color_palette
)
```
- 원본 이미지 위에 결과 오버레이
- 색상으로 요소 구분

---

## 🚀 배포 후 확인 사항

### 체크리스트

#### API 서버
- [ ] Health check 응답 정상
- [ ] `edocr_available: true`
- [ ] `models_loaded: true`
- [ ] 로그에 에러 없음

#### OCR 기능
- [ ] 다양한 도면으로 테스트
- [ ] dimensions 배열에 실제 값
- [ ] gdt 배열에 실제 값
- [ ] text 객체에 실제 값
- [ ] Mock 데이터가 아님 확인

#### 성능
- [ ] 처리 시간 5-10초 (Mock: 2초 고정)
- [ ] 메모리 사용량 모니터링
- [ ] CPU 사용량 확인

#### 시각화
- [ ] visualization_url 반환
- [ ] 이미지 다운로드 가능
- [ ] 원본 위에 결과 오버레이 확인

---

## 📈 성능 예상

| 항목 | Mock (현재) | eDOCr v1 (예상) |
|------|-------------|-----------------|
| 처리 시간 | 2초 고정 | 5-10초 |
| 메모리 | ~200MB | ~1-2GB |
| CPU | 최소 | 중간-높음 |
| 정확도 | N/A | 80-90% |
| dimensions | 0개 | 실제 추출 |
| GD&T | 0개 | 실제 추출 |
| text | Mock | 실제 추출 |

---

## 🐛 알려진 이슈 및 해결

### Issue 1: libgl1-mesa-glx 패키지 없음
- **문제**: Dockerfile 빌드 실패
- **원인**: Debian trixie에서 패키지 이름 변경
- **해결**: `libgl1-mesa-glx` → `libgl1`

### Issue 2: Python venv 설치 불가
- **문제**: `python3-venv` 패키지 필요 (sudo 권한)
- **원인**: WSL 환경 제약
- **해결**: Docker 사용으로 우회

### Issue 3: Conda 미설치
- **문제**: `conda` 명령어 없음
- **원인**: Anaconda/Miniconda 미설치
- **해결**: Docker 사용으로 우회

---

## 📚 참고 자료

### 문서
- `/home/uproot/ax/poc/opensource/README.md` - 전체 분석
- `/home/uproot/ax/poc/opensource/COMPARISON_REPORT.md` - 비교 분석
- `/home/uproot/ax/poc/opensource/SOLUTION.md` - 해결 가이드

### 코드
- `/home/uproot/ax/poc/edocr2-api/api_server_edocr_v1.py` - API 서버
- `/home/uproot/ax/poc/edocr2-api/Dockerfile.v1` - Docker 이미지
- `/home/uproot/ax/poc/edocr2-api/api_server_mock.py.backup` - 백업

### 테스트 이미지
- `/home/uproot/ax/poc/opensource/01-immediate/eDOCr/tests/test_samples/`

### 외부 링크
- eDOCr GitHub: https://github.com/javvi51/eDOCr
- eDOCr 논문: https://www.frontiersin.org/articles/10.3389/fmtec.2023.1154132/full
- 모델 Releases: https://github.com/javvi51/eDOCr/releases/tag/v1.0.0

---

## ⏭️ 다음 단계

### 즉시 (Docker 빌드 완료 후)
1. Docker 이미지 빌드 완료 확인
2. 컨테이너 시작
3. Health check
4. OCR 테스트

### 단기 (이번 주)
1. 다양한 도면으로 테스트
2. 성능 벤치마크
3. 에러 처리 개선
4. 로깅 강화

### 중기 (1-2주)
1. edocr2 v2 환경 설정
2. v1 vs v2 성능 비교
3. 프로덕션 배포 계획

### 장기 (1개월)
1. Image2CAD 통합 (DXF 출력)
2. Deep-Vectorization 파일럿
3. 3D 확장 연구

---

## 📞 지원

문제가 발생하면:
1. 로그 확인: `docker-compose -f docker-compose.v1.yml logs -f`
2. 컨테이너 상태: `docker ps -a`
3. 이미지 확인: `docker images | grep edocr`
4. 백업으로 롤백: `cp api_server_mock.py.backup api_server.py`

---

**상태**: 🟡 진행 중 (Docker 빌드 중)
**완료 예상**: 10-15분 후
**다음 업데이트**: 배포 및 테스트 결과
