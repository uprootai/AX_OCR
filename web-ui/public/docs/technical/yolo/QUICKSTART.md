# YOLOv11 빠른 시작 가이드

**작성일**: 2025-10-31
**목적**: 5분 안에 YOLOv11 프로토타입 실행

---

## 🚀 빠른 시작 (Prototype)

### 1. 의존성 설치

```bash
cd /home/uproot/ax/poc
pip install ultralytics torch torchvision opencv-python pillow
```

### 2. 프로토타입 테스트 (사전 학습 모델)

사전 학습된 YOLOv11n 모델로 즉시 테스트 가능합니다.

```bash
# Python으로 직접 테스트
python3 -c "
from ultralytics import YOLO

# 모델 로드 (첫 실행 시 자동 다운로드)
model = YOLO('yolo11n.pt')

# 테스트 이미지로 추론
results = model.predict(
    source='https://ultralytics.com/images/bus.jpg',
    save=True,
    conf=0.25
)

print(f'✅ Detection complete! Found {len(results[0].boxes)} objects')
print(f'📁 Results saved to: runs/detect/predict/')
"
```

### 3. YOLO API 서버 실행 (단독)

```bash
# 1. API 서버 시작 (포트 5005)
cd yolo-api
python api_server.py &

# 2. Health Check
curl http://localhost:5005/api/v1/health

# 3. 테스트 이미지 다운로드
curl -o test_drawing.jpg https://ultralytics.com/images/bus.jpg

# 4. Detection API 호출
curl -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@test_drawing.jpg" \
  -F "conf_threshold=0.25" \
  -F "visualize=true"
```

### 4. Docker로 전체 시스템 실행

```bash
# 1. YOLO API 서비스만 빌드
docker-compose build yolo-api

# 2. YOLO API 서비스 시작
docker-compose up -d yolo-api

# 3. 로그 확인
docker logs -f yolo-api

# 4. Health Check
curl http://localhost:5005/api/v1/health

# 5. API 테스트
curl -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@test_drawing.jpg" \
  -F "conf_threshold=0.25"
```

---

## 📚 전체 워크플로우

### Phase 1: 프로토타입 (현재 단계)

```bash
# 사전 학습 모델로 즉시 테스트
python -c "from ultralytics import YOLO; YOLO('yolo11n.pt').predict('test.jpg', save=True)"
```

**예상 결과**:
- 일반 객체 검출 가능 (사람, 차, 등)
- 공학 도면 특화 학습 전: F1 40-50% (eDOCr 대비 5배)

---

### Phase 2: 데이터셋 준비 (Week 1)

```bash
# 1. eDOCr 결과를 YOLO 포맷으로 변환
python scripts/prepare_dataset.py

# 2. 데이터셋 확인
ls -R datasets/engineering_drawings/
```

**필요 작업**:
- eDOCr API로 최소 100장 처리
- 또는 수동 라벨링 (Roboflow/LabelImg)

---

### Phase 3: 모델 학습 (Week 2-3)

```bash
# Transfer Learning (권장)
python scripts/train_yolo.py \
  --model-size n \
  --epochs 100 \
  --batch 16 \
  --device 0

# 학습 모니터링
tensorboard --logdir runs/train
```

**예상 시간**:
- GPU (RTX 3060): 2-3시간 (100 epochs)
- CPU: 10-15시간

---

### Phase 4: 평가 및 추론 (Week 3)

```bash
# 1. 모델 평가
python scripts/evaluate_yolo.py \
  --model runs/train/engineering_drawings/weights/best.pt \
  --split test

# 2. 추론 실행
python scripts/inference_yolo.py \
  --model runs/train/engineering_drawings/weights/best.pt \
  --source test_images/ \
  --output runs/inference/test

# 3. 결과 확인
ls runs/inference/test/*_annotated.jpg
cat runs/inference/test/summary.json
```

---

### Phase 5: API 배포 (Week 4)

```bash
# 1. 학습된 모델 복사
cp runs/train/engineering_drawings/weights/best.pt yolo-api/models/

# 2. Docker 빌드 및 실행
docker-compose up -d yolo-api

# 3. API 테스트
curl -X POST "http://localhost:5005/api/v1/extract_dimensions" \
  -F "file=@drawing.pdf"
```

---

## 🔍 트러블슈팅

### Issue 1: CUDA not available

```bash
# GPU 확인
nvidia-smi

# PyTorch CUDA 지원 확인
python -c "import torch; print(torch.cuda.is_available())"

# CPU로 실행 (느리지만 작동)
python scripts/train_yolo.py --device cpu
```

### Issue 2: 메모리 부족

```bash
# 배치 크기 줄이기
python scripts/train_yolo.py --batch 4

# 이미지 크기 줄이기
python scripts/train_yolo.py --imgsz 640
```

### Issue 3: 모델 파일 없음

```bash
# API 서버는 모델 없어도 시작 가능 (기본 yolo11n.pt 사용)
# 학습 후 모델 복사
cp runs/train/engineering_drawings/weights/best.pt yolo-api/models/
docker-compose restart yolo-api
```

---

## 📊 예상 성능

| 단계 | 모델 | 데이터 | F1 Score | 시간 |
|------|------|--------|----------|------|
| **Prototype** | yolo11n.pt | 0장 | 40-50% | **즉시** |
| **Transfer Learning** | best.pt | 100장 | 70-80% | 2-3일 |
| **Full Training** | best.pt | 500장 | 85-90% | 1-2주 |
| **Production** | best.pt | 1000장+ | 90-96% | 1-2개월 |

---

## 🎯 다음 단계

1. **즉시 (오늘)**:
   ```bash
   # 프로토타입 테스트
   python -c "from ultralytics import YOLO; print(YOLO('yolo11n.pt'))"
   ```

2. **Week 1**:
   - eDOCr로 도면 100장 처리
   - `prepare_dataset.py` 실행
   - 데이터셋 확인

3. **Week 2-3**:
   - `train_yolo.py` 실행
   - 학습 모니터링
   - 평가 및 조정

4. **Week 4**:
   - API 배포
   - Gateway 통합
   - Web UI 연동

---

## 📞 지원

**문서**:
- 상세 가이드: `YOLOV11_IMPLEMENTATION_GUIDE.md`
- 제안서: `YOLOV11_PROPOSAL.md`
- 의사결정: `DECISION_MATRIX.md`

**로그 확인**:
```bash
# API 서버 로그
docker logs yolo-api

# 학습 로그
tail -f runs/train/engineering_drawings/results.txt
```

**API 문서**:
- Swagger: http://localhost:5005/docs
- ReDoc: http://localhost:5005/redoc

---

**작성자**: Claude 3.7 Sonnet
**최종 업데이트**: 2025-10-31

**핵심 메시지**:
> 5분 만에 프로토타입 테스트 가능!
> 사전 학습 모델로 즉시 시작하세요. 🚀
