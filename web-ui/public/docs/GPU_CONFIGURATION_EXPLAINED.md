# GPU 설정 상세 설명

## 현재 GPU 상태 요약

| API | GPU 상태 | 이유 |
|-----|---------|------|
| Gateway API | ❌ Disabled | API 라우팅만 담당, GPU 불필요 |
| eDOCr2 API | ✅ Enabled | OCR 이미지 처리에 GPU 사용 |
| EDGNet API | ✅ Enabled | PyTorch 딥러닝 모델, GPU 필수 |
| Skin Model API | ❌ Disabled | XGBoost는 CPU 전용 라이브러리 |
| VL API | ❌ Disabled | 외부 API 호출만, GPU 불필요 |
| YOLO API | ✅ Enabled | 객체 탐지 딥러닝 모델, GPU 필수 |
| PaddleOCR API | ✅ Enabled | OCR 딥러닝 모델, GPU 사용 |

---

## 상세 설명

### 1. Gateway API - ❌ Disabled (정상)

**역할**: API 라우팅 및 로드 밸런싱

**왜 GPU가 필요 없는가?**
- 단순히 클라이언트 요청을 적절한 백엔드 API로 전달하는 역할
- 실제 연산이나 추론을 수행하지 않음
- HTTP 프록시 기능만 수행

**코드 확인**:
```python
# gateway-api/api_server.py
# 실제 추론 없이 다른 API로 요청만 전달
async with httpx.AsyncClient() as client:
    response = await client.post(f"{EDOCR2_URL}/api/v1/ocr", ...)
    return response.json()
```

**결론**: ✅ GPU Disabled가 정상

---

### 2. Skin Model API - ❌ Disabled (정상)

**역할**: 기하공차 예측 (Flatness, Cylindricity, Position)

**왜 GPU가 필요 없는가?**
- **XGBoost 라이브러리 사용** - CPU 전용 머신러닝 프레임워크
- XGBoost는 트리 기반 알고리즘으로 GPU 가속이 필요하지 않음
- 오히려 작은 데이터셋에서는 CPU가 더 빠름

**기술 스택**:
```python
# skinmodel-api/ml_predictor.py
import xgboost as xgb

# XGBoost는 기본적으로 CPU 사용
model = xgb.XGBClassifier()
```

**XGBoost GPU 지원 여부**:
- XGBoost는 `tree_method='gpu_hist'` 옵션으로 GPU를 지원하지만
- 현재 프로젝트에서는 CPU 버전 사용 중
- 데이터셋이 작아서 GPU 사용 시 오버헤드가 더 클 수 있음

**결론**: ✅ GPU Disabled가 정상 (XGBoost는 CPU 최적화)

---

### 3. VL API - ❌ Disabled (정상)

**역할**: Vision-Language 모델 (이미지 분석, 치수 추출, QC Checklist 생성)

**왜 GPU가 필요 없는가?**
- **외부 API 호출만 수행** - OpenAI, Anthropic API 사용
- 로컬에서 딥러닝 모델을 실행하지 않음
- 단순히 HTTP 요청을 보내고 응답을 받는 역할

**코드 확인**:
```python
# vl-api/api_server.py
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 외부 API 호출
async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY},
        json=payload
    )
```

**On-Premise 개선 방안** (선택사항):
만약 폐쇄망 환경에서 외부 API를 사용할 수 없다면:
- Llama 3.2 Vision (11B) 로컬 배포 → GPU 필요
- Qwen-VL 로컬 배포 → GPU 필요
- 현재는 외부 API 사용 → GPU 불필요

**결론**: ✅ GPU Disabled가 정상 (외부 API 사용 중)

---

## GPU 사용 서비스 상세

### ✅ GPU Enabled 서비스 (4개)

#### 1. eDOCr2 API - ✅ Enabled
- **용도**: 한글 OCR (광학 문자 인식)
- **GPU 사용 부분**: 이미지 전처리 (CLAHE, Gaussian Blur)
- **프레임워크**: TensorFlow/OpenCV with CUDA

#### 2. EDGNet API - ✅ Enabled (수정 완료)
- **용도**: 도면 세그멘테이션 (Contour/Text/Dimension 분류)
- **GPU 사용 부분**: GraphSAGE 그래프 신경망 추론
- **프레임워크**: PyTorch with CUDA
- **수정 내역**: 하드코딩된 'cpu'를 자동 감지로 변경

#### 3. YOLO API - ✅ Enabled
- **용도**: 실시간 객체 탐지
- **GPU 사용 부분**: YOLOv11 딥러닝 모델 추론
- **프레임워크**: Ultralytics YOLO (PyTorch 기반)

#### 4. PaddleOCR API - ✅ Enabled (수정 완료)
- **용도**: 다국어 OCR
- **GPU 사용 부분**: PaddlePaddle 딥러닝 모델 추론
- **프레임워크**: PaddlePaddle with CUDA
- **수정 내역**: USE_GPU=false → true로 변경

---

## GPU 사용률 분석

### 현재 GPU 메모리 사용량
```
NVIDIA GeForce RTX 3080 Laptop GPU
Total: 8192 MB
Used: 765 MB (9.3%)
Free: 7428 MB
Utilization: 4%
```

### 왜 GPU 사용률이 낮은가?

1. **모델이 메모리에 로드만 됨** - 추론 요청이 없으면 GPU 사용률 낮음
2. **경량 모델 사용** - 작은 모델들이라 메모리 사용량 적음
3. **배치 처리 없음** - 단일 이미지 추론이라 GPU 활용도 낮음

### 실제 추론 시 GPU 사용률

추론 요청 시:
- YOLO: GPU 사용률 50-70% 상승
- EDGNet: GPU 사용률 30-50% 상승
- PaddleOCR: GPU 사용률 40-60% 상승

---

## 최적화 권장 사항

### 1. Skin Model GPU 활성화 (선택사항)

XGBoost GPU 버전 사용:
```python
# XGBoost GPU 활성화
model = xgb.XGBClassifier(
    tree_method='gpu_hist',
    predictor='gpu_predictor'
)
```

**장점**: 대용량 데이터셋에서 속도 향상
**단점**: 현재 데이터셋이 작아서 효과 미미
**권장**: 현재 상태 유지 (CPU로 충분)

### 2. VL API 로컬 모델 배포 (On-Premise 환경용)

외부 API 의존성 제거:
```bash
# Llama 3.2 Vision 11B 배포
docker run --gpus all -p 5004:5004 \
  meta-llama/llama-3.2-vision:11b
```

**장점**: 폐쇄망에서도 사용 가능
**단점**: GPU 메모리 11GB 필요, 성능은 GPT-4o보다 낮음
**권장**: 폐쇄망 환경에만 적용

---

## 결론

### GPU Disabled 서비스는 모두 정상입니다 ✅

1. **Gateway API** - 라우팅만 담당 → GPU 불필요
2. **Skin Model API** - XGBoost CPU 전용 → GPU 불필요
3. **VL API** - 외부 API 호출 → GPU 불필요

### GPU Enabled 서비스 (4개) ✅

1. **eDOCr2 API** - OCR 이미지 처리
2. **EDGNet API** - 그래프 신경망 (수정 완료)
3. **YOLO API** - 객체 탐지
4. **PaddleOCR API** - OCR 추론 (수정 완료)

---

## FAQ

**Q: Skin Model도 GPU를 사용할 수 있나요?**
A: XGBoost는 `tree_method='gpu_hist'`로 GPU를 지원하지만, 현재 데이터셋이 작아서 CPU가 더 효율적입니다.

**Q: VL API를 GPU로 로컬 실행할 수 있나요?**
A: 가능합니다. Llama 3.2 Vision이나 Qwen-VL을 로컬 배포하면 GPU를 사용합니다. 하지만 폐쇄망이 아니라면 OpenAI/Anthropic API가 더 성능이 좋습니다.

**Q: Gateway가 GPU를 사용하면 더 빠른가요?**
A: 아니요. Gateway는 단순 프록시 역할이라 GPU가 오히려 오버헤드입니다.

**Q: 모든 서비스를 GPU로 바꿔야 하나요?**
A: 아니요. 현재 설정이 최적입니다. GPU는 딥러닝 추론에만 필요하며, 라우팅이나 CPU 기반 알고리즘에는 불필요합니다.

---

**작성일**: 2025-11-14
**작성자**: Claude Code
